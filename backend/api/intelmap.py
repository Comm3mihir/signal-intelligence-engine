import logging
import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import case, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.intelmap.analysis import fingerprint, unique_article_key
from backend.intelmap.contracts import AnalystReview, StrictModel
from backend.intelmap.gateway import CapacityUnavailable, providers
from backend.intelmap.jobs import add_once, archive_articles, process_one, queue_generation
from backend.intelmap.metrics import aware, bayesian_update, evaluate
from backend.intelmap.models import Article, Evidence, Forecast, Inference, IntelMap, Job, ProviderDay, Resolution, Revision, now
from backend.models.database import get_db
from backend.research.world_intelligence import read_record, refresh


router = APIRouter(prefix="/api/intelmap", tags=["IntelMap"])


class Generate(BaseModel):
    article_ids: list[str] = Field(min_length=1, max_length=8)


def forecast_view(db, forecast):
    original = forecast.original
    evidence = db.query(Evidence).filter_by(forecast_id=forecast.id).order_by(Evidence.created_at.desc()).all()
    revisions = db.query(Revision).filter_by(forecast_id=forecast.id).order_by(Revision.created_at.desc()).all()
    resolution = db.get(Resolution, forecast.id)
    if resolution:
        status = resolution.status
    elif aware(forecast.deadline) <= now():
        status = "expired_inconclusive"
    else:
        status = "active"
        for item in evidence:
            if aware(item.created_at) < aware(forecast.issued_at) or item.reasoning == "Cited by the original model assessment.":
                continue
            status = {"supports": "supporting_evidence", "contradicts": "contradictory_evidence",
                      "partial": "partially_materialized"}.get(item.stance, "monitoring")
            break
    probability = revisions[0].probability if revisions else original["probability"]
    parent = db.get(Forecast, forecast.parent_id) if forecast.parent_id else None
    joint_probability = None
    if parent:
        parent_revision = db.query(Revision).filter_by(forecast_id=parent.id).order_by(Revision.created_at.desc()).first()
        joint_probability = (parent_revision.probability if parent_revision else parent.original["probability"]) * probability
    return {
        "id": forecast.id, "map_id": forecast.map_id, "parent_id": forecast.parent_id, "original": original,
        "probability": probability, "joint_probability": joint_probability, "issued_at": aware(forecast.issued_at),
        "deadline": aware(forecast.deadline), "status": status, "truth_value": resolution.truth_value if resolution else None,
        "evidence": [{"id": row.id, "article": db.get(Article, row.article_id).data,
                      "stance": row.stance, "reasoning": row.reasoning, "at": aware(row.created_at)} for row in evidence],
        "revisions": [{"id": row.id, "probability": row.probability, "rationale": row.rationale, "at": aware(row.created_at),
                       "evidence_id": row.evidence_id, **row.provenance} for row in revisions],
        "resolution": {"status": resolution.status, "reasoning": resolution.reasoning,
                       "credibility": resolution.credibility, "at": aware(resolution.created_at),
                       "article": db.get(Article, resolution.article_id).data if resolution.article_id else None} if resolution else None,
    }


@router.get("/catalog")
def catalog(db: Session = Depends(get_db)):
    snapshot = read_record(db, "snapshot", {})
    return {"events": [{"id": item["id"], "articles": item["articles"]} for item in snapshot.get("events", [])[:150]],
            "history": [article.data for article in db.query(Article).order_by(Article.published_at.desc()).limit(200)],
            "maps": [{"id": item.id, "title": item.event["title"], "created_at": aware(item.created_at)}
                     for item in db.query(IntelMap).order_by(IntelMap.created_at.desc()).limit(100)],
            "jobs": [{"id": job.id, "map_id": job.payload["map_id"], "state": job.state,
                      "stage": job.payload["stage"], "error": job.error, "ready_at": aware(job.ready_at),
                      "title": job.payload["source"][0]["title"]}
                     for job in db.query(Job).filter(Job.kind == "generate", Job.state != "complete")
                     .order_by(Job.created_at.desc()).limit(30)]}


