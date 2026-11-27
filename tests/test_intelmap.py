import json
from datetime import timedelta

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.intelmap import gateway
from backend.intelmap.jobs import archive_articles, process_one
from backend.intelmap.metrics import bayesian_update, statistics
from backend.intelmap.models import Article, Forecast, Inference, Job, Revision, now
from backend.main import app
from backend.models.database import Base, get_db


def article(key, title, date):
    return {
        "id": key, "title": title, "excerpt": title, "url": f"https://example.org/{key}",
        "publisher": "Test Publisher", "published_at": date.isoformat(),
        "regions": ["Japan"], "topics": ["Trade policy"],
    }


def snapshot(*articles):
    return {"events": [{"id": row["id"], "articles": [row]} for row in articles]}


def draft(source):
    return {"predictions": [
        {"key": key, "parent": parent, "title": title, "domain": "trade", "scenario": scenario,
         "probability": 0.45, "horizon_days": 15, "reasoning": "The notified proposal starts a formal review.",
         "assumptions": ["Public consultation proceeds."], "alternatives": ["The timetable is postponed."],
         "weaknesses": ["No final notice has been published."],
         "confirm_if": "The ministry publishes a dated notice that implements the forecasted action.",
         "refute_if": "The ministry publishes a final decision explicitly rejecting the action.",
         "support_ids": [source], "contradict_ids": [], "precedent_ids": [], "exclusive_group": None}
        for key, parent, title, scenario in [
            ("notice", None, "Japan ministry publishes revised chip export notice", "consequence"),
            ("hearing", None, "Japan ministry schedules formal industry hearing", "consequence"),
            ("pause", None, "Japan ministry suspends the proposed review", "alternative"),
            ("licenses", "notice", "Japan ministry publishes an updated licensing application", "consequence"),
        ]
    ]}


def test_forecast_lifecycle_and_provider_failover(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'intelmap.sqlite3'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(gateway, "SessionLocal", session)
    for key in ("GROQ", "GEMINI"):
        monkeypatch.setenv(f"{key}_API_KEY", "fixture")
        monkeypatch.setenv(f"{key}_FREE_TIER_CONFIRMED", "1")
        monkeypatch.setenv(f"{key}_DAILY_TOKEN_BUDGET", "500000")
    monkeypatch.setenv("SIGNAL_EMBEDDINGS", "0")
    source = article("source", "Japan ministry proposes revised chip export notice", now() - timedelta(days=1))

    def fake_request(provider, system, content, schema, _maximum):
        assert "untrusted" in system
        data = json.loads(content)
        if provider.name == "groq":
            http_request = httpx.Request("POST", "https://example.org/")
            raise httpx.HTTPStatusError("Rate limited", request=http_request,
                                        response=httpx.Response(429, request=http_request))
        model = schema["title"]
        if model == "EventAssessment":
            assert data["sources"][0]["id"] == source["id"]
            result = {"title": source["title"], "actors": ["Japan ministry"], "regions": ["Japan"],
                      "date": "reported", "classification": "Trade policy",
                      "reported_developments": ["The ministry reportedly proposed a new notice."],
                      "unverified_claims": [], "article_ids": [source["id"]]}
        elif model == "Draft":
            result = draft(source["id"])
        else:
            assert model == "Verification"
            result = {"stance": "supports", "reasoning": "The ministry released a dated draft with the reported change.",
                      "probability": 0.60}
        return json.dumps(result), 100, 50, provider.model

    monkeypatch.setattr(gateway, "request", fake_request)

    def test_db():
        with session() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, test_db)
    with session() as db:
        archive_articles(db, snapshot(source))
    client = TestClient(app)
    assert client.post("/api/intelmap/generate", json={"article_ids": ["unknown"]}).status_code == 404
    response = client.post("/api/intelmap/generate", json={"article_ids": [source["id"]]})
    assert response.status_code == 202
    job = response.json()
    assert client.post("/api/intelmap/generate", json={"article_ids": [source["id"]]}).json() == job
    with session() as db:
        for _ in range(3):
            assert process_one(db)
        assert db.get(Job, job["job_id"]).state == "complete"
        assert db.query(Inference).filter_by(status="http_429").count()
        assert db.query(Inference).filter_by(provider="gemini", status="success").count() == 3

    path = f'/api/intelmap/maps/{job["map_id"]}'
    generated = client.get(path).json()
    assert len(generated["forecasts"]) == 4
    root = next(item for item in generated["forecasts"] if item["original"]["title"].endswith("export notice"))
    child = next(item for item in generated["forecasts"] if item["parent_id"] == root["id"])
    assert child["joint_probability"] == root["probability"] * child["probability"]
    assert root["evidence"][0]["article"]["url"] == source["url"]

    later = article("later", "Japan ministry publishes revised chip export notice", now())
    syndicated = {**later, "id": "duplicate", "url": "https://example.org/other"}
    with session() as db:
        archive_articles(db, snapshot(later))
        archive_articles(db, snapshot(syndicated))
        assert db.query(Article).count() == 3
        assert db.query(Job).filter_by(kind="verify").count() > 0
        for _ in range(3):
            if not process_one(db):
                break
        assert db.query(Revision).filter_by(forecast_id=root["id"]).count() == 1
        assert db.get(Forecast, root["id"]).original["probability"] == 0.45
    revised = next(item for item in client.get(path).json()["forecasts"] if item["id"] == root["id"])
    assert revised["probability"] == 0.60
    assert revised["truth_value"] is None
    assert revised["status"] == "supporting_evidence"

    review_url = f'/api/intelmap/forecasts/{root["id"]}/resolve'
    review = {"status": "confirmed", "reasoning": "The original notice was published as defined.",
              "credibility": "Official ministry publication"}
    assert client.post(review_url, json=review).status_code == 422
    assert client.post(review_url, json={**review, "article_id": later["id"]}).status_code == 422
    verified = {**review, "article_id": later["id"], "criteria_verified": True}
    assert client.post(review_url, json=verified).status_code == 201
    assert client.post(review_url, json=verified).status_code == 409
    metrics = client.get("/api/intelmap/evaluate").json()
    assert metrics["confirmed"] == 1
    assert metrics["original"] == {"count": 1, "brier": None, "calibration": []}
    assert metrics["revised_24h"]["count"] == 0


def test_probability_math_requires_sufficient_outcomes():
    assert bayesian_update(0.5, 3) == 0.75
    result = statistics([(0.75, 1)] * 12)
    assert result["brier"] == 0.0625
    assert result["calibration"] == [{"predicted": 0.75, "observed": 1, "count": 12}]
