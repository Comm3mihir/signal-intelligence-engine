from collections import defaultdict
from datetime import timedelta
from statistics import mean

from backend.intelmap.models import Forecast, Resolution, Revision, now


def aware(value):
    from datetime import timezone
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def bayesian_update(prior: float, likelihood_ratio: float) -> float:
    """Apply an externally documented likelihood ratio to prior odds."""
    import math
    if not 0 < prior < 1 or not math.isfinite(likelihood_ratio) or likelihood_ratio <= 0:
        raise ValueError("Expected a probability between 0 and 1 and a positive finite likelihood ratio")
    return 1 / (1 + (1 - prior) / prior / likelihood_ratio)


def statistics(rows):
    bins = defaultdict(list)
    for probability, truth in rows:
        bins[min(9, int(probability * 10))].append((probability, truth))
    return {
        "count": len(rows),
        "brier": mean((p - truth) ** 2 for p, truth in rows) if len(rows) >= 10 else None,
        "calibration": [
            {"predicted": mean(row[0] for row in group), "observed": mean(row[1] for row in group), "count": len(group)}
            for _, group in sorted(bins.items()) if len(group) >= 3
        ] if len(rows) >= 10 else [],
    }


def evaluate(db):
    forecasts = db.query(Forecast).all()
    resolutions = {r.forecast_id: r for r in db.query(Resolution)}
    revisions = defaultdict(list)
    for revision in db.query(Revision).order_by(Revision.created_at):
        revisions[revision.forecast_id].append(revision)
    original, revised_24h = [], []
    by_domain, by_model, revised_by_model, by_horizon = (defaultdict(list) for _ in range(4))
    counts = {"active": 0, "confirmed": 0, "refuted": 0, "inconclusive": 0}
    for forecast in forecasts:
        resolution = resolutions.get(forecast.id)
        truth = resolution.truth_value if resolution else None
        if truth is None:
            expired = resolution or aware(forecast.deadline) <= now()
            counts["inconclusive" if expired else "active"] += 1
            continue
        counts["confirmed" if truth == 1 else "refuted"] += 1
        parent = resolutions.get(forecast.parent_id)
        if forecast.parent_id and (not parent or parent.truth_value != 1):
            continue  # Conditional probabilities are only evaluated when their condition occurred.
        row = (forecast.original["probability"], truth)
        original.append(row)
        by_domain[forecast.domain].append(row)
        horizon = forecast.original["horizon_days"]
        by_horizon["1–7 days" if horizon <= 7 else "8–30 days" if horizon <= 30 else "31–180 days"].append(row)
        provenance = forecast.original["provenance"]
        by_model[f'{provenance["provider"]}/{provenance["model"]}'].append(row)
        # Also cap the evaluation at the cited report date if it precedes analyst review.
        report_time = None
        if resolution.article_id:
            from backend.intelmap.models import Article
            report = db.get(Article, resolution.article_id)
            report_time = aware(report.published_at) if report else None
        earliest = min(aware(resolution.created_at), aware(forecast.deadline), report_time or aware(resolution.created_at))
        cutoff = earliest - timedelta(hours=24)
        for revision in reversed(revisions[forecast.id]):
            if aware(revision.created_at) <= cutoff:
                revised_row = (revision.probability, truth)
                revised_24h.append(revised_row)
                source = revision.provenance
                revised_by_model[f'{source["provider"]}/{source["model"]}'].append(revised_row)
                break
    total = len(forecasts)
    return {
        **counts, "total": total,
        "resolved": counts["confirmed"] + counts["refuted"],
        "resolution_rate": (counts["confirmed"] + counts["refuted"]) / total if total else None,
        "average_horizon_days": mean(r.original["horizon_days"] for r in forecasts) if total else None,
        "original": statistics(original), "revised_24h": statistics(revised_24h),
        "by_domain": {key: statistics(rows) for key, rows in by_domain.items()},
        "by_horizon": {key: statistics(rows) for key, rows in by_horizon.items()},
        "by_model": {key: statistics(rows) for key, rows in by_model.items()},
        "revised_by_model": {key: statistics(rows) for key, rows in revised_by_model.items()},
        "base_rate_benchmark": None,
    }
