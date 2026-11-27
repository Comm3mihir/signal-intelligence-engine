from datetime import timedelta

from sqlalchemy import and_, or_, update
from sqlalchemy.exc import IntegrityError

from backend.intelmap.analysis import candidate_forecasts, context, fingerprint, generation_step, historical_candidates, unique_article_key, verify_article
from backend.intelmap.embeddings import enabled, store_embedding
from backend.intelmap.gateway import CapacityUnavailable
from backend.intelmap.models import Article, Evidence, Forecast, Job, now, uid
from backend.research.world_intelligence import article_date


def add_once(db, instance) -> bool:
    try:
        with db.begin_nested():
            db.add(instance)
            db.flush()
        return True
    except IntegrityError:
        return False


def archive_articles(db, snapshot: dict):
    articles = {a["id"]: a for event in snapshot.get("events", []) for a in event["articles"]}
    if not articles:
        return
    known = set(db.scalars(db.query(Article.id).filter(Article.id.in_(articles)).statement))
    for article_id in articles.keys() - known:
        data = articles[article_id]
        article = Article(id=article_id, published_at=article_date(data["published_at"]),
                          fingerprint=unique_article_key(data), data=data)
        if add_once(db, article):
            queue_matches(db, article)
            if enabled() and (data["regions"] or data["topics"]):
                add_once(db, Job(id=fingerprint("embed_article", article.id), kind="embed_article", priority=35,
                                 payload={"article_id": article.id}))
    db.commit()


def queue_matches(db, article):
    for fid in candidate_forecasts(db, article):
        job_id = fingerprint("verify", fid, article.fingerprint)
        if not db.get(Job, job_id):
            add_once(db, Job(id=job_id, kind="verify", priority=20,
                             payload={"article_id": article.id, "forecast_id": fid}))


def queue_generation(db, articles: list[Article], previous_map_id: str | None = None) -> Job:
    source = sorted((context(article) for article in articles), key=lambda a: a["id"])
    ids = [article["id"] for article in source]
    map_id = (fingerprint("intelmap:regenerate", previous_map_id, ids)
              if previous_map_id else fingerprint("intelmap:v1", ids))[:32]
    key = fingerprint("generate", map_id)
    job = db.get(Job, key)
    if job:
        return job
    pending = db.query(Job).filter(Job.kind == "generate", Job.state.in_(("queued", "running"))).count()
    if pending >= 20:
        raise CapacityUnavailable("Generation queue is full. Please wait for an existing map to complete.")
    related = []
    if previous_map_id:
        evidence = (db.query(Article).join(Evidence, Evidence.article_id == Article.id)
                    .join(Forecast, Forecast.id == Evidence.forecast_id)
                    .filter(Forecast.map_id == previous_map_id, Article.id.notin_(ids))
                    .order_by(Article.published_at.desc()).limit(12).all())
        related = [context(article) for article in evidence[:6]]
    add_once(db, Job(id=key, kind="generate", priority=10, payload={
        "stage": "event", "map_id": map_id, "source": source, "previous_map_id": previous_map_id,
        "precedents": historical_candidates(db, source), "followup": related,
    }))
    db.commit()
    return db.get(Job, key)


def claim(db):
    instant = now()
    ready = and_(Job.state.in_(("queued", "running")), Job.ready_at <= instant)
    query = db.query(Job).filter(ready).order_by(Job.priority, Job.ready_at, Job.created_at)
    if db.bind.dialect.name == "postgresql":
        # A transaction-level advisory lock serializes claims across scheduled invocations.
        from sqlalchemy import text
        if not db.scalar(text("SELECT pg_try_advisory_xact_lock(58223719)")):
            db.rollback()
            return None
    if db.query(Job).filter(Job.state == "running", Job.ready_at > instant).first():
        db.rollback()
        return None
    candidate = query.first()
    if not candidate:
        db.rollback()
        return None
    lease = uid()
    item_id = candidate.id
    changed = db.execute(update(Job).where(Job.id == item_id, ready).execution_options(synchronize_session=False).values(
        lease=lease, state="running", ready_at=instant + timedelta(minutes=4), attempts=Job.attempts + 1,
    )).rowcount
    db.commit()
    return (item_id, lease) if changed == 1 else None


def process_one(db):
    claimed = claim(db)
    if not claimed:
        return False
    job_id, lease = claimed
    item = db.get(Job, job_id)
    try:
        next_payload = None
        if item.kind == "generate":
            next_payload = generation_step(db, item.payload)
            if not next_payload and enabled():
                for forecast in db.query(Forecast).filter_by(map_id=item.payload["map_id"]):
                    add_once(db, Job(id=fingerprint("embed_forecast", forecast.id), kind="embed_forecast",
                                     priority=15, payload={"forecast_id": forecast.id}))
        elif item.kind == "verify":
            verify_article(db, item.payload)
        elif item.kind == "embed_article":
            article = db.get(Article, item.payload["article_id"])
            store_embedding(db, f"article:{article.id}", f'{article.data["title"]} {article.data["excerpt"]}')
            queue_matches(db, article)
        elif item.kind == "embed_forecast":
            forecast = db.get(Forecast, item.payload["forecast_id"])
            store_embedding(db, f"forecast:{forecast.id}", f'{forecast.original["title"]} {forecast.original["confirm_if"]}')
        else:
            raise ValueError("Unknown IntelMap job kind")
        state = "queued" if next_payload else "complete"
        changes = {"state": state, "ready_at": now(), "lease": None, "attempts": 0, "error": None}
        if next_payload:
            changes["payload"] = next_payload
        if db.execute(update(Job).where(Job.id == job_id, Job.lease == lease).values(**changes)).rowcount != 1:
            db.rollback()
            return False
        db.commit()
    except CapacityUnavailable as exc:
        db.rollback()
        item = db.get(Job, job_id)
        delay = min(3600, 30 * 2 ** min(item.attempts, 7))
        db.execute(update(Job).where(Job.id == job_id, Job.lease == lease).values(
            state="queued", ready_at=now() + timedelta(seconds=delay), lease=None, error=str(exc),
        ))
        db.commit()
    except Exception:
        db.rollback()
        item = db.get(Job, job_id)
        db.execute(update(Job).where(Job.id == job_id, Job.lease == lease).values(
            state="failed" if item.attempts >= 5 else "queued",
            ready_at=now() + timedelta(seconds=30 * 2 ** min(item.attempts, 7)),
            lease=None, error="Analysis could not be completed. See backend logs.",
        ))
        db.commit()
        raise
    return True
