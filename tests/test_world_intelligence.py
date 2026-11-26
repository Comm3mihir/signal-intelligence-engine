from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.models.database import Base
from backend.research import world_intelligence as world


NOW = datetime(2026, 11, 26, 12, tzinfo=timezone.utc)


def test_news_market_and_saved_forecast(monkeypatch):
    feed = """<rss><channel><item>
      <title>Japan announces new semiconductor export controls</title>
      <link>https://example.org/japan#section</link>
      <pubDate>Tue, 24 Nov 2026 18:00:00 GMT</pubDate>
      <description>&lt;p&gt;Tokyo updated its chip policy.&lt;/p&gt;</description>
      </item><item><title>Bad URL</title><link>javascript:alert(1)</link>
      <pubDate>Tue, 24 Nov 2026 18:00:00 GMT</pubDate></item></channel></rss>"""
    first, = world.parse_feed(feed, "Publisher A", NOW)
    assert first["url"] == "https://example.org/japan"
    assert first["excerpt"] == "Tokyo updated its chip policy."
    assert first["regions"] == ["Japan"]
    second = {**first, "id": "second", "url": "https://example.net/japan", "publisher": "Publisher B"}
    series = world.market_series("NIKKEI225", "Nikkei 225", "https://example.org/markets", None,
                                 [("2026-11-23", "100"), ("2026-11-25", "102")])
    event, = world.build_events([first, second], [series])
    assert len(event["articles"]) == 2
    assert event["market_moves"][0]["change_pct"] == 2
    forecast = world.make_forecast(event, NOW)
    assert len(forecast["evidence"]) == 2
    assert forecast["deadline"].startswith("2026-12-10")

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.astimezone(tz) if tz else NOW.replace(tzinfo=None)

    monkeypatch.setattr(world, "datetime", FrozenDateTime)
    monkeypatch.setattr(world, "FEEDS", {"Publisher A": "https://example.org/feed"})
    monkeypatch.setattr(world, "STOCKS", {})
    monkeypatch.setattr(world, "download", lambda *args, **kwargs: feed)
    monkeypatch.setattr(world, "fred_prices", lambda now: [series])
    monkeypatch.setattr(world, "REFRESH_SECONDS", 0)
    with Session(engine) as db:
        original = world.refresh(db)["events"][0]["forecast"]
        assert original is not None

    def unavailable(*args, **kwargs):
        raise world.requests.Timeout()

    monkeypatch.setattr(world, "download", unavailable)
    with Session(engine) as db:
        refreshed = world.refresh(db)
        assert refreshed["sources"]["Publisher A"]["status"] == "stale"
        assert refreshed["events"][0]["forecast"] == original
        assert world.list_forecasts(db) == [original]
