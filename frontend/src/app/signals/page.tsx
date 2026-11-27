"use client";

import Link from "next/link";
import { apiUrl } from "@/lib/api-url";
import React, { useState, useEffect } from "react";

export default function SignalsPage() {
  const [publicationDate, setPublicationDate] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [feedError, setFeedError] = useState(false);
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [dynamicResult, setDynamicResult] = useState<any>(null);

  // Surprise Record Test form inputs
  const [title, setTitle] = useState("");
  const [countryName, setCountryName] = useState("");
  const [signalType, setSignalType] = useState("Geopolitical Policy / Export Control");
  const [sourceName, setSourceName] = useState("");
  const [content, setContent] = useState("");

  useEffect(() => {
    fetchSignals();
    const articleId = new URLSearchParams(window.location.search).get("article");
    if (!articleId) return;
    const controller = new AbortController();
    async function loadArticle() {
      try {
        const response = await fetch(apiUrl(`/api/intelligence/articles/${encodeURIComponent(articleId!)}`),
          { signal: controller.signal });
        if (!response.ok) throw new Error("Article unavailable");
        const article = await response.json();
        setTitle(article.title.slice(0, 255));
        setCountryName(article.regions[0] || "");
        setSignalType(article.topics[0] || "News report");
        setSourceName(article.publisher);
        setSourceUrl(article.url);
        setPublicationDate(article.published_at.slice(0, 10));
        setContent(article.excerpt || article.title);
      } catch {
        if (!controller.signal.aborted) setErrorMsg("Could not load the selected article. You can enter it manually.");
      }
    }
    loadArticle();
    return () => controller.abort();
  }, []);

  async function fetchSignals() {
    try {
      const res = await fetch(apiUrl("/api/signals/"));
      if (!res.ok) throw new Error("Signal request failed");
      setSignals(await res.json());
      setFeedError(false);
    } catch {
      setFeedError(true);
    } finally {
      setLoading(false);
    }
  }

  async function handleIngestDynamic(e?: React.MouseEvent | React.FormEvent) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    setSubmitting(true);
    setErrorMsg(null);
    setDynamicResult(null);

    try {
      const res = await fetch(apiUrl("/api/signals/ingest-dynamic"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          country_name: countryName,
          signal_type: signalType,
          source_name: sourceName,
          source_url: sourceUrl || null,
          published_date: publicationDate || null,
          content
        })
      });

      if (res.ok) {
        const data = await res.json();
        setDynamicResult(data);
        fetchSignals();
      } else {
        const errText = await res.text();
        setErrorMsg(`Backend Response (${res.status}): ${errText}`);
      }
    } catch {
      setErrorMsg("Could not reach the signal API. No analysis was returned.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-7 animate-in fade-in duration-300">

      {/* Header */}
      <div className="border-b border-line pb-4">
        <div className="font-mono text-[10.5px] text-signal tracking-[0.1em] uppercase mb-1">
          INTELLIGENCE COLLECTION
        </div>
        <h1 className="font-display font-bold text-2xl text-paper">
          OSINT Intelligence Collection &amp; Dynamic Ingestion
        </h1>
        <p className="font-sans text-[13px] text-paper-dim mt-1">
          Save geopolitical developments and source details for research, forecasting, and verification.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-7 items-start">
        {/* Dynamic Ingestion Form */}
        <div className="reticle border border-line bg-panel p-6 space-y-5">
          <div className="tick-tr" />
          <div className="tick-bl" />

          <div className="flex items-center justify-between border-b border-line pb-3">
            <h3 className="font-display font-bold text-base text-paper flex items-center gap-2">
              <span className="text-signal">◉</span> Record a development
            </h3>
            <span className="font-mono text-[9.5px] text-signal border border-signal-dim px-2 py-0.5">
              RULE-BASED
            </span>
          </div>

          <form onSubmit={handleIngestDynamic} className="space-y-4 font-mono text-[11px]">
            <div>
              <label className="text-paper-faint font-semibold block mb-1">SIGNAL TITLE</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-ink border border-line p-2.5 text-paper focus:outline-none focus:border-signal"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-paper-faint font-semibold block mb-1">COUNTRY / REGION</label>
                <input
                  type="text"
                  value={countryName}
                  onChange={(e) => setCountryName(e.target.value)}
                  className="w-full bg-ink border border-line p-2.5 text-paper focus:outline-none focus:border-signal"
                  required
                />
              </div>

              <div>
                <label className="text-paper-faint font-semibold block mb-1">SIGNAL TYPE</label>
                <input
                  type="text"
                  value={signalType}
                  onChange={(e) => setSignalType(e.target.value)}
                  className="w-full bg-ink border border-line p-2.5 text-paper focus:outline-none focus:border-signal"
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-paper-faint font-semibold block mb-1">SOURCE / PUBLISHER</label>
              <input
                type="text"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                className="w-full bg-ink border border-line p-2.5 text-paper focus:outline-none focus:border-signal"
                required
              />
            </div>

            <label className="block text-paper-faint font-semibold">
              Source URL (optional)
              <input type="url" value={sourceUrl} onChange={e => setSourceUrl(e.target.value)}
                className="mt-1 w-full bg-ink border border-line p-2.5 text-paper" />
            </label>
            <label className="block text-paper-faint font-semibold">
              Publication date (optional)
              <input type="date" value={publicationDate} onChange={e => setPublicationDate(e.target.value)}
                className="mt-1 w-full bg-ink border border-line p-2.5 text-paper" />
            </label>
            <div>
              <label className="text-paper-faint font-semibold block mb-1">SIGNAL EVENT TEXT</label>
              <textarea
                rows={4}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full bg-ink border border-line p-3 text-paper focus:outline-none focus:border-signal font-sans text-[12.5px]"
                required
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="btn btn-primary w-full py-3 justify-center text-[12px] font-mono tracking-wider disabled:opacity-50 cursor-pointer"
            >
              {submitting ? "SAVING INTELLIGENCE…" : "SAVE INTELLIGENCE"}
            </button>
          </form>
        </div>

        {/* Dynamic Execution Result Output */}
        <div className="border border-line bg-panel p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-line pb-3">
            <h3 className="font-display font-bold text-base text-paper flex items-center gap-2">
              <span className="text-confirmed">●</span> INGESTION RESULT
            </h3>
            <span className="font-mono text-[10px] text-paper-faint">SOURCE RECORD</span>
          </div>

          {errorMsg && (
            <div role="alert" className="p-3.5 bg-ink border border-alert text-alert font-mono text-[11px]">
              {errorMsg}
            </div>
          )}

          {submitting && (
            <div className="min-h-[300px] flex flex-col items-center justify-center text-center p-6 space-y-3 font-mono text-signal animate-pulse">
              <div className="w-10 h-10 border border-signal flex items-center justify-center text-lg animate-spin">
                ◐
              </div>
              <h4 className="text-sm font-semibold text-paper">SAVING INTELLIGENCE</h4>
              <p className="font-sans text-[12.5px] text-paper-dim max-w-sm">
                Saving the submitted record and extracting country references.
              </p>
            </div>
          )}

          {!submitting && !dynamicResult && !errorMsg && (
            <div className="min-h-[300px] flex flex-col items-center justify-center text-center p-6 space-y-3 font-mono">
              <div className="w-10 h-10 border border-signal-dim flex items-center justify-center text-signal text-lg">
                ◉
              </div>
              <h4 className="text-sm font-semibold text-paper">READY TO INGEST</h4>
              <p className="font-sans text-[12.5px] text-paper-dim max-w-sm">
                Submit a geopolitical development with its source details to make it available for research and IntelMap.
              </p>
            </div>
          )}

          {!submitting && dynamicResult && (
            <div className="space-y-4 animate-in fade-in duration-300">
              {/* Step 1: Extracted Entities */}
              <div className="p-3.5 bg-ink border border-line space-y-1 font-mono text-[10.5px]">
                <span className="text-signal font-bold tracking-wider">Matched countries and severity</span>
                <div className="text-paper-dim flex flex-wrap gap-3">
                  <span>SEVERITY: <strong className="text-alert">{dynamicResult.extracted_entities?.perceived_severity || "High"}</strong></span>
                  <span>|</span>
                  <span>COUNTRIES: <strong className="text-paper">{(dynamicResult.extracted_entities?.mentioned_countries || []).join(", ") || countryName}</strong></span>
                </div>
              </div>

              <p className="text-sm text-confirmed">Intelligence saved.</p>
              <Link className="btn btn-primary" href={`/intelmap?signal=${encodeURIComponent(dynamicResult.signal.id)}`}>Generate IntelMap →</Link>
            </div>
          )}
        </div>
      </div>
      <section className="border border-line bg-panel p-5">
        <h2 className="font-display font-semibold text-paper">Saved signals</h2>
        {feedError && <p role="alert" className="text-alert">Saved signals unavailable.</p>}
        {loading && <p className="text-paper-dim">Loading…</p>}
        {!loading && !feedError && signals.length === 0 && <p className="text-paper-dim">No saved signals.</p>}
        <ul className="mt-3 divide-y divide-line">
          {signals.map(signal => {
            const demo = ["sig_china_export_2026", "sig_taiwan_strait_shipping"].includes(signal.id);
            const hasSource = !demo && /^https?:\/\//i.test(signal.source_url || "") &&
              !signal.source_url.startsWith("https://osint-wire.org/reports/");
            return <li key={signal.id} className="py-3">
              <strong className="text-paper">{signal.title}</strong>
              <p className="text-sm text-paper-dim">{demo ? "Demo record" : signal.source_name} · {signal.published_date}</p>
              {!demo && <Link className="mr-4 text-sm text-signal" href={`/intelmap?signal=${encodeURIComponent(signal.id)}`}>Generate IntelMap →</Link>}
              {hasSource && <a className="text-sm text-signal" href={signal.source_url} target="_blank" rel="noreferrer">Submitted source ↗</a>}
            </li>;
          })}
        </ul>
      </section>
    </div>
  );
}
