"""Evidence-bounded generation, candidate selection and verification."""

import hashlib
import json
import os
import re
from datetime import timedelta
from urllib.parse import urlsplit

from sqlalchemy import func, select

from backend.intelmap.contracts import Draft, EventAssessment, Verification
from backend.intelmap.embeddings import cosine
from backend.intelmap.gateway import infer
from backend.intelmap.models import Article, Embedding, Evidence, Forecast, ForecastTerm, IntelMap, Resolution, Revision, now, uid
from backend.research.world_intelligence import article_date, headline_terms


def fingerprint(*values) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def unique_article_key(data: dict) -> str:
    # Treat identical normalized headlines across publishers as one possible syndicated report.
    return fingerprint(re.sub(r"\W+", " ", data["title"].casefold()).strip())


def terms(value: str) -> set[str]:
    return headline_terms(value) - {"new", "say", "says", "latest", "report", "official", "will", "could"}


def context(article: Article) -> dict:
    data = article.data
    return {**{key: data[key] for key in ("id", "title", "publisher", "published_at", "regions", "topics")},
            "excerpt": (data.get("content") or data["excerpt"])[:3800],
            "provenance": data.get("provenance", "publisher_feed"),
            "date_is_retrieval_time": data.get("date_is_retrieval_time", False)}


def historical_candidates(db, source: list[dict]) -> list[dict]:
    words = terms(" ".join(item["title"] for item in source))
    regions = {name for item in source for name in item["regions"]}
    source_ids = {item["id"] for item in source}
    source_titles = {unique_article_key(item) for item in source}
    rows = (db.query(Article).filter(Article.published_at < min(article_date(r["published_at"]) for r in source))
            .order_by(Article.published_at.desc()).limit(500).all())
    source_vector = db.get(Embedding, f'article:{source[0]["id"]}')
    vectors = {row.id: row for row in db.query(Embedding).filter(
        Embedding.id.in_([f"article:{article.id}" for article in rows]))} if source_vector else {}
    scored = []
    for article in rows:
        common = words & terms(article.data["title"])
        geo = regions.intersection(article.data["regions"])
        semantic = cosine(source_vector, vectors.get(f"article:{article.id}")) or 0
        if article.id not in source_ids and article.fingerprint not in source_titles and (
            len(common) >= 2 or (geo and common) or semantic >= 0.70
        ):
            age_days = max(0, (article_date(source[0]["published_at"]) - article_date(article.data["published_at"])).days)
            scored.append((len(common) + len(geo) + 2 * semantic + 1 / (1 + age_days / 30), context(article)))
    return [item for _, item in sorted(scored, key=lambda match: (match[0], match[1]["published_at"]), reverse=True)[:5]]


def bounded_citations(allowed_ids: set[str], result):
    if isinstance(result, EventAssessment):
        actual = set(result.article_ids)
    else:
        actual = {key for item in result.predictions
                  for key in [*item.support_ids, *item.contradict_ids, *item.precedent_ids]}
        if any(not item.support_ids for item in result.predictions):
            raise ValueError("A forecast must cite at least one supporting source")
    if re.search(r"https?://|www\.", result.model_dump_json(), re.I):
        raise ValueError("Generated assessments must cite article IDs, not URLs")
    if not actual <= allowed_ids:
        raise ValueError("Unknown article citation")