@router.post("/generate", status_code=202)
def generate(req: Generate, db: Session = Depends(get_db)):
    ids = set(req.article_ids)
    if len(ids) != len(req.article_ids) or any(len(article_id) > 32 for article_id in ids):
        raise HTTPException(422, "Select up to eight distinct articles.")
    articles = db.query(Article).filter(Article.id.in_(ids)).all()
    if len(articles) != len(ids):
        archive_articles(db, read_record(db, "snapshot", {}))
        articles = db.query(Article).filter(Article.id.in_(ids)).all()
    if len(articles) != len(ids):
        raise HTTPException(404, "An article is unavailable in SIGNAL.")
    try:
        job = queue_generation(db, articles)
    except CapacityUnavailable as exc:
        raise HTTPException(429, str(exc)) from exc
    return {"job_id": job.id, "map_id": job.payload["map_id"], "state": job.state}


@router.get("/maps/{map_id}")
def map_details(map_id: str, db: Session = Depends(get_db)):
    item = db.get(IntelMap, map_id)
    if not item:
        raise HTTPException(404, "The map is not published yet.")
    forecasts = db.query(Forecast).filter_by(map_id=map_id).order_by(Forecast.parent_id.is_not(None), Forecast.id).all()
    return {"id": item.id, "event": item.event, "created_at": aware(item.created_at),
            "articles": [db.get(Article, item_id).data for item_id in item.article_ids],
            "forecasts": [forecast_view(db, forecast) for forecast in forecasts]}


@router.get("/track")
def track(db: Session = Depends(get_db)):
    forecasts = (db.query(Forecast).outerjoin(Resolution, Resolution.forecast_id == Forecast.id)
                 .order_by(case((Resolution.forecast_id.is_(None) & (Forecast.deadline > now()), 0), else_=1),
                           Forecast.deadline.desc()).limit(150).all())
    return [forecast_view(db, row) for row in forecasts]


class AnalystSource(StrictModel):
    title: str = Field(min_length=5, max_length=350)
    publisher: str = Field(min_length=2, max_length=120)
    url: HttpUrl
    published_at: datetime
    excerpt: str = Field(min_length=10, max_length=650)


@router.post("/sources", status_code=201)
def save_source(req: AnalystSource, db: Session = Depends(get_db)):
    if req.published_at.tzinfo is None or req.published_at > now():
        raise HTTPException(422, "Use a source publication date and time in UTC or with an explicit offset.")
    article_id = fingerprint("analyst_source", str(req.url))[:32]
    data = {"id": article_id, **req.model_dump(mode="json"), "regions": [], "topics": [],
            "provenance": "analyst_submitted"}
    if not db.get(Article, article_id):
        add_once(db, Article(id=article_id, published_at=req.published_at,
                             fingerprint=unique_article_key(data), data=data))
        db.commit()
    return db.get(Article, article_id).data


class BayesianRevisionRequest(StrictModel):
    evidence_id: str = Field(min_length=1, max_length=32)
    likelihood_ratio: float = Field(gt=0, le=1_000_000, allow_inf_nan=False)
    rationale: str = Field(min_length=20, max_length=1500)


@router.post("/forecasts/{forecast_id}/bayesian-revision", status_code=201)
def bayesian_revision(forecast_id: str, req: BayesianRevisionRequest, db: Session = Depends(get_db)):
    forecast = db.query(Forecast).filter_by(id=forecast_id).with_for_update().first()
    evidence = db.get(Evidence, req.evidence_id)
    if not forecast or not evidence or evidence.forecast_id != forecast_id:
        raise HTTPException(404, "Select evidence associated with this forecast.")
    if forecast.original["exclusive_group"] or db.get(Resolution, forecast_id) or aware(forecast.deadline) <= now():
        raise HTTPException(409, "This forecast cannot be individually revised.")
    if db.query(Revision).filter_by(evidence_id=evidence.id).first():
        raise HTTPException(409, "This evidence already triggered a revision.")
    latest = db.query(Revision).filter_by(forecast_id=forecast_id).order_by(Revision.created_at.desc()).first()
    prior = latest.probability if latest else forecast.original["probability"]
    probability = bayesian_update(prior, req.likelihood_ratio)
    db.add(Revision(forecast_id=forecast_id, evidence_id=evidence.id, probability=probability,
                    rationale=req.rationale, provenance={"provider": "analyst", "model": "bayes_odds",
                    "likelihood_ratio": req.likelihood_ratio, "prior": prior, "estimate": "analyst_supplied_ratio"}))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "This evidence already triggered a revision.") from exc
    return {"probability": probability}


