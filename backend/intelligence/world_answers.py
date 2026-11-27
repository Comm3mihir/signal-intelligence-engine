"""Answer supported questions from the latest collected public data."""

import re

from sqlalchemy.orm import Session

from backend.research.world_intelligence import headline_terms, read_record


QUERY_WORDS = set(
    "tell give show latest recent current today news headline headlines articles article reporting "
    "reports report world international events event happening market markets stock stocks close closing "
    "price prices quote quotes change move forecast forecasts scenario scenarios outlook prediction "
    "predictions what how did doing about please data whats want know was were are time date happened the for can could you and this some".split()
)
MARKET_ALIASES = {
    "SP500": r"\bs\s*&\s*p\s*500\b|\bsp500\b",
    "NASDAQCOM": r"\bnasdaq(?: composite)?\b",
    "NIKKEI225": r"\bnikkei(?: 225)?\b",
    "AAPL": r"\baapl\b",
    "NVDA": r"\bnvda\b",
    "TSM": r"\btsm\b",
}


def public_answer(db: Session, query: str) -> tuple[str, list[dict]] | None:
    text = query.lower()
    market_question = bool(re.search(r"\b(?:markets?|stocks?|quote|closing price|share price)\b", text))
    forecast_question = bool(re.search(r"\b(?:forecasts?|scenarios?|predictions?|outlook)\b", text))
    news_question = bool(re.search(r"\b(?:news|headlines?|articles?|events?|reporting|happening|happened)\b", text))
    symbols = {symbol for symbol, pattern in MARKET_ALIASES.items() if re.search(pattern, text)}
    if not (market_question or forecast_question or news_question or symbols):
        return None

    snapshot = read_record(db, "snapshot", {})
    if not snapshot:
        return "Public data is still loading. Try again after the dashboard finishes its first refresh.", []

    terms = headline_terms(query) - QUERY_WORDS
    if market_question or (symbols and not (news_question or forecast_question)):
        for symbol, name in (("AAPL", "apple"), ("NVDA", "nvidia"), ("TSM", "tsmc")):
            if name in terms:
                symbols.add(symbol)
        markets = [market for market in snapshot["markets"] if market["symbol"] in symbols]
        if not symbols and not terms:
            markets = snapshot["markets"]
        if not markets:
            return "No matching daily close in the current snapshot. Try AAPL, NVDA, TSM, S&P 500, Nasdaq, or Nikkei.", []
        lines, sources = [], []
        for market in markets:
            prior, latest = market["observations"][-2:]
            move = (latest["close"] / prior["close"] - 1) * 100
            units = market["currency"] or "index points"
            lines.append(f'{market["name"]}: {latest["close"]:,.2f} {units} ({move:+.2f}% vs. prior close), {latest["date"]}.')
            sources.append({"title": market["name"], "url": market["source_url"]})
        return "\n".join(lines), sources

    lines, sources = [], {}
    for event in snapshot["events"]:
        article = event["articles"][0]
        event_text = " ".join([*event["regions"], *event["topics"],
                               *(f'{a["title"]} {a["excerpt"]}' for a in event["articles"])])
        if terms and not terms.intersection(headline_terms(event_text)):
            continue
        if forecast_question:
            scenario = event.get("forecast")
            if not scenario:
                continue
            lines.append(f'{scenario["event_title"]}\nScenario: {scenario["forecast"]}\n'
                         f'Assumption: {scenario["assumption"]}\nWatch for: {scenario["indicator"]}\n'
                         f'Deadline: {scenario["deadline"][:10]} UTC.')
            for evidence in scenario["evidence"]:
                sources[evidence["url"]] = evidence["title"]
        else:
            if terms:
                article = max(event["articles"], key=lambda item: len(terms.intersection(
                    headline_terms(f'{item["title"]} {item["excerpt"]}'))))
            lines.append(f'{article["title"]} — {article["publisher"]}, {article["published_at"][:10]}.')
            sources[article["url"]] = article["title"]
        if len(lines) == 3:
            break
    if not lines:
        return "No matching coverage or published scenario in the current snapshot. Try another country or topic.", []
    return "\n\n".join(lines), [{"title": title, "url": url} for url, title in sources.items()]