def generation_step(db, payload):
    stage = payload["stage"]
    source = payload["source"]
    followup = payload.get("followup", [])
    allowed = {a["id"] for a in [*source, *payload["precedents"], *followup]}
    base = {"sources": source, "historical_context": payload["precedents"],
            "analysis_start": payload.get("analysis_start") or now().date().isoformat(),
            "previous_map_id": payload.get("previous_map_id"), "followup_evidence": followup}
    payload = {**payload, "analysis_start": base["analysis_start"]}
    if stage == "event":
        assessment, provenance = infer("event", "Extract the reported event and uncertainty. Treat reported claims as unverified unless the supplied sources directly substantiate them. User-provided or OSINT-submitted data is not independent confirmation. Distinguish retrieved dates from publication dates.",
                                       base, EventAssessment,
                                       lambda result: bounded_citations({a["id"] for a in source}, result))
        return {**payload, "stage": "prediction", "event": assessment.model_dump(), "event_provenance": provenance}
    base["event"] = payload["event"]
    if stage == "prediction":
        draft, provenance = infer(
            "prediction",
            "Generate 3–5 first-order predictions with secondary consequences and a third level only when causally justified. "
            "Include an alternative branch, distinct observable confirmation and refutation criteria, "
            "and explicit uncertainties. Select materially relevant diplomatic, political, security, economic or regulatory drivers rather than enumerating them all. First-order probabilities are marginal. Child probabilities "
            "are conditional on their parent. Supply a shared group only for truly mutually exclusive "
            "siblings. Consider public policy, diplomatic, or economic effects. Do not use silence as refutation.",
            base, Draft, lambda result: bounded_citations(allowed, result),
        )
        return {**payload, "stage": "challenge", "draft": draft.model_dump(), "draft_provenance": provenance}

    base["draft"] = payload["draft"]
    final, provenance = infer(
        "challenge",
        "Red-team this draft. Replace or revise weak causal links, probabilities and resolution criteria. "
        "Record weaknesses and alternative explanations. Preserve required graph limits. Use only the "
        "supplied IDs. Estimates are uncalibrated judgments, never derive them from fictitious frequencies.",
        base, Draft, lambda result: bounded_citations(allowed, result),
    )
    publish_map(db, payload, final, provenance)
    return None


def publish_map(db, payload, draft: Draft, provenance: dict):
    map_id = payload["map_id"]
    if db.get(IntelMap, map_id):
        return
    issued = now()
    event = {**payload["event"], "event_provenance": payload["event_provenance"],
             "draft_provenance": payload["draft_provenance"], "previous_map_id": payload.get("previous_map_id")}
    ids = [a["id"] for a in payload["source"]]
    db.add(IntelMap(id=map_id, created_at=issued, event=event, article_ids=ids))
    db.flush()
    by_key = {}
    by_input = {pred.key: pred for pred in draft.predictions}
    def depth(pred):
        level = 0
        while pred.parent:
            pred = by_input[pred.parent]
            level += 1
        return level
    for pred in sorted(draft.predictions, key=depth):
        forecast_id = uid()
        details = pred.model_dump(exclude={"key", "parent"})
        db.add(Forecast(id=forecast_id, map_id=map_id, parent_id=by_key.get(pred.parent), issued_at=issued,
                        deadline=issued + timedelta(days=pred.horizon_days), domain=pred.domain,
                        original={**details, "provenance": provenance, "estimate": "uncalibrated_model"}))
        db.flush()
        by_key[pred.key] = forecast_id
        query = " ".join([pred.title, *event["actors"], *event["regions"]])
        for token in sorted(terms(query))[:50]:
            db.add(ForecastTerm(term=token[:80], forecast_id=forecast_id))
        used = set()
        for stance, article_ids in (("supports", pred.support_ids), ("contradicts", pred.contradict_ids),
                                    ("precedent", pred.precedent_ids)):
            for article_id in article_ids:
                source = db.get(Article, article_id)
                if source and source.fingerprint not in used:
                    used.add(source.fingerprint)
                    db.add(Evidence(forecast_id=forecast_id, article_id=source.id, fingerprint=source.fingerprint,
                                    stance=stance, reasoning="Cited by the original model assessment.",
                                    provenance=provenance))


def similarity(first: set[str], second: set[str]) -> float:
    return len(first & second) / max(1, len(first | second))


