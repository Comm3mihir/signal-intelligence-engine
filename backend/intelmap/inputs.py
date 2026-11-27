from datetime import datetime

from sqlalchemy.orm import Session

from backend.intelmap.analysis import fingerprint, unique_article_key
from backend.intelmap.jobs import add_once
from backend.intelmap.metrics import aware
from backend.intelmap.models import Article, now
from backend.models.database import CountryModel, ExternalSignalModel


def stored_input(db: Session, data: dict) -> Article:
    article_id = data["id"]
    article = db.get(Article, article_id)
    if article:
        return article
    add_once(db, Article(id=article_id, published_at=datetime.fromisoformat(data["published_at"]),
                         fingerprint=unique_article_key(data), data=data))
    db.commit()
    return db.get(Article, article_id)


def signal_input(signal: ExternalSignalModel, country: CountryModel | None) -> dict:
    try:
        published_at = aware(datetime.fromisoformat(signal.published_date))
    except (ValueError, TypeError):
        published_at = aware(signal.created_at) if signal.created_at else now()
    return {
        "id": fingerprint("osint", signal.id)[:32], "title": signal.title,
        "url": signal.source_url if (signal.source_url or "").startswith(("https://", "http://")) and "osint-wire.org/reports/" not in signal.source_url else "",
        "published_at": published_at.isoformat(), "publisher": signal.source_name or "OSINT submission",
        "excerpt": (signal.content or signal.summary or "")[:500], "content": (signal.content or "")[:8000],
        "regions": [country.name] if country else [], "topics": [signal.signal_type] if signal.signal_type else [],
        "provenance": "osint_submission",
    }


def get_signal_input(db: Session, signal_id: str) -> dict | None:
    row = db.get(ExternalSignalModel, signal_id)
    if not row:
        return None
    country = db.get(CountryModel, row.country_id) if row.country_id else None
    return signal_input(row, country)
