import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.intelmap.access import production
from backend.research.world_intelligence import FEEDS, list_forecasts, read_record, refresh


router = APIRouter(prefix="/api/intelligence", tags=["World Intelligence"])


@router.get("/")
def get_intelligence(db: Session = Depends(get_db)):
    scheduled = production() and bool(os.getenv("SIGNAL_SCHEDULER_SECRET"))
    snapshot = read_record(db, "snapshot", {}) if scheduled else {}
    if not snapshot:
        snapshot = refresh(db)
    if not snapshot:
        raise HTTPException(503, detail="Waiting for the first scheduled news refresh.")
    return {
        **snapshot,
        "sources": [
            {"name": name, "kind": "news" if name in FEEDS else "market",
             "status": source["status"], "updated_at": source["updated_at"]}
            for name, source in snapshot["sources"].items()
        ],
    }


@router.get("/forecasts")
def get_forecasts(db: Session = Depends(get_db)):
    return [{**entry, "review": read_record(db, f"review:{entry['id']}", None)}
            for entry in list_forecasts(db)]


@router.get("/articles/{article_id}")
def get_article(article_id: str, db: Session = Depends(get_db)):
    snapshot = read_record(db, "snapshot", {})
    for event in snapshot.get("events", []):
        for article in event["articles"]:
            if article["id"] == article_id:
                return article
    raise HTTPException(status_code=404, detail="Article no longer in the current news snapshot")
