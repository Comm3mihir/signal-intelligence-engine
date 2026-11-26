"""Public-source news, daily market observations, and evidence-linked scenarios."""

import csv
import hashlib
import json
import math
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from threading import Lock
from urllib.parse import quote, urlsplit
from xml.etree import ElementTree
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
from sqlalchemy.orm import Session

from backend.models.database import IntelligenceRecord


FEEDS = {
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "France 24": "https://www.france24.com/en/rss",
    "DW": "https://rss.dw.com/rdf/rss-en-all",
}
BENCHMARKS = {"SP500": "S&P 500", "NASDAQCOM": "Nasdaq Composite", "NIKKEI225": "Nikkei 225"}
STOCKS = {"AAPL": "Apple", "NVDA": "Nvidia", "TSM": "TSMC"}
REGIONS = {
    "United States": r"united states|u\.s\.|washington|american",
    "China": r"china|chinese|beijing",
    "Taiwan": r"taiwan|taiwanese|taipei",
    "European Union": r"european union|eu|brussels",
    "Japan": r"japan|japanese|tokyo",
    "India": r"india|indian|new delhi",
    "Russia": r"russia|russian|moscow",
    "Ukraine": r"ukraine|ukrainian|kyiv",
    "Israel": r"israel|israeli",
    "Palestinian territories": r"gaza|palestinian|west bank",
    "Iran": r"iran|iranian|tehran",
    "United Kingdom": r"united kingdom|u\.k\.|britain|british",
    "South Korea": r"south korea|seoul",
    "France": r"france|french|paris",
    "Germany": r"germany|german|berlin",
}
TOPICS = {
    "Trade policy": r"tariffs?|trade deal|export controls?|trade restrictions?|import duties",
    "Monetary policy": r"interest rates?|central bank|rate cuts?|rate hikes?",
    "Energy and shipping": r"oil prices?|crude oil|natural gas|shipping lanes?|strait of hormuz|red sea",
    "Diplomacy and conflict": r"ceasefire|peace talks|sanctions?|airstrikes?|military strikes?",
    "Semiconductors": r"semiconductors?|chipmakers?|microchips?|tsmc|nvidia",
}
SCENARIOS = {
    "Trade policy": (
        "Affected governments may revise or clarify the reported trade measure within 14 days.",
        "The reported measure remains active and at least one affected government has scope to respond.",
        "An official notice changes the rate, scope, exemptions, or effective date.",
    ),
    "Monetary policy": (
        "The central bank may update its policy guidance within 14 days.",
        "The reported issue remains material and policymakers have a scheduled decision or public remarks.",
        "A decision or official statement specifies a change to the rate outlook.",
    ),
    "Energy and shipping": (
        "Authorities or operators may issue a new supply or routing advisory within 14 days.",
        "The reported energy or transport issue continues to affect operating conditions.",
        "A dated operator or government advisory changes access, routing, or supply guidance.",
    ),
    "Diplomacy and conflict": (
        "An involved government or mediator may announce a formal diplomatic response within 14 days.",
        "The parties remain publicly engaged and have a channel for formal communication.",
        "An official readout announces talks, a suspension of talks, or a new diplomatic measure.",
    ),
    "Semiconductors": (
        "An affected chipmaker or regulator may clarify the operational impact within 14 days.",
        "The reported development has a material impact requiring a public update.",
        "A company filing or regulator notice specifies a change to guidance, capacity, or licensing.",
    ),
}
STOP_WORDS = set("about after against also amid been could first from have into over says said their them they this were what when where which will with would years".split())
REFRESH_SECONDS = 600
MAX_DOWNLOAD_BYTES = 2_000_000
_REFRESH_LOCK = Lock()


class PlainText(HTMLParser):
    def __init__(self, markup: str):
        super().__init__()
        self.parts = []
        self.feed(markup)

    def handle_data(self, data: str):
        self.parts.append(data)


