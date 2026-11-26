from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from contextlib import asynccontextmanager, suppress

import uvicorn
import os
import sys

# Ensure root directory is on sys.path for backend package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import init_db, SessionLocal
from data.seed.seed_data import populate_seed_data
from backend.api import organisations, signals, risks, transformation, chat, intelligence
from backend.research.world_intelligence import REFRESH_SECONDS, refresh


def refresh_sources():
    with SessionLocal() as db:
        refresh(db)


async def refresh_forever():
    while True:
        try:
            await asyncio.to_thread(refresh_sources)
        except Exception:
            logging.getLogger(__name__).exception("Could not refresh public intelligence")
        await asyncio.sleep(REFRESH_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if os.getenv("SIGNAL_SEED_DEMO") == "1":
        with SessionLocal() as db:
            populate_seed_data(db)
    worker = asyncio.create_task(refresh_forever()) if os.getenv("SIGNAL_AUTO_REFRESH", "1") == "1" else None
    try:
        yield
    finally:
        if worker:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker


app = FastAPI(
    title="SIGNAL Strategic Intelligence & Geopolitical Risk Engine",
    description="Enterprise strategic risk analysis engine mapping external OSINT events to internal business dependencies, transparent risk scoring, evidence traceability, and AI transformation priorities.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(organisations.router)
app.include_router(signals.router)
app.include_router(risks.router)
app.include_router(transformation.router)
app.include_router(chat.router)
app.include_router(intelligence.router)

@app.get("/")
def root():
    return {
        "engine": "SIGNAL Strategic Intelligence Engine",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