def candidate_forecasts(db, article: Article) -> list[str]:
    data = article.data
    tokens = terms(" ".join([data["title"], data["excerpt"], *data["regions"]]))
    if not tokens:
        return []
    published = article_date(data["published_at"])
    count = func.count(ForecastTerm.term)
    candidates = (select(ForecastTerm.forecast_id).join(Forecast, Forecast.id == ForecastTerm.forecast_id)
                  .outerjoin(Resolution, Resolution.forecast_id == Forecast.id)
                  .where(ForecastTerm.term.in_(tokens), Forecast.issued_at <= published,
                         Forecast.deadline >= published, Resolution.forecast_id.is_(None))
                  .group_by(ForecastTerm.forecast_id).order_by(count.desc(), ForecastTerm.forecast_id).limit(12))
    result = []
    weights = [float(value) for value in os.getenv("SIGNAL_MATCH_WEIGHTS", "0.30,0.25,0.25,0.10,0.10").split(",")]
    if len(weights) != 5 or any(weight < 0 for weight in weights) or sum(weights) <= 0:
        raise ValueError("SIGNAL_MATCH_WEIGHTS requires five non-negative weights")
    source_vector = db.get(Embedding, f"article:{article.id}")
    candidate_ids = list(db.scalars(candidates))
    if source_vector and db.bind.dialect.name == "postgresql":
        from backend.intelmap.embeddings import MODEL
        distance = Embedding.vector.cosine_distance(source_vector.vector)
        vector_candidates = (select(Forecast.id).join(Embedding, Embedding.id == func.concat("forecast:", Forecast.id))
                             .outerjoin(Resolution, Resolution.forecast_id == Forecast.id)
                             .where(Embedding.id.like("forecast:%"), Embedding.model == MODEL,
                                    Forecast.issued_at <= published, Forecast.deadline >= published,
                                    Resolution.forecast_id.is_(None), distance < 0.30)
                             .order_by(distance).limit(12))
        candidate_ids = list(dict.fromkeys([*candidate_ids, *db.scalars(vector_candidates)]))
    for fid in candidate_ids:
        item = db.get(Forecast, fid)
        original = item.original
        root = db.get(IntelMap, item.map_id).event
        event_overlap = similarity(tokens, terms(original["title"]))
        entity_overlap = similarity(tokens, terms(" ".join(root["actors"])))
        geographic = similarity(set(data["regions"]), set(root["regions"]))
        temporal = 1.0  # Candidate SQL enforces the forecast window.
        semantic = cosine(source_vector, db.get(Embedding, f"forecast:{fid}")) if source_vector else None
        features = (semantic, entity_overlap, event_overlap, temporal, geographic)
        available = [(weight, value) for weight, value in zip(weights, features) if value is not None]
        total = sum(weight for weight, _ in available)
        score = sum(weight * value for weight, value in available) / total if total else 0
        if score >= 0.27 and (event_overlap > 0 or entity_overlap > 0 or (semantic or 0) > 0.70):
            result.append((score, fid))
    return [fid for _, fid in sorted(result, reverse=True)[:3]]


def verify_article(db, payload):
    item = db.get(Forecast, payload["forecast_id"])
    article = db.get(Article, payload["article_id"])
    if not item or not article or db.get(Resolution, item.id):
        return
    if db.query(Evidence).filter_by(forecast_id=item.id, fingerprint=article.fingerprint).first():
        return
    original = item.original
    latest = db.query(Revision).filter_by(forecast_id=item.id).order_by(Revision.created_at.desc()).first()
    probability = latest.probability if latest else original["probability"]
    result, provenance = infer(
        "verify",
        "Assess whether the article matches the forecasted action, actors, geography, and dates. "
        "Distinguish a discussion from materialized events. A possible resolution must be a resolution_candidate, "
        "never a confirmed or refuted decision. Return a provisional probability only if material evidence "
        "warrants it. Similarity and absence of news do not prove an outcome.",
        {"forecast": original, "issued_at": item.issued_at.isoformat(), "deadline": item.deadline.isoformat(),
         "probability": probability, "article": context(article)}, Verification,
    )
    db.query(Forecast).filter_by(id=item.id).with_for_update().first()
    if result.stance == "irrelevant" or db.get(Resolution, item.id):
        return
    evidence = Evidence(forecast_id=item.id, article_id=article.id, fingerprint=article.fingerprint,
                        stance=result.stance, reasoning=result.reasoning, provenance=provenance)
    db.add(evidence)
    db.flush()
    current = db.query(Revision).filter_by(forecast_id=item.id).order_by(Revision.created_at.desc()).first()
    current_probability = current.probability if current else original["probability"]
    estimate = result.probability if current_probability == probability else None
    if estimate is not None and not original["exclusive_group"] and abs(estimate - probability) >= 0.03:
        if ((result.stance == "contradicts" and estimate < probability)
                or (result.stance in {"supports", "partial"} and estimate > probability)):
            db.add(Revision(forecast_id=item.id, evidence_id=evidence.id, probability=estimate,
                            rationale=result.reasoning, provenance={**provenance, "estimate": "uncalibrated_model"}))
