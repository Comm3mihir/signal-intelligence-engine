"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import AnalystAccess from "@/components/AnalystAccess";
import Assessment, { Source } from "./Assessment";
import Graph from "./Graph";
import { api, day, label, percent, type Article, type Catalog, type Forecast, type Infrastructure, type MapDetails, type Metrics, type Score } from "./types";

const views = ["Generate", "Explore", "Track", "Evaluate", "Infrastructure"] as const;
type View = typeof views[number];

function Performance({ title, score }: { title: string; score: Score }) {
  return <section className="space-y-2 border border-line bg-panel p-4">
    <h3 className="font-semibold text-paper">{title}</h3>
    <p className="text-sm text-paper-dim">{score.count} eligible resolved forecasts · {score.brier === null ? "Insufficient data for a Brier score" : `Brier ${score.brier.toFixed(3)}`}</p>
    {!!score.calibration.length && <svg width="240" height="150" viewBox="0 0 240 150" role="img" aria-label={`${title} probability calibration`}>
      <title>Mean predicted probability versus observed frequency</title>
      <path d="M35 10V120H225 M35 120L225 10" fill="none" stroke="#6b7280" strokeDasharray="4 3" />
      <text x="66" y="141" fill="#a1a8b1" fontSize="11">Predicted probability</text>
      <text x="4" y="20" fill="#a1a8b1" fontSize="10">100%</text>
      <text x="8" y="121" fill="#a1a8b1" fontSize="10">0%</text>
      <polyline fill="none" stroke="#ff6a2e" strokeWidth="2"
        points={score.calibration.map(bin => `${35 + bin.predicted * 190},${120 - bin.observed * 110}`).join(" ")} />
      {score.calibration.map(bin => <circle key={bin.predicted} cx={35 + bin.predicted * 190} cy={120 - bin.observed * 110} r="4" fill="#ff6a2e">
        <title>{percent(bin.predicted)} estimated, {percent(bin.observed)} observed across {bin.count} forecasts</title>
      </circle>)}
    </svg>}
  </section>;
}