@router.post("/forecasts/{forecast_id}/resolve", status_code=201)
def resolve(forecast_id: str, req: AnalystReview, db: Session = Depends(get_db)):
    forecast = db.query(Forecast).filter_by(id=forecast_id).with_for_update().first()
    if not forecast:
        raise HTTPException(404, "Forecast unavailable.")
    if db.get(Resolution, forecast_id):
        raise HTTPException(409, "A resolution is already recorded.")
    article = db.get(Article, req.article_id) if req.article_id else None
    if req.article_id and article is None:
        raise HTTPException(422, "The evidence article is not in the archive.")
    if req.status != "expired_inconclusive":
        if not req.criteria_verified:
            raise HTTPException(422, "Verify the original criteria and timeframe before recording a binary outcome.")
        if not article or not aware(forecast.issued_at) <= aware(article.published_at) <= now():
            raise HTTPException(422, "A confirmed or refuted outcome needs a post-issuance archived source.")
    elif aware(forecast.deadline) > now():
        raise HTTPException(422, "An inconclusive resolution can be recorded once the deadline passes.")
    value = {"confirmed": 1, "refuted": 0}.get(req.status)
    db.add(Resolution(forecast_id=forecast.id, truth_value=value, **req.model_dump(exclude={"criteria_verified"})))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "A resolution is already recorded.") from exc
    return {"truth_value": value}


@router.get("/evaluate")
def metrics(db: Session = Depends(get_db)):
    return evaluate(db)


@router.get("/infrastructure")
def infrastructure(db: Session = Depends(get_db)):
    configured = {provider.name: provider for provider in providers("event")}
    reasoning = {provider.name: provider.model for provider in providers("prediction")}
    day = now().date()
    cutoff = now() - timedelta(hours=24)
    rows = db.query(Inference).filter(Inference.created_at >= cutoff).order_by(Inference.created_at.desc()).all()
    totals = []
    for name in ("groq", "gemini", "openrouter"):
        provider = configured.get(name)
        attempts = [row for row in rows if row.provider == name]
        actual = [row for row in attempts if row.status != "cached"]
        budget = db.get(ProviderDay, f"{name}:{day}")
        reserved = budget.reserved if budget else 0
        totals.append({"name": name, "configured": bool(provider), "model": provider.model if provider else None,
                       "reasoning_model": reasoning.get(name), "last_result": actual[0].status if actual else None,
                       "last_latency_ms": actual[0].milliseconds if actual else None, "requests": len(actual),
                       "failures": sum(row.status != "success" for row in actual),
                       "cache_hits": len(attempts) - len(actual),
                       "fallback_attempts": sum(row.fallback_rank > 0 for row in actual),
                       "input_tokens": sum(row.input_tokens or 0 for row in actual) if any(row.input_tokens is not None for row in actual) else None,
                       "output_tokens": sum(row.output_tokens or 0 for row in actual) if any(row.output_tokens is not None for row in actual) else None,
                       "local_budget_remaining": max(0, provider.daily_budget - reserved) if provider else None,
                       "provider_quota": None, "estimated_expenditure": None})
    return {"providers": totals, "pending_jobs": db.query(Job).filter(Job.state.in_(("queued", "running"))).count(),
            "failed_jobs": db.query(Job).filter_by(state="failed").count()}


@router.post("/workflows/tick")
def tick(request: Request, db: Session = Depends(get_db)):
    secret = os.getenv("SIGNAL_SCHEDULER_SECRET", "")
    if not secret or not secrets.compare_digest(request.headers.get("authorization", "").encode(), f"Bearer {secret}".encode()):
        raise HTTPException(401, "Scheduler authorization required.")
    snapshot = read_record(db, "snapshot", {})
    refreshed = False
    if (not snapshot or aware(datetime.fromisoformat(snapshot["refreshed_at"])) < now() - timedelta(minutes=15)):
        # In PostgreSQL, take a session-scoped lock on a dedicated connection across refresh commits.
        if db.bind.dialect.name == "postgresql":
            with db.bind.connect() as connection:
                if connection.scalar(text("SELECT pg_try_advisory_lock(58223720)")):
                    try:
                        snapshot = refresh(db)
                        archive_articles(db, snapshot)
                        refreshed = True
                    finally:
                        connection.execute(text("SELECT pg_advisory_unlock(58223720)"))
        else:
            snapshot = refresh(db)
            archive_articles(db, snapshot)
            refreshed = True
    try:
        processed = process_one(db)
    except Exception:
        logging.getLogger(__name__).exception("IntelMap workflow stage failed")
        raise HTTPException(503, "Workflow will retry.")
    return {"snapshot_at": snapshot.get("refreshed_at"), "refreshed": refreshed, "processed": processed}
