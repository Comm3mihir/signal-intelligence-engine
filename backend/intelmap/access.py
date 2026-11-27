import os
import secrets
from datetime import timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.intelmap.models import ProviderDay, now
from backend.models.database import get_db


def production() -> bool:
    return os.getenv("SIGNAL_ENV") == "production" or os.getenv("RENDER") == "true"


def analyst(request: Request, db: Session = Depends(get_db)):
    token = os.getenv("SIGNAL_ANALYST_TOKEN", "")
    if production() and not token:
        raise HTTPException(503, "Analyst access is not configured on Render.")
    if token and not secrets.compare_digest(request.headers.get("authorization", "").encode(),
                                            f"Bearer {token}".encode()):
        raise HTTPException(401, "Enter a valid analyst access token.")
    if production() and db.get_bind().dialect.name != "postgresql":
        raise HTTPException(503, "AI features require a hosted PostgreSQL database on Render.")
    return db


def throttle(db: Session, category: str, default: int):
    limit = int(os.getenv(f"SIGNAL_{category.upper()}_PER_HOUR", str(default)))
    hour = now().astimezone(timezone.utc).strftime("%Y%m%d%H")
    key = f"limit:{category}:{hour}"
    if db.get(ProviderDay, key) is None:
        try:
            with db.begin_nested():
                db.add(ProviderDay(id=key, reserved=0))
                db.flush()
        except IntegrityError:
            pass
    changed = db.execute(update(ProviderDay).where(
        ProviderDay.id == key, ProviderDay.reserved < limit
    ).values(reserved=ProviderDay.reserved + 1))
    db.commit()
    if changed.rowcount != 1:
        raise HTTPException(429, "The workspace has reached this feature’s hourly limit.", headers={"Retry-After": "3600"})
