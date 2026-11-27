"use client";

import { apiUrl } from "@/lib/api-url";
import { useEffect, useState } from "react";
import Link from "next/link";

type Article = {
  id: string;
  title: string;
  publisher: string;
  url: string;
  excerpt: string;
  published_at: string;
};

type Forecast = {
  id: string;
  event_title: string;
  forecast: string;
  assumption: string;
  indicator: string;
  invalidation: string;
  issued_at: string;
  deadline: string;
  review?: { outcome: string; evidence_url: string; note: string; reviewed_at: string } | null;
  evidence: Pick<Article, "title" | "publisher" | "url">[];
};

type Market = {
  symbol: string;
  name: string;
  currency: string | null;
  source_url: string;
  observations: { date: string; close: number }[];
};

type Intelligence = {
  refreshed_at: string;
  sources: { name: string; kind: string; status: string; updated_at: string | null }[];
  markets: Market[];
  events: {
    id: string;
    articles: Article[];
    regions: string[];
    topics: string[];
    forecast: Forecast | null;
    related_events: { id: string; title: string; shared_regions: string[]; shared_topics: string[] }[];
    market_moves: {
      symbol: string;
      start: string;
      end: string;
      change_pct: number;
      relative_pp: number | null;
      source_url: string;
    }[];
  }[];
};