export default function IntelMapPage() {
  const [view, setView] = useState<View>("Generate");
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [checked, setChecked] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [mapId, setMapId] = useState("");
  const [map, setMap] = useState<MapDetails | null>(null);
  const [selected, setSelected] = useState("event");
  const [tracked, setTracked] = useState<Forecast[] | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [infrastructure, setInfrastructure] = useState<Infrastructure | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [waiting, setWaiting] = useState("");
  const [signalId, setSignalId] = useState("");
  const [inputMode, setInputMode] = useState<"articles" | "url" | "manual" | "signal">("articles");
  const [access, setAccess] = useState(0);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const articleId = params.get("article");
    const initialMap = params.get("map");
    const signal = params.get("signal");
    if (signal) { setSignalId(signal); setInputMode("signal"); }
    if (articleId) setChecked([articleId]);
    if (initialMap) { setMapId(initialMap); setView("Explore"); }
  }, []);

  useEffect(() => {
    let stopped = false;
    const refresh = async () => {
      try {
        const data = await api<Catalog>("catalog");
        if (!stopped) setCatalog(data);
      } catch (reason) {
        if (!stopped) setError((reason as Error).message);
      }
    };
    refresh();
    const timer = setInterval(refresh, 8000);
    return () => { stopped = true; clearInterval(timer); };
  }, [access]);

  useEffect(() => {
    if (waiting && catalog?.maps.some(item => item.id === waiting)) {
      setMapId(waiting);
      setSelected("event");
      setView("Explore");
      setWaiting("");
    }
  }, [catalog, waiting]);

  const refreshView = useCallback(async () => {
    setError("");
    if (view === "Generate" || (view === "Explore" && !mapId)) return;
    setLoading(true);
    try {
      if (view === "Explore") setMap(await api<MapDetails>(`maps/${encodeURIComponent(mapId)}`));
      else if (view === "Track") setTracked(await api<Forecast[]>("track"));
      else if (view === "Evaluate") setMetrics(await api<Metrics>("evaluate"));
      else if (view === "Infrastructure") setInfrastructure(await api<Infrastructure>("infrastructure"));
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setLoading(false);
    }
  }, [view, mapId, access]);
  // Refresh data when the user enters a subview or selects a map.
  useEffect(() => {
    refreshView();
    if (view !== "Track" && view !== "Explore") return;
    const timer = setInterval(refreshView, 30_000);
    return () => clearInterval(timer);
  }, [refreshView, view]);

  const articles = Array.from(new Map([
    ...(catalog?.events.flatMap(event => event.articles) || []),
    ...(catalog?.history || []),
  ].map(article => [article.id, article])).values());
  const selectedArticles = articles.filter(article => checked.includes(article.id));
  const matching = articles.filter(article => `${article.title} ${article.publisher}`.toLowerCase().includes(query.toLowerCase())).slice(0, 24);

  function openMap(id: string, node = "event") {
    setMapId(id);
    setSelected(node);
    setView("Explore");
  }

  async function generate(input: Record<string, unknown>) {
    setSaving(true);
    setError("");
    try {
      const result = await api<{ map_id: string; state: string }>("generate", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input),
      });
      if (result.state === "complete") openMap(result.map_id);
      else {
        setWaiting(result.map_id);
        setCatalog(await api<Catalog>("catalog"));
      }
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setSaving(false);
    }
  }

  function submitInput(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    if (inputMode === "url") generate({ article_url: form.get("url") });
    else if (inputMode === "manual") generate({
      manual: { title: form.get("title"), description: form.get("description") },
    });
  }

  function updateAccess() {
    setError("");
    setCatalog(null);
    setMap(null);
    setTracked(null);
    setMetrics(null);
    setInfrastructure(null);
    setAccess(value => value + 1);
  }

  function pick(article: Article) {
    setChecked(previous => previous.includes(article.id)
      ? previous.filter(id => id !== article.id)
      : previous.length < 8 ? [...previous, article.id] : previous);
  }

  return <div className="space-y-5">
    <header className="border-b border-line pb-4">
      <h1 className="font-display text-3xl font-bold text-paper">IntelMap</h1>
      <p className="mt-1 text-paper-dim">Map future developments, track evidence, and evaluate past forecasts.</p>
    </header>
    <AnalystAccess onChange={updateAccess} />
    <nav aria-label="IntelMap views" className="flex flex-wrap gap-2">
      {views.map(tab => <button type="button" key={tab} aria-pressed={view === tab}
        className={`btn ${tab === view ? "btn-primary" : "btn-ghost"}`} onClick={() => setView(tab)}>{tab}</button>)}
    </nav>
    {error && <p role="alert" className="text-alert">{error}</p>}

    {view === "Generate" && <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
      <section className="space-y-3 border border-line bg-panel p-5">
        <h2 className="font-display text-xl text-paper">Forecast input</h2>
        <div aria-label="Input type" className="flex flex-wrap gap-2">
          <button type="button" aria-pressed={inputMode === "articles"} className="btn btn-ghost" onClick={() => setInputMode("articles")}>SIGNAL articles</button>
          <button type="button" aria-pressed={inputMode === "url"} className="btn btn-ghost" onClick={() => setInputMode("url")}>Article URL</button>
          <button type="button" aria-pressed={inputMode === "manual"} className="btn btn-ghost" onClick={() => setInputMode("manual")}>Manual event</button>
          {signalId && <button type="button" aria-pressed={inputMode === "signal"} className="btn btn-ghost" onClick={() => setInputMode("signal")}>Saved OSINT record</button>}
        </div>
        {inputMode === "signal" && <>
          <p className="text-sm text-paper-dim">The saved OSINT record will be cited as analyst-submitted evidence.</p>
          <button className="btn btn-primary" type="button" disabled={saving} onClick={() => generate({ signal_id: signalId })}>Generate IntelMap</button>
        </>}
        {(inputMode === "url" || inputMode === "manual") && <form className="grid gap-3 text-sm text-paper-dim" onSubmit={submitInput}>
          {inputMode === "url" ? <label>Public article URL
            <input name="url" type="url" maxLength={2048} placeholder="https://" required className="mt-1 block w-full border border-line bg-ink p-2 text-paper" />
          </label> : <>
            <p>Manual descriptions are stored as user-provided claims.</p>
            <label>Event title<input name="title" minLength={5} maxLength={200} required className="mt-1 block w-full border border-line bg-ink p-2 text-paper" /></label>
            <label>Event description<textarea name="description" rows={5} minLength={30} maxLength={8000} required className="mt-1 block w-full border border-line bg-ink p-2 text-paper" /></label>
          </>}
          <button className="btn btn-primary justify-self-start" disabled={saving} type="submit">{saving ? "Queuing…" : "Generate IntelMap"}</button>
        </form>}
        {inputMode === "articles" && <>
        <p className="text-sm text-paper-dim">Select one article or up to eight related reports.</p>
        <label className="block text-sm text-paper-dim">Search headlines or publishers
          <input value={query} onChange={event => setQuery(event.target.value)} className="mt-1 w-full border border-line bg-ink p-2 text-paper" />
        </label>
        {selectedArticles.length > 0 && <ul className="space-y-1 text-sm">
          {selectedArticles.map(article => <li key={article.id}><button type="button" onClick={() => pick(article)} className="text-signal">
            Remove · {article.title}</button></li>)}
        </ul>}
        {!catalog && <p role="status" className="text-paper-dim">Loading collected articles…</p>}
        {catalog && !matching.length && <p className="text-paper-dim">No collected articles match.</p>}
        <ul className="max-h-[36vh] divide-y divide-line overflow-auto">
          {matching.map(article => <li key={article.id} className="py-2 text-sm">
            <label className="flex gap-2 text-paper"><input type="checkbox" checked={checked.includes(article.id)}
              disabled={checked.length >= 8 && !checked.includes(article.id)} onChange={() => pick(article)} />{article.title}</label>
            <p className="pl-5 text-xs text-paper-dim">{article.publisher} · {day(article.published_at)}</p>
          </li>)}
        </ul>
        <button type="button" className="btn btn-primary" disabled={saving || !selectedArticles.length}
          onClick={() => generate({ article_ids: selectedArticles.map(article => article.id) })}>{saving ? "Queuing…" : "Generate IntelMap"}</button>
        </>}
        {waiting && <p role="status" className="text-sm text-paper-dim">Request queued. The map opens when generation finishes.</p>}
      </section>
      <div className="space-y-4">
        <section className="space-y-2 border border-line bg-panel p-4">
          <h2 className="font-semibold text-paper">Related reports</h2>
          {catalog?.events.filter(event => event.articles.length > 1).slice(0, 8).map(event =>
            <button key={event.id} className="block text-left text-sm text-signal hover:underline" type="button"
              onClick={() => { setInputMode("articles"); setChecked(event.articles.slice(0, 8).map(article => article.id)); }}>
              {event.articles[0].title} · {event.articles.length} reports
            </button>)}
          {catalog && !catalog.events.some(event => event.articles.length > 1) && <p className="text-sm text-paper-dim">No multi-source clusters currently collected.</p>}
        </section>
        {!!catalog?.jobs.length && <section className="space-y-2 border border-line bg-panel p-4">
          <h2 className="font-semibold text-paper">Generation queue</h2>
          {catalog.jobs.map(job => <div className="border-t border-line pt-2 text-sm text-paper-dim" key={job.id}>
            <p>{job.title}</p><p>{label(job.state)} · {label(job.stage)}</p>
            {job.error && <p className="text-caution">{job.error}</p>}
          </div>)}
        </section>}
      </div>
    </div>}

    {view === "Explore" && <>
      <label className="text-paper-dim">Saved map
        <select className="ml-2 max-w-full border border-line bg-panel p-2 text-paper" value={mapId}
          onChange={event => openMap(event.target.value)}>
          <option value="">Choose a map</option>
          {catalog?.maps.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}
        </select>
      </label>
      {map?.id === mapId && <div className="flex flex-wrap gap-2">
        <button type="button" className="btn btn-ghost" disabled={saving || Boolean(waiting)} onClick={() => generate({ previous_map_id: map.id })}>Regenerate as new version</button>
        {map.previous_map_id && <button type="button" className="btn btn-ghost" onClick={() => openMap(map.previous_map_id)}>Previous version</button>}
        {map.next_map_ids.map((id, index) => <button key={id} type="button" className="btn btn-ghost" onClick={() => openMap(id)}>Next version{map.next_map_ids.length > 1 ? ` ${index + 1}` : ""}</button>)}
        {waiting && <p role="status" className="text-sm text-paper-dim">New version queued.</p>}
      </div>}
      {map?.id === mapId && <div className="grid items-start gap-3 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <Graph map={map} selected={selected} onSelect={setSelected} />
        <Assessment key={selected} map={map} forecast={map.forecasts.find(item => item.id === selected)}
          history={catalog?.history || []} onReview={refreshView} />
      </div>}
      {!mapId && <p className="text-paper-dim">Choose a saved map or generate one from collected reporting.</p>}
    </>}

    {view === "Track" && <section className="space-y-3 border border-line bg-panel p-4">
      <h2 className="font-display text-xl text-paper">Forecast tracker</h2>
      <label className="text-sm text-paper-dim">Status
        <select value={statusFilter} onChange={event => setStatusFilter(event.target.value)} className="ml-2 bg-ink p-2">
          <option value="">All</option>
          {Array.from(new Set((tracked || []).map(row => row.verification_state))).map(status => <option key={status} value={status}>{label(status)}</option>)}
        </select>
      </label>
      {tracked?.length === 0 && <p className="text-paper-dim">No forecasts published yet.</p>}
      {tracked?.filter(item => !statusFilter || item.verification_state === statusFilter).map(item =>
        <article key={item.id} className="space-y-1 border-t border-line pt-3 text-sm text-paper-dim">
          <button type="button" className="text-left font-semibold text-signal hover:underline" onClick={() => openMap(item.map_id, item.id)}>{item.original.title}</button>
          <p>{percent(item.probability)} · {label(item.verification_state)} · Deadline {day(item.deadline)} · {item.evidence.length} evidence records</p>
          {item.revisions[0] && <p>Revised {day(item.revisions[0].at)} · {item.revisions[0].rationale}</p>}
          {item.evidence[0] && <Source article={item.evidence[0].article} />}
        </article>)}
    </section>}

    {view === "Evaluate" && metrics && <div className="space-y-3">
      <section className="border border-line bg-panel p-4 text-sm text-paper-dim">
        <h2 className="font-display text-xl text-paper">Forecast performance</h2>
        <p className="mt-2">{metrics.total} total · {metrics.active} active · {metrics.confirmed} confirmed · {metrics.refuted} refuted · {metrics.inconclusive} inconclusive</p>
        <p>Resolution rate {metrics.resolution_rate === null ? "unavailable" : percent(metrics.resolution_rate)} · Average horizon {metrics.average_horizon_days === null ? "unavailable" : `${metrics.average_horizon_days.toFixed(1)} days`}</p>
        <p>Historical base-rate benchmark unavailable.</p>
      </section>
      <div className="grid gap-3 md:grid-cols-2">
        <Performance title="Original forecasts" score={metrics.original} />
        <Performance title="Revisions at least 24 hours before outcome" score={metrics.revised_24h} />
        {Object.entries(metrics.by_domain).map(([key, score]) => <Performance key={key} title={`Domain · ${key}`} score={score} />)}
        {Object.entries(metrics.by_horizon).map(([key, score]) => <Performance key={key} title={`Horizon · ${key}`} score={score} />)}
        {Object.entries(metrics.by_model).map(([key, score]) => <Performance key={key} title={`Original model · ${key}`} score={score} />)}
        {Object.entries(metrics.revised_by_model).map(([key, score]) => <Performance key={key} title={`Revision model · ${key}`} score={score} />)}
      </div>
    </div>}

    {view === "Infrastructure" && infrastructure && <section className="space-y-3">
      <h2 className="font-display text-xl text-paper">AI infrastructure</h2>
      <p className="text-sm text-paper-dim">{infrastructure.pending_jobs} pending jobs · {infrastructure.failed_jobs} failed jobs</p>
      <div className="grid gap-3 lg:grid-cols-3">
        {infrastructure.providers.map(provider => <article key={provider.name} className="space-y-1 border border-line bg-panel p-4 text-sm text-paper-dim">
          <h3 className="font-semibold capitalize text-paper">{provider.name}</h3>
          <p>{provider.configured ? "Configured" : "Not configured"} · {provider.last_result ? label(provider.last_result) : "No recent result"}</p>
          <p>{provider.model || "No model"}{provider.reasoning_model !== provider.model && ` · ${provider.reasoning_model}`}</p>
          <p>{provider.requests} requests · {provider.failures} failed · {provider.cache_hits} cache hits · {provider.fallback_attempts} fallback attempts</p>
          <p>Last latency {provider.last_latency_ms === null ? "unavailable" : `${provider.last_latency_ms} ms`}</p>
          <p>Provider-reported tokens {provider.input_tokens ?? "unavailable"} in / {provider.output_tokens ?? "unavailable"} out</p>
          <p>Local budget remaining {provider.local_budget_remaining ?? "unavailable"}</p>
          <p>Provider quota and expenditure unavailable.</p>
        </article>)}
      </div>
    </section>}
    {loading && <p role="status" className="text-paper-dim">Loading…</p>}
  </div>;
}
