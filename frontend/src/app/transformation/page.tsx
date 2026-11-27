"use client";

import { apiUrl } from "@/lib/api-url";
import { useEffect, useState } from "react";

export default function TransformationPage() {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [initiatives, setInitiatives] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(apiUrl("/api/transformation/opportunities")).then(r => r.ok ? r.json() : Promise.reject()),
      fetch(apiUrl("/api/transformation/initiatives")).then(r => r.ok ? r.json() : Promise.reject())
    ]).then(([oppsData, initsData]) => {
      setOpportunities(oppsData);
      setInitiatives(initsData);
    }).catch(() => setUnavailable(true)).finally(() => setLoading(false));
  }, []);

  if (unavailable) return <p role="alert" className="border border-alert p-4 text-alert">Transformation workspace unavailable.</p>;

  if (loading) return <p role="status" className="text-paper-dim">Loading…</p>;
  if (opportunities.length === 0 && initiatives.length === 0) return <p className="text-paper-dim">No transformation proposals or initiatives saved.</p>;

  return (
    <div className="space-y-7 animate-in fade-in duration-300">
      {/* Header */}
      <div className="border-b border-line pb-4">
        <div className="font-mono text-[10.5px] text-signal tracking-[0.1em] uppercase mb-1">
          STRATEGIC MITIGATION &amp; AI INTERVENTIONS
        </div>
        <h1 className="font-display font-bold text-2xl text-paper">
          AI Transformation Roadmap &amp; Resilience Initiatives
        </h1>
        <p className="font-sans text-[13px] text-paper-dim mt-1">
          Prioritised strategic initiatives designed to reduce single-supplier concentration risk, automate inventory buffers, and qualify secondary component sourcing.
        </p>
      </div>

      {/* Grid: Transformation Opportunities */}
      <div className="space-y-4">
        <h3 className="font-display font-bold text-base text-paper flex items-center gap-2">
          <span className="text-signal">◆</span> RECOMMENDED AI &amp; SUPPLY CHAIN OPPORTUNITIES
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {opportunities.map((opp) => (
            <div key={opp.id} className="reticle border border-line bg-panel p-6 space-y-4">
              <div className="tick-tr" />
              <div className="tick-bl" />

              <div className="flex items-center justify-between font-mono text-[10px]">
                <span className="text-signal border border-signal-dim px-2 py-0.5 uppercase tracking-wider">
                  {opp.category}
                </span>
                <span className="text-confirmed font-semibold">
                  {opp.estimated_cost_reduction == null ? "Impact unestimated" : `Demo estimate: ${opp.estimated_cost_reduction}%`}
                </span>
              </div>

              <h4 className="font-display font-bold text-base text-paper leading-snug">{opp.title}</h4>
              <p className="font-sans text-[13px] text-paper-dim leading-relaxed">{opp.description}</p>

              <div className="pt-3 border-t border-line flex justify-between font-mono text-[10.5px] text-paper-faint">
                <span>COMPLEXITY: <strong className="text-caution font-normal">{opp.implementation_complexity.toUpperCase()}</strong></span>
                <span>PRIORITY: <strong className="text-alert font-normal">{opp.priority.toUpperCase()}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Executive Implementation Initiatives */}
      <div className="border border-line bg-panel p-6 space-y-4">
        <h3 className="font-display font-bold text-base text-paper border-b border-line pb-3 flex items-center justify-between">
          <span>EXECUTIVE IMPLEMENTATION INITIATIVES</span>
          <span className="font-mono text-[10px] text-paper-faint">ROADMAP TRACKING</span>
        </h3>

        <div className="space-y-3">
          {initiatives.map((init) => (
            <div key={init.id} className="p-4 bg-ink border border-line flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-[11px]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 border text-[9.5px] tracking-wider ${
                    init.status === "Active" ? "text-confirmed border-confirmed" : "text-signal border-signal"
                  }`}>
                    {init.status.toUpperCase()}
                  </span>
                  <span className="text-paper-faint">TIMELINE: {init.timeline_months} MONTHS</span>
                </div>
                <h4 className="font-display font-semibold text-sm text-paper">{init.title}</h4>
              </div>

              <div className="text-paper-faint font-mono">
                OWNER: <strong className="text-paper font-normal">{init.owner}</strong>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
