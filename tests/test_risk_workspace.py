import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.models.database import Base, IntelligenceRecord, get_db
from backend.research.osint_collector import OSINTCollector


def test_manual_risk_and_public_answers_without_demo_graph():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        signal = OSINTCollector.create_signal_from_raw(
            db, "Shipping disruption", "Japan", "Shipping", "Test publisher",
            "A port closed temporarily.", "https://example.org/shipping",
        )["signal"]
        signal_id = signal.id
        article = {
            "title": "Japan port closes", "publisher": "Test publisher",
            "excerpt": "A port closed temporarily.", "published_at": "2026-11-26T12:00:00+00:00",
            "url": "https://example.org/shipping",
        }
        scenario = {"event_title": article["title"], "forecast": "Operators may issue a new advisory.",
                    "assumption": "The port remains closed.", "indicator": "An official routing notice.",
                    "deadline": "2026-12-10T12:00:00+00:00", "evidence": [article]}
        event = {"regions": ["Japan"], "topics": ["Shipping"], "articles": [article], "forecast": scenario}
        market = {"symbol": "NVDA", "name": "Nvidia", "currency": "USD",
                  "source_url": "https://example.org/market",
                  "observations": [{"close": 100, "date": "2026-11-24"}, {"close": 110, "date": "2026-11-25"}]}
        db.add(IntelligenceRecord(id="snapshot", payload=json.dumps({"events": [event], "markets": [market]})))
        db.commit()

    def test_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    try:
        client = TestClient(app)
        assert client.get("/api/risks/").json() == []
        news = client.post("/api/chat/", json={"query": "Latest news about Japan"}).json()
        assert "Japan port closes" in news["answer"]
        assert news["sources"][0]["url"] == article["url"]
        forecast = client.post("/api/chat/", json={"query": "Show me the latest forecasts."}).json()
        assert scenario["forecast"] in forecast["answer"]
        assert "2026-12-10" in forecast["answer"]
        close = client.post("/api/chat/", json={"query": "What was the latest close for NVDA?"}).json()
        assert "110.00 USD (+10.00%" in close["answer"]
        payload = {"title": "Port delay exposure", "description": "Reduced throughput may delay shipments.",
                   "signal_id": signal_id, "likelihood": 5, "impact": 5, "exposure": 5,
                   "dependency_weight": 5, "evidence_confidence": 0.5}
        res = client.post("/api/risks/", json=payload)
        assert res.status_code == 201
        risk = res.json()
        assert risk["normalized_score"] == 50
        assert risk["signal_title"] == "Shipping disruption"
        assert risk["source_url"] == article["url"]
        assert risk["evidence_snippets"][0]["snippet"] == article["excerpt"]
        assert client.get("/api/risks/").json() == [risk]
        assert client.post("/api/risks/", json={**payload, "signal_id": "missing"}).status_code == 404
        assert client.post("/api/risks/", json={**payload, "likelihood": 6}).status_code == 422
        answer = client.post("/api/chat/", json={"query": "What are our highest risks?"}).json()
        assert "Port delay exposure" in answer["answer"]
    finally:
        app.dependency_overrides.pop(get_db)
        engine.dispose()
