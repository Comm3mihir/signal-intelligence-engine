"use client";

import { useState, type FormEvent } from "react";
import { api, day, label, percent, type Article, type Forecast, type MapDetails } from "./types";

export function Source({ article }: { article: Article }) {
  const provenance = article.provenance ? ` · ${label(article.provenance)}` : "";
  const detail = `${article.title} · ${article.publisher} · ${article.date_is_retrieval_time ? "Retrieved " : ""}${day(article.published_at)}${provenance}`;
  return article.url && /^https?:\/\//i.test(article.url) ?
    <a target="_blank" rel="noreferrer" className="text-signal hover:underline" href={article.url}>{detail} ↗</a> :
    <span className="text-paper-dim">{detail}</span>;
}

function List({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return <section><h3 className="font-semibold text-paper">{title}</h3><ul className="list-disc pl-5">
    {items.map((item, index) => <li key={index}>{item}</li>)}
  </ul></section>;
}

export default function Assessment({ map, forecast, history, onReview }: {
  map: MapDetails; forecast?: Forecast; history: Article[]; onReview: () => void;
}) {
  const [review, setReview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [sourceMessage, setSourceMessage] = useState("");
  const [attached, setAttached] = useState<Article[]>([]);
  const [revising, setRevising] = useState(false);
  const [revisionMessage, setRevisionMessage] = useState("");
  if (!forecast) return <aside className="space-y-4 border border-line bg-panel p-5 text-sm text-paper-dim">
    <h2 className="font-display text-lg text-paper">{map.event.title}</h2>
    <p>{map.event.classification} · {map.event.date}</p>
    <List title="Actors" items={map.event.actors} />
    <List title="Regions" items={map.event.regions} />
    <List title="Reported developments" items={map.event.reported_developments} />
    <List title="Unverified claims" items={map.event.unverified_claims} />
    <ul className="space-y-2">{map.articles.map(article => <li key={article.id}><Source article={article} /></li>)}</ul>
  </aside>;

  const item = forecast;
  const initial = item.original;
  const field = "mt-1 w-full border border-line bg-ink p-2 text-paper";
  async function submitSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setSourceMessage("");
    try {
      const source = await api<Article>("sources", { method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ title: form.get("title"), publisher: form.get("publisher"),
          url: form.get("url"), excerpt: form.get("excerpt"),
          published_at: new Date(String(form.get("published_at"))).toISOString() }) });
      setAttached(previous => [...previous, source]);
      setSourceMessage("Source archived. Select it in Review outcome.");
    } catch (error) {
      setSourceMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function submitRevision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setRevisionMessage("");
    try {
      await api(`forecasts/${item.id}/bayesian-revision`, { method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ evidence_id: form.get("evidence_id"),
          likelihood_ratio: Number(form.get("likelihood_ratio")), rationale: form.get("rationale") }) });
      setRevising(false);
      onReview();
    } catch (error) {
      setRevisionMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setMessage("");
    try {
      await api(`forecasts/${item.id}/resolve`, { method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ status: form.get("status"), article_id: form.get("article_id") || null,
          reasoning: form.get("reasoning"), credibility: form.get("credibility"),
          criteria_verified: form.get("criteria_verified") === "on" }) });
      setReview(false);
      onReview();
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return <aside className="max-h-[680px] space-y-4 overflow-auto border border-line bg-panel p-5 text-sm text-paper-dim">
    <h2 className="font-display text-lg text-paper">{initial.title}</h2>
    <p className="text-caution">{percent(item.probability)} · {item.parent_id ? "Conditional on parent" : "Marginal"} · Uncalibrated model estimate</p>
    {item.joint_probability !== null && <p>Joint pathway estimate {percent(item.joint_probability)}</p>}
    <p>{label(item.verification_state)} · {initial.domain} · Deadline {day(item.deadline)} UTC</p>
    {item.last_evaluated_at && <p>Last evaluated {day(item.last_evaluated_at)} UTC</p>}
    <p>Issued {day(item.issued_at)} · {initial.provenance.provider} / {initial.provenance.model}</p>
    <section><h3 className="font-semibold text-paper">Causal reasoning</h3><p>{initial.reasoning}</p></section>
    <List title="Actors" items={map.event.actors} />
    <List title="Assumptions" items={initial.assumptions} />
    <List title="Alternative explanations" items={initial.alternatives} />
    <List title="Challenges and evidence gaps" items={initial.weaknesses} />
    <section className="space-y-1"><h3 className="font-semibold text-paper">Resolution criteria</h3>
      <p>Confirm when {initial.confirm_if}</p><p>Refute when {initial.refute_if}</p>
    </section>
    <section className="space-y-2"><h3 className="font-semibold text-paper">Evidence and precedents</h3>
      {item.evidence.map(evidence => <div key={evidence.id} className="border-t border-line pt-2">
        <p className="capitalize">{label(evidence.stance)}</p><Source article={evidence.article} /><p>{evidence.reasoning}</p>
      </div>)}
    </section>
    <section className="space-y-2"><h3 className="font-semibold text-paper">Probability history</h3>
      {item.revisions.map(revision => <div key={revision.id}><p>{percent(revision.probability)} · {day(revision.at)} · {revision.provider} / {revision.model}</p>
        <p>{revision.rationale}</p></div>)}
      <p>Original estimate {percent(initial.probability)} · {day(item.issued_at)}</p>
    </section>
    {!item.resolution && item.verification_state !== "expired" && item.evidence.length > 0 && <>
      <button className="btn btn-ghost" type="button" onClick={() => setRevising(value => !value)}>
        {revising ? "Close probability review" : "Record Bayesian revision"}
      </button>
      {revising && <form className="grid gap-2" onSubmit={submitRevision}>
        <p>Use a likelihood ratio supported by documented evidence.</p>
        <label>Evidence<select name="evidence_id" required className={field}>
          <option value="">Select linked evidence</option>
          {item.evidence.map(e => <option key={e.id} value={e.id}>{e.article.title}</option>)}
        </select></label>
        <label>Likelihood ratio<input name="likelihood_ratio" type="number" min="0.000001" max="1000000" step="any" required className={field} /></label>
        <label>Document the source and calculation<textarea name="rationale" minLength={20} maxLength={1500} required className={field} /></label>
        {revisionMessage && <p role="alert" className="text-alert">{revisionMessage}</p>}
        <button type="submit" disabled={busy} className="btn btn-primary">Save probability revision</button>
      </form>}
    </>}
    {item.resolution ? <section><h3 className="font-semibold text-paper">Analyst resolution</h3>
      <p>{item.resolution.reasoning}</p><p>{item.resolution.credibility}</p>
      {item.resolution.article && <Source article={item.resolution.article} />}
    </section> : <button className="btn btn-ghost" onClick={() => setReview(value => !value)}>{review ? "Close review" : "Review outcome"}</button>}
    {review && <details className="space-y-2">
      <summary className="cursor-pointer text-signal">Archive a primary source</summary>
      <form className="grid gap-2" onSubmit={submitSource}>
        <label>Title<input name="title" minLength={5} maxLength={350} required className={field} /></label>
        <label>Publisher<input name="publisher" minLength={2} maxLength={120} required className={field} /></label>
        <label>Original URL<input name="url" type="url" required className={field} /></label>
        <label>Publication time (your local time)<input name="published_at" type="datetime-local" required className={field} /></label>
        <label>Evidence excerpt<textarea name="excerpt" minLength={10} maxLength={650} required className={field} /></label>
        {sourceMessage && <p role="status">{sourceMessage}</p>}
        <button type="submit" disabled={busy} className="btn btn-ghost">Archive source</button>
      </form>
    </details>}
    {review && <form className="grid gap-2" onSubmit={submit}>
      <label>Outcome<select name="status" className={field}><option value="confirmed">Confirmed</option>
        <option value="refuted">Refuted</option><option value="expired_inconclusive">Expired and inconclusive</option></select></label>
      <label>Evidence article<select name="article_id" className={field}><option value="">Select archived evidence</option>
        {Array.from(new Map([...item.evidence.map(e => e.article), ...history, ...attached].map(a => [a.id, a])).values())
          .filter(article => new Date(article.published_at) >= new Date(item.issued_at))
          .map(article => <option key={article.id} value={article.id}>{article.title}</option>)}</select></label>
      <label>Explain how the evidence satisfies the criteria<textarea name="reasoning" minLength={20} maxLength={1500} required className={field} /></label>
      <label>Source credibility<textarea name="credibility" minLength={5} maxLength={600} required className={field} /></label>
      <label className="flex items-start gap-2">
        <input name="criteria_verified" type="checkbox" className="mt-1" />
        For a confirmed or refuted outcome, I verified the original criteria and timeframe.
      </label>
      {message && <p role="alert" className="text-alert">{message}</p>}
      <button type="submit" disabled={busy} className="btn btn-primary">Record resolution</button>
    </form>}
  </aside>;
}
