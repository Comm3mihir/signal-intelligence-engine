from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import base64
import secrets
import logging
from contextlib import asynccontextmanager, suppress

import uvicorn
import os
import sys

# Ensure root directory is on sys.path for backend package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import init_db, SessionLocal
from data.seed.seed_data import populate_seed_data
from backend.api import organisations, signals, risks, transformation, chat, intelligence, intelmap
from backend.research.world_intelligence import REFRESH_SECONDS, refresh
from backend.intelmap.jobs import archive_articles, process_one

PRODUCTION = os.getenv("SIGNAL_ENV") == "production" or bool(os.getenv("VERCEL"))



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
    if not PRODUCTION:
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("SIGNAL_CORS_ORIGINS", "").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def authenticate_workspace(request: Request, call_next):
    if not PRODUCTION or request.method == "OPTIONS" or request.url.path in {"/", "/api/intelmap/workflows/tick"}:
        return await call_next(request)
    password = os.getenv("SIGNAL_WORKSPACE_PASSWORD", "")
    username = os.getenv("SIGNAL_WORKSPACE_USER", "signal")
    authorization = request.headers.get("authorization", "")
    expected = "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()
    if not password or not secrets.compare_digest(authorization.encode(), expected.encode()):
        return JSONResponse({"detail": "Workspace sign-in required."}, status_code=401,
                            headers={"WWW-Authenticate": 'Basic realm="SIGNAL"'})
    return await call_next(request)


# Include API Routers
app.include_router(organisations.router)
app.include_router(signals.router)
app.include_router(risks.router)
app.include_router(transformation.router)
app.include_router(chat.router)
app.include_router(intelligence.router)
app.include_router(intelmap.router)

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