def download(url: str, params=None) -> str:
    with requests.get(url, params=params, timeout=(4, 8), stream=True,
                      headers={"User-Agent": "Mozilla/5.0 (compatible; SIGNAL/1.0)"}) as response:
        response.raise_for_status()
        content = bytearray()
        for chunk in response.iter_content(16_384):
            content.extend(chunk)
            if len(content) > MAX_DOWNLOAD_BYTES:
                raise ValueError("Source response exceeded the size limit")
        return content.decode("utf-8-sig", errors="replace")


def article_date(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = parsedate_to_datetime(value)
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def parse_feed(xml: str, publisher: str, now: datetime) -> list[dict]:
    root = ElementTree.fromstring(xml)
    articles = {}
    for item in root.findall(".//{*}item"):
        url = (item.findtext("{*}link") or "").strip()
        parsed_url = urlsplit(url)
        title = " ".join((item.findtext("{*}title") or "").split())[:350]
        raw_date = item.findtext("{*}pubDate") or item.findtext("{*}date") or ""
        if parsed_url.scheme not in {"https", "http"} or not parsed_url.hostname or not title:
            continue
        try:
            published = article_date(raw_date)
        except (ValueError, TypeError, OverflowError):
            continue
        if not now - timedelta(days=7) <= published <= now + timedelta(minutes=5):
            continue
        url = parsed_url._replace(fragment="").geturl()
        excerpt = " ".join(" ".join(PlainText(item.findtext("{*}description") or "").parts).split())[:650]
        haystack = f"{title} {excerpt}"
        articles[url] = {
            "id": hashlib.sha256(url.encode()).hexdigest()[:24],
            "title": title, "url": url, "publisher": publisher, "excerpt": excerpt,
            "published_at": published.isoformat(),
            "regions": [name for name, match in REGIONS.items() if re.search(rf"\b(?:{match})(?!\w)", haystack, re.I)],
            "topics": [name for name, match in TOPICS.items() if re.search(rf"\b(?:{match})\b", haystack, re.I)],
        }
    if not root.findall(".//{*}item"):
        raise ValueError("Source returned no RSS items")
    return sorted(articles.values(), key=lambda a: a["published_at"], reverse=True)[:35]


def market_series(symbol: str, name: str, source_url: str, currency: str | None, rows: list) -> dict:
    prices = {}
    for session, close in rows:
        try:
            close = float(close)
            date.fromisoformat(session)
        except (ValueError, TypeError):
            continue
        if math.isfinite(close) and close > 0:
            prices[session] = close
    observations = [{"date": day, "close": prices[day]} for day in sorted(prices)[-30:]]
    if len(observations) < 2:
        raise ValueError(f"Not enough observations for {symbol}")
    return {"symbol": symbol, "name": name, "source_url": source_url, "currency": currency,
            "observations": observations}


def fred_prices(now: datetime) -> list[dict]:
    csv_data = download("https://fred.stlouisfed.org/graph/fredgraph.csv", {
        "id": ",".join(BENCHMARKS), "cosd": (now.date() - timedelta(days=55)).isoformat(),
    })
    rows = list(csv.DictReader(csv_data.splitlines()))
    results = []
    for symbol, name in BENCHMARKS.items():
        try:
            results.append(market_series(symbol, name, f"https://fred.stlouisfed.org/series/{symbol}", None,
                                         [(r.get("observation_date"), r.get(symbol)) for r in rows]))
        except ValueError:
            continue
    if not results:
        raise ValueError("FRED returned no usable series")
    return results


def stock_prices(symbol: str, now: datetime) -> dict:
    data = json.loads(download(f"https://query2.finance.yahoo.com/v8/finance/chart/{quote(symbol)}",
                               {"range": "2mo", "interval": "1d"}))
    result = data["chart"]["result"][0]
    meta = result["meta"]
    # Daily candles can contain an intraday observation for the active US session.
    # Use only dates before the current exchange day.
    zone = ZoneInfo(meta["exchangeTimezoneName"])
    cutoff = now.astimezone(zone).date()
    rows = []
    for timestamp, close in zip(result["timestamp"], result["indicators"]["quote"][0]["close"]):
        session = datetime.fromtimestamp(timestamp, zone).date()
        if session < cutoff:
            rows.append((session.isoformat(), close))
    return market_series(symbol, STOCKS[symbol], f"https://finance.yahoo.com/quote/{symbol}/history/",
                         meta["currency"], rows)


def headline_terms(title: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", title.lower())) - STOP_WORDS


def related(first: dict, second: dict) -> bool:
    gap = abs(article_date(first["published_at"]) - article_date(second["published_at"]))
    if gap > timedelta(days=2):
        return False
    a, b = headline_terms(first["title"]), headline_terms(second["title"])
    common = len(a & b)
    if common >= 3 and common / max(1, len(a | b)) >= 0.58:
        return True
    return bool(set(first["topics"]) & set(second["topics"]) and
                set(first["regions"]) & set(second["regions"]) and
                common >= 3 and common / max(1, len(a | b)) >= 0.30)


def market_context(event: dict, markets: list[dict]) -> list[dict]:
    headlines = " ".join(f"{a['title']} {a['excerpt']}" for a in event["articles"])
    symbols = {"AAPL": r"\bapple(?: inc| shares| stock| ceo| iphone| watch)\b|\biphone\b|\baapl\b", "NVDA": r"\bnvidia\b", "TSM": r"\btsmc\b|taiwan semiconductor"}
    watch = [symbol for symbol, pattern in symbols.items() if re.search(pattern, headlines, re.I)]
    for region, symbol in (("United States", "SP500"), ("Japan", "NIKKEI225")):
        if region in event["regions"]:
            watch.append(symbol)
    day = event["articles"][-1]["published_at"][:10]
    available = {entry["symbol"]: entry for entry in markets}
    benchmark = {point["date"]: point["close"] for point in available.get("SP500", {}).get("observations", [])}
    moves = []
    for symbol in watch:
        if symbol not in available:
            continue
        series = available[symbol]
        before = [point for point in series["observations"] if point["date"] < day]
        after = [point for point in series["observations"] if point["date"] > day]
        if not before or not after:
            continue
        start, end = before[-1], after[0]
        move = (end["close"] / start["close"] - 1) * 100
        relative = None
        if symbol in STOCKS and start["date"] in benchmark and end["date"] in benchmark:
            relative = round(move - (benchmark[end["date"]] / benchmark[start["date"]] - 1) * 100, 2)
        moves.append({"symbol": symbol, "start": start["date"], "end": end["date"],
                      "change_pct": round(move, 2), "relative_pp": relative, "source_url": series["source_url"]})
    return moves


def build_events(articles: list[dict], markets: list[dict]) -> list[dict]:
    events = []
    for article in sorted(articles, key=lambda a: (a["published_at"], a["id"])):
        event = next((e for e in events if related(e["articles"][0], article)), None)
        if event is None:
            events.append({"id": article["id"], "articles": [article]})
        else:
            event["articles"].append(article)
    for event in events:
        event["articles"].reverse()
        event["regions"] = sorted({region for a in event["articles"] for region in a["regions"]})
        event["topics"] = sorted({topic for a in event["articles"] for topic in a["topics"]})
        event["market_moves"] = market_context(event, markets)
    events.sort(key=lambda e: e["articles"][0]["published_at"], reverse=True)
    for event in events:
        regions, topics = set(event["regions"]), set(event["topics"])
        published = article_date(event["articles"][0]["published_at"])
        event["related_events"] = [
            {"id": other["id"], "title": other["articles"][0]["title"],
             "shared_regions": sorted(regions.intersection(other["regions"])),
             "shared_topics": sorted(topics.intersection(other["topics"]))}
            for other in events
            if event is not other and regions.intersection(other["regions"]) and topics.intersection(other["topics"])
            and abs(published - article_date(other["articles"][0]["published_at"])) <= timedelta(days=3)
        ][:3]
    return events


def make_forecast(event: dict, now: datetime) -> dict | None:
    if not event["topics"] or not event["regions"]:
        return None
    # Require a recent report before publishing a forward-looking scenario.
    if now - article_date(event["articles"][0]["published_at"]) > timedelta(days=2):
        return None
    topic = event["topics"][0]
    prediction, assumption, indicator = SCENARIOS[topic]
    return {
        "id": event["id"], "event_title": event["articles"][0]["title"],
        "topic": topic, "regions": event["regions"], "forecast": prediction, "assumption": assumption,
        "indicator": indicator, "invalidation": "The indicator is absent by the deadline or an official source contradicts the premise.",
        "issued_at": now.isoformat(), "deadline": (now + timedelta(days=14)).isoformat(),
        "evidence": [{key: article[key] for key in ("title", "publisher", "url")}
                     for article in event["articles"]],
    }


def read_record(db: Session, key: str, default):
    record = db.get(IntelligenceRecord, key)
    return json.loads(record.payload) if record else default


def list_forecasts(db: Session) -> list[dict]:
    records = db.query(IntelligenceRecord).filter(IntelligenceRecord.id.startswith("forecast:")).all()
    return sorted((json.loads(record.payload) for record in records),
                  key=lambda entry: entry["issued_at"], reverse=True)


def refresh(db: Session) -> dict:
    with _REFRESH_LOCK:
        now = datetime.now(timezone.utc)
        previous = read_record(db, "snapshot", {})
        if previous and (now - article_date(previous["refreshed_at"])).total_seconds() < REFRESH_SECONDS:
            return previous
        old_sources = previous.get("sources", {})
        jobs = {name: (lambda url=url, name=name: parse_feed(download(url), name, now))
                for name, url in FEEDS.items()}
        jobs["FRED"] = lambda: fred_prices(now)
        for symbol in STOCKS:
            jobs[symbol] = lambda symbol=symbol: [stock_prices(symbol, now)]
        sources = {}
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            futures = {name: pool.submit(job) for name, job in jobs.items()}
            for name, future in futures.items():
                try:
                    rows = future.result()
                    if name in FEEDS:
                        recent = {a["url"]: a for a in old_sources.get(name, {}).get("rows", [])
                                  if now - article_date(a["published_at"]) <= timedelta(days=7)}
                        recent.update({a["url"]: a for a in rows})
                        rows = sorted(recent.values(), key=lambda a: a["published_at"], reverse=True)[:120]
                    sources[name] = {"status": "ok", "updated_at": now.isoformat(), "rows": rows}
                except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, ZoneInfoNotFoundError, ElementTree.ParseError):
                    old = old_sources.get(name, {})
                    sources[name] = {"status": "stale" if old.get("rows") else "unavailable",
                                     "updated_at": old.get("updated_at"), "rows": old.get("rows", [])}
        articles = {a["url"]: a for name in FEEDS for a in sources[name]["rows"]
                    if now - article_date(a["published_at"]) <= timedelta(days=7)}
        markets = [entry for name in ("FRED", *STOCKS) for entry in sources[name]["rows"]]
        events = build_events(list(articles.values()), markets)
        previous_forecasts = {entry["id"]: entry for entry in list_forecasts(db)}
        for event in events:
            forecast = previous_forecasts.get(event["id"])
            if forecast is None:
                # An older headline can arrive late and change the cluster anchor.
                # Keep the original issue date and evidence if an article overlaps.
                urls = {article["url"] for article in event["articles"]}
                forecast = next((entry for entry in previous_forecasts.values()
                                 if any(article["url"] in urls for article in entry["evidence"])), None)
            if forecast is None:
                forecast = make_forecast(event, now)
                if forecast:
                    db.add(IntelligenceRecord(id=f"forecast:{forecast['id']}", payload=json.dumps(forecast)))
            event["forecast"] = forecast
        snapshot = {"refreshed_at": now.isoformat(), "sources": sources, "events": events, "markets": markets}
        db.merge(IntelligenceRecord(id="snapshot", payload=json.dumps(snapshot)))
        db.commit()
        return snapshot
