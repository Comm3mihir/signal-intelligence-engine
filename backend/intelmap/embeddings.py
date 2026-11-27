"""Optional free-tier cloud embeddings with a single, versioned vector space."""

import math
import os
import time

import httpx

from backend.intelmap.gateway import CapacityUnavailable, Provider, reserve
from backend.intelmap.models import Embedding, Inference
from backend.models.database import SessionLocal


MODEL = "gemini-embedding-001"
DIMENSIONS = 768


def enabled() -> bool:
    return (os.getenv("SIGNAL_EMBEDDINGS") == "1"
            and os.getenv("GEMINI_FREE_TIER_CONFIRMED") == "1" and bool(os.getenv("GEMINI_API_KEY")))


def store_embedding(db, key: str, text: str):
    if not enabled() or db.get(Embedding, key):
        return
    key_value = os.environ["GEMINI_API_KEY"]
    provider = Provider("gemini", MODEL, key_value, int(os.getenv("GEMINI_DAILY_TOKEN_BUDGET", "40000")))
    text = text[:2500]
    if not reserve(provider, len(text.encode())):
        raise CapacityUnavailable("Waiting for free embedding budget.")
    started = time.monotonic()
    status = "success"
    count = None
    values = None
    try:
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:embedContent",
            headers={"x-goog-api-key": key_value},
            json={"model": f"models/{MODEL}", "content": {"parts": [{"text": text}]},
                  "outputDimensionality": DIMENSIONS},
            timeout=httpx.Timeout(12, connect=3), follow_redirects=False,
        )
        response.raise_for_status()
        result = response.json()
        values = result["embedding"]["values"]
        count = result.get("usageMetadata", {}).get("promptTokenCount")
        if len(values) != DIMENSIONS or not all(math.isfinite(value) for value in values):
            raise ValueError("Unexpected embedding response")
    except httpx.HTTPStatusError as exc:
        status = f"http_{exc.response.status_code}"
    except (httpx.RequestError, ValueError, KeyError, TypeError):
        status = "invalid_or_unavailable"
    with SessionLocal() as metrics:
        metrics.add(Inference(cache_key=key, provider="gemini", model=MODEL, task="embedding", status=status,
                              milliseconds=int((time.monotonic() - started) * 1000), input_tokens=count))
        metrics.commit()
    if status != "success":
        raise CapacityUnavailable("Cloud embedding is temporarily unavailable.")
    db.add(Embedding(id=key, model=MODEL, vector=values))
    db.flush()


def cosine(first, second) -> float | None:
    if not first or not second or first.model != MODEL or second.model != MODEL:
        return None
    a, b = first.vector, second.vector
    norm = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    return max(0, min(1, sum(x * y for x, y in zip(a, b)) / norm)) if norm else None
