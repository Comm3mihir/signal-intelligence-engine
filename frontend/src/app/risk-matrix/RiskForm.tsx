"use client";

import { apiUrl } from "@/lib/api-url";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

type Signal = { id: string; title: string; source_name: string; published_date: string };
const factors = [
  ["likelihood", "Likelihood"],
  ["impact", "Impact"],
  ["exposure", "Exposure"],
  ["dependency_weight", "Dependency weight"],
];

export default function RiskForm({ onSaved }: { onSaved: (risk: any) => void }) {
  const [signals, setSignals] = useState<Signal[] | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch(apiUrl("/api/signals/"), { signal: controller.signal })
      .then(response => {
        if (!response.ok) throw new Error("Signals unavailable");
        return response.json();
      })
      .then(setSignals)
      .catch(() => {
        if (!controller.signal.aborted) setError("Could not load saved signals. Close the form and try again.");
      });
    return () => controller.abort();
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    const values = new FormData(event.currentTarget);
    const body = {
      signal_id: values.get("signal_id"), title: values.get("title"),
      description: values.get("description"),
      likelihood: Number(values.get("likelihood")), impact: Number(values.get("impact")),
      exposure: Number(values.get("exposure")), dependency_weight: Number(values.get("dependency_weight")),
      evidence_confidence: Number(values.get("evidence_confidence")) / 100,
    };
    setSaving(true);
    setError("");
    try {
      const response = await fetch(apiUrl("/api/risks/"), {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      if (!response.ok) {
        setError(response.status === 404 ? "The selected signal no longer exists." : "Risk could not be saved. Check the fields and try again.");
        return;
      }
      onSaved(await response.json());
    } catch {
      setError("Could not reach the risk API. Check the risk list before retrying.");
    } finally {
      setSaving(false);
    }
  }

  const inputClass = "mt-1 w-full border border-line bg-ink p-2 text-paper";

  return (
    <section className="border border-line bg-panel p-5" aria-labelledby="new-risk">
      <h2 id="new-risk" className="font-semibold text-paper">New risk assessment</h2>
      <p className="mt-1 text-sm text-paper-dim">Pick a saved signal as evidence and rate the potential impact on your business.</p>
      {error && <p role="alert" className="mt-2 text-alert">{error}</p>}
      {!signals && !error && <p role="status" className="mt-3 text-paper-dim">Loading saved signals…</p>}
      {signals?.length === 0 && <p className="mt-3 text-paper-dim">
        Save a signal first. <Link className="text-signal underline" href="/signals">Open OSINT Ingestion</Link>
      </p>}
      {!!signals?.length && <form onSubmit={submit} className="mt-4 grid gap-3 text-sm text-paper-dim">
        <label>
          Evidence signal
          <select name="signal_id" required defaultValue="" className={inputClass}>
            <option value="" disabled>Select a saved signal</option>
            {signals.map(signal => <option key={signal.id} value={signal.id}>{signal.title} · {signal.published_date}</option>)}
          </select>
        </label>
        <label>Risk title<input name="title" required maxLength={255} className={inputClass} /></label>
        <label>Business impact and rationale<textarea name="description" required maxLength={4000} rows={3} className={inputClass} /></label>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
          {factors.map(([name, label]) => <label key={name}>{label} (1–5)
            <input name={name} type="number" min={1} max={5} defaultValue={3} required className={inputClass} />
          </label>)}
          <label>Evidence confidence (%)
            <input name="evidence_confidence" type="number" min={10} max={100} defaultValue={50} required className={inputClass} />
          </label>
        </div>
        <button type="submit" disabled={saving} className="btn btn-primary justify-self-start">{saving ? "Saving…" : "Save risk"}</button>
      </form>}
    </section>
  );
}
