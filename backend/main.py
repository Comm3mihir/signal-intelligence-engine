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

from backend.models.database import engine, init_db, SessionLocal
from data.seed.seed_data import populate_seed_data
from backend.api import organisations, signals, risks, transformation, chat, intelligence, intelmap, assistant
from backend.research.world_intelligence import REFRESH_SECONDS, refresh
from backend.intelmap.jobs import archive_articles, process_one

from backend.intelmap.access import production

PRODUCTION = production()



def refresh_sources():
    with SessionLocal() as db:
        archive_articles(db, refresh(db))


async def refresh_forever():
    while True:
        try:
            await asyncio.to_thread(refresh_sources)
        except Exception:
            logging.getLogger(__name__).exception("Could not refresh public intelligence")
        await asyncio.sleep(REFRESH_SECONDS)


def process_local_job():
    with SessionLocal() as db:
        process_one(db)


async def local_jobs_forever():
    while True:
        try:
            await asyncio.to_thread(process_local_job)
        except Exception:
            logging.getLogger(__name__).exception("IntelMap job failed")
        await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if PRODUCTION and os.getenv("SIGNAL_RUN_MIGRATIONS") == "1" and engine.dialect.name == "postgresql":
        from backend.intelmap.migrate import migrate
        await asyncio.to_thread(migrate)
    elif not PRODUCTION or engine.dialect.name == "sqlite":
        init_db()
    if not PRODUCTION and os.getenv("SIGNAL_SEED_DEMO") == "1":
        with SessionLocal() as db:
            populate_seed_data(db)
    workers = []
    if not PRODUCTION:
        if os.getenv("SIGNAL_AUTO_REFRESH", "1") == "1":
            workers.append(asyncio.create_task(refresh_forever()))
        if os.getenv("SIGNAL_LOCAL_WORKER", "1") == "1":
            workers.append(asyncio.create_task(local_jobs_forever()))
    try:
        yield
    finally:
        for worker in workers:
            worker.cancel()
        for worker in workers:
            with suppress(asyncio.CancelledError):
                await worker


app = FastAPI(
    title="SIGNAL Strategic Intelligence & Geopolitical Risk Engine",
    description="Enterprise strategic risk analysis engine mapping external OSINT events to internal business dependencies, transparent risk scoring, evidence traceability, and AI transformation priorities.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend
cors = os.getenv("SIGNAL_CORS_ORIGINS", "")
if not cors:
    cors = "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors.split(",") if origin.strip()],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include API Routers
app.include_router(organisations.router)
app.include_router(signals.router)
app.include_router(risks.router)
app.include_router(transformation.router)
app.include_router(chat.router)
app.include_router(intelligence.router)
app.include_router(intelmap.router)
app.include_router(assistant.router)

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
