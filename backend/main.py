from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys

# Ensure root directory is on sys.path for backend package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import init_db, SessionLocal
from data.seed.seed_data import populate_seed_data
from backend.api import organisations, signals, risks, transformation, chat

app = FastAPI(
    title="SIGNAL Strategic Intelligence & Geopolitical Risk Engine",
    description="Enterprise strategic risk analysis engine mapping external OSINT events to internal business dependencies, transparent risk scoring, evidence traceability, and AI transformation priorities.",
    version="1.0.0"
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

@app.on_event("startup")
def startup_event():
    init_db()
    db = SessionLocal()
    try:
        populate_seed_data(db)
    finally:
        db.close()

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