const signed = (value: number) => `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
const utc = (value: string) => `${value.slice(0, 16).replace("T", " ")} UTC`;

function ForecastDetails({ scenario }: { scenario: Forecast }) {
  return (
    <div className="mt-4 border-l-2 border-signal pl-4">
      <p className="mb-1 font-mono text-xs text-caution">Rule-based scenario</p>
      <p className="font-semibold text-paper">{scenario.forecast}</p>
      <dl className="mt-2 space-y-1 text-sm text-paper-dim">
        <div><dt className="inline font-semibold">Assumption. </dt><dd className="inline">{scenario.assumption}</dd></div>
        <div><dt className="inline font-semibold">What to watch. </dt><dd className="inline">{scenario.indicator}</dd></div>
        <div><dt className="inline font-semibold">Invalidation. </dt><dd className="inline">{scenario.invalidation}</dd></div>
      </dl>
      <p className="mt-2 font-mono text-xs text-paper-faint">
        Issued {utc(scenario.issued_at)} · Deadline {utc(scenario.deadline)}
      </p>
      {scenario.review && (
        <div className="mt-2 text-sm text-paper-dim">
          <p>Review · {scenario.review.outcome} · {utc(scenario.review.reviewed_at)}</p>
          <p>{scenario.review.note}</p>
          <a href={scenario.review.evidence_url} className="text-signal hover:underline" target="_blank" rel="noreferrer">Review evidence ↗</a>
        </div>
      )}
      <ul className="mt-2 space-y-1 text-xs text-signal">
        {scenario.evidence.map(article => (
          <li key={article.url}>
            <a href={article.url} target="_blank" rel="noreferrer" className="hover:underline">
              {article.publisher} · {article.title}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<Intelligence | null>(null);
  const [forecasts, setForecasts] = useState<Forecast[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [archiveError, setArchiveError] = useState("");
  const [topic, setTopic] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const res = await fetch(apiUrl("/api/intelligence/"), { signal: controller.signal, cache: "no-store" });
        if (!res.ok) throw new Error("Intelligence request failed");
        setData(await res.json());
        setError("");
      } catch {
        if (!controller.signal.aborted) setError("Could not reach the intelligence API. The page will retry automatically.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, 60_000);
    return () => { controller.abort(); clearInterval(interval); };
  }, []);

  async function loadArchive() {
    setArchiveError("");
    try {
      const res = await fetch(apiUrl("/api/intelligence/forecasts"), { cache: "no-store" });
      if (!res.ok) throw new Error("Forecast archive request failed");
      setForecasts(await res.json());
    } catch {
      setArchiveError("Forecast archive unavailable.");
    }
  }

  const topics = Array.from(new Set(data?.events.flatMap(event => event.topics))).sort();
  const events = data?.events.filter(event => !topic || event.topics.includes(topic)) ?? [];

  return (
    <div className="space-y-8">
      <header className="border border-line bg-panel-2 p-6 sm:p-8">
        <h1 className="font-display text-3xl font-bold text-paper">World Intelligence</h1>
        <p className="mt-2 text-paper-dim">International reporting, daily market closes, and evidence-linked 14-day scenarios.</p>
        <Link href="/signals" className="mt-4 inline-block text-sm text-signal hover:underline">Open enterprise signal workspace →</Link>
      </header>

      {loading && <p role="status" className="text-paper-dim">Fetching publishers and market sources…</p>}
      {error && <p role="alert" className="border border-alert p-4 text-alert">{error}{data && " Showing the last loaded snapshot."}</p>}

      {data && <>
        <section aria-label="Source status" className="border border-line bg-panel p-4">
          <p className="font-mono text-xs text-paper-dim">Last checked {utc(data.refreshed_at)}</p>
          <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-xs">
            {data.sources.map(source => (
              <li key={source.name} className={source.status === "ok" ? "text-confirmed" : "text-caution"}>
                {source.name} · {source.status === "ok" ? "Available" : source.status}
                {source.updated_at && source.status === "stale" && ` · ${utc(source.updated_at)}`}
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="markets-title">
          <h2 id="markets-title" className="mb-3 font-display text-xl font-semibold text-paper">Market closes</h2>
          {data.markets.length === 0 && <p className="text-paper-dim">Market data unavailable.</p>}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
            {data.markets.map(market => {
              const latest = market.observations[market.observations.length - 1];
              const prior = market.observations[market.observations.length - 2];
              const change = (latest.close / prior.close - 1) * 100;
              return (
                <div key={market.symbol} className="border border-line bg-panel p-4">
                  <a href={market.source_url} target="_blank" rel="noreferrer" className="text-sm text-paper hover:text-signal">{market.name} ↗</a>
                  <p className="mt-2 font-mono text-lg text-paper">
                    {latest.close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    {market.currency && <span className="ml-1 text-xs text-paper-faint">{market.currency}</span>}
                  </p>
                  <p className={change < 0 ? "text-sm text-alert" : "text-sm text-confirmed"}>{signed(change)}%</p>
                  <p className="mt-1 font-mono text-xs text-paper-faint">{latest.date}</p>
                </div>
              );
            })}
          </div>
        </section>

        <section aria-labelledby="events-title">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <h2 id="events-title" className="font-display text-xl font-semibold text-paper">International events</h2>
            <label className="text-sm text-paper-dim">
              Topic
              <select value={topic} onChange={event => setTopic(event.target.value)} className="ml-2 border border-line bg-panel p-2 text-paper">
                <option value="">All topics</option>
                {topics.map(value => <option key={value}>{value}</option>)}
              </select>
            </label>
          </div>
          {events.length === 0 && <p className="text-paper-dim">No recent articles available for this view.</p>}
          <div className="space-y-3">
            {events.map(event => {
              const lead = event.articles[0];
              const publishers = new Set(event.articles.map(article => article.publisher)).size;
              return (
                <article key={event.id} id={`event-${event.id}`} className="scroll-mt-28 border border-line bg-panel p-5">
                  <p className="mb-2 font-mono text-xs text-paper-faint">
                    {[utc(lead.published_at), ...event.regions, ...event.topics].join(" · ")}
                  </p>
                  <h3 className="font-display text-lg font-semibold text-paper">
                    <a href={lead.url} target="_blank" rel="noreferrer" className="hover:text-signal">{lead.title} ↗</a>
                  </h3>
                  {lead.excerpt && <p className="mt-2 text-sm text-paper-dim">{lead.excerpt}</p>}
                  <p className="mt-2 text-xs text-paper-dim">{lead.publisher} · {event.articles.length} {event.articles.length === 1 ? "report" : "reports"} from {publishers} {publishers === 1 ? "publisher" : "publishers"}</p>
                  <div className="mt-2 flex flex-wrap gap-4 text-xs text-signal">
                    <Link href={`/intelmap?article=${lead.id}`} className="hover:underline">Generate IntelMap →</Link>
                    <Link href={`/signals?article=${lead.id}`} className="hover:underline">Analyze enterprise exposure →</Link>
                  </div>
                  {(event.articles.length > 1 || event.market_moves.length > 0 || event.forecast || event.related_events.length > 0) && (
                    <details className="mt-3 border-t border-line pt-3 text-sm text-paper-dim">
                      <summary className="cursor-pointer text-signal">Event evidence and analysis</summary>
                      <ul className="mt-2 space-y-1">
                        {event.articles.slice(1).map(article => (
                          <li key={article.id}>
                            <a href={article.url} target="_blank" rel="noreferrer" className="text-signal hover:underline">
                              {article.publisher} · {article.title}
                            </a>
                          </li>
                        ))}
                      </ul>
                      {event.related_events.length > 0 && <>
                        <h4 className="mt-4 font-semibold text-paper">Related coverage</h4>
                        <ul className="mt-1 space-y-1">
                          {event.related_events.map(related => (
                            <li key={related.id}>
                              <a href={`#event-${related.id}`} className="text-signal hover:underline">{related.title}</a>
                              {" · "}{[...related.shared_regions, ...related.shared_topics].join(", ")}
                            </li>
                          ))}
                        </ul>
                      </>}
                      {event.market_moves.length > 0 && <>
                        <h4 className="mt-4 font-semibold text-paper">Market moves around first report</h4>
                        <ul className="mt-1 space-y-1">
                          {event.market_moves.map(move => (
                            <li key={move.symbol}>
                              <a href={move.source_url} target="_blank" rel="noreferrer" className="text-signal hover:underline">{move.symbol}</a>
                              {" "}{signed(move.change_pct)}% · {move.start} to {move.end}
                              {move.relative_pp !== null && ` · ${signed(move.relative_pp)} pp vs. S&P 500`}
                            </li>
                          ))}
                        </ul>
                        <p className="mt-1 text-xs text-paper-faint">The window runs from the last close before publication day to the first close after it. The figures measure timing and performance.</p>
                      </>}
                      {event.forecast && <ForecastDetails scenario={event.forecast} />}
                    </details>
                  )}
                </article>
              );
            })}
          </div>
        </section>
      </>}

      <section aria-labelledby="archive-title">
        <h2 id="archive-title" className="font-display text-xl font-semibold text-paper">Forecast archive</h2>
        <button type="button" onClick={loadArchive} className="btn btn-ghost mt-3">Load saved forecasts</button>
        {archiveError && <p role="alert" className="mt-3 text-alert">{archiveError}</p>}
        {forecasts?.length === 0 && <p className="mt-3 text-paper-dim">No saved forecasts yet.</p>}
        {!!forecasts?.length && <p className="mt-3 text-sm text-paper-dim">
          {forecasts.filter(item => item.review?.outcome === "confirmed").length} confirmed · {forecasts.filter(item => item.review?.outcome === "refuted").length} refuted · {forecasts.filter(item => item.review?.outcome === "inconclusive").length} inconclusive · {forecasts.filter(item => !item.review).length} awaiting review
        </p>}
        {forecasts?.map(scenario => (
          <details key={scenario.id} className="mt-3 border border-line bg-panel p-4">
            <summary className="cursor-pointer text-paper">{scenario.event_title}</summary>
            <p className="mt-2 font-mono text-xs text-paper-faint">Forecast ID {scenario.id}</p>
            <ForecastDetails scenario={scenario} />
          </details>
        ))}
      </section>
    </div>
  );
}
