"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function Dashboard() {
  const [risks, setRisks] = useState<any[]>([]);
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [risksRes, signalsRes] = await Promise.all([
          fetch("http://localhost:8000/api/risks/").then(r => r.ok ? r.json() : []),
          fetch("http://localhost:8000/api/signals/").then(r => r.ok ? r.json() : [])
        ]);
        setRisks(risksRes);
        setSignals(signalsRes);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const criticalRisks = risks.filter(r => r.risk_level === "Critical" || r.normalized_score >= 80);

  return (
    <div className="space-y-7 animate-in fade-in duration-300">
      {/* Hero Briefing Panel */}
      <section className="reticle border border-line bg-gradient-to-br from-signal/5 via-transparent to-panel-2 bg-panel-2 p-8 sm:p-9 grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-8 items-center">
        <div className="tick-tr" />
        <div className="tick-bl" />

        <div>
          <div className="font-mono text-[11px] tracking-[0.14em] text-signal flex items-center gap-2 mb-4">
            <span className="w-[22px] h-[1px] bg-signal opacity-60" />
            STRATEGIC INTELLIGENCE OPERATING PICTURE
          </div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl lg:text-[40px] leading-[1.08] tracking-tight max-w-[640px] text-paper">
            AuraTech Electronics <span className="text-signal">Risk &amp; Transformation Radar</span>
          </h1>
          <p className="font-sans text-[14.5px] text-paper-dim leading-relaxed max-w-[560px] mt-3.5">
            Monitoring global geopolitical events, export-restriction notices, and Taiwan Strait freight corridors — mapped directly to semiconductor PCB assembly lines and revenue streams.
          </p>
          <div className="flex flex-wrap gap-3 mt-6">
            <Link href="/signals" className="btn btn-primary">
              INGEST DYNAMIC SIGNAL
            </Link>
            <Link href="/chat" className="btn btn-ghost">
              ASK AI ASSISTANT
            </Link>
          </div>
        </div>

        {/* Taiwan Strait Live Corridor Trace */}
        <div className="border-t lg:border-t-0 lg:border-l border-line pt-5 lg:pt-0 lg:pl-7 flex flex-col gap-2.5">
          <span className="font-mono text-[9.5px] text-paper-faint tracking-[0.08em]">
            TAIWAN STRAIT FREIGHT CORRIDOR — LIVE TRACE
          </span>
          <svg viewBox="0 0 260 130" fill="none" className="w-full h-auto block">
            <path d="M0 20 L40 15 L55 40 L48 70 L20 85 L0 78 Z" fill="#1B1F27" stroke="#262B33"/>
            <path d="M200 10 L260 5 L260 60 L230 75 L195 55 Z" fill="#1B1F27" stroke="#262B33"/>
            <path d="M180 90 L230 85 L260 110 L260 130 L190 130 L170 110 Z" fill="#1B1F27" stroke="#262B33"/>
            <path d="M52 55 C 100 50, 140 75, 190 60" stroke="#FF6A2E" strokeWidth="1.4" strokeDasharray="3 4" opacity="0.8"/>
            <circle r="3" fill="#FF6A2E">
              <animateMotion dur="4.5s" repeatCount="indefinite" path="M52 55 C 100 50, 140 75, 190 60" />
            </circle>
            <text x="46" y="45" fill="#9298A3" fontFamily="IBM Plex Mono" fontSize="7">CN</text>
            <text x="205" y="30" fill="#9298A3" fontFamily="IBM Plex Mono" fontSize="7">TW</text>
            <text x="192" y="105" fill="#9298A3" fontFamily="IBM Plex Mono" fontSize="7">KAOHSIUNG</text>
          </svg>
          <div className="font-mono text-[9.5px] text-paper-faint flex justify-between">
            <span>22.6°N 120.3°E</span>
            <span className="text-caution font-semibold">STATUS: DELAYED</span>
          </div>
        </div>
      </section>

      {/* KPI Strip */}
      <section className="reticle border border-line bg-panel grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <div className="tick-tr" />
        <div className="tick-bl" />

        <div className="p-[22px_26px] border-b sm:border-b-0 sm:border-r border-line">
          <div className="flex items-center justify-between font-mono text-[10px] tracking-[0.08em] text-paper-faint mb-3.5">
            <span>CRITICAL EXPOSURES</span>
            <span className="text-signal text-[12px]">⛨</span>
          </div>
          <div className="font-display font-semibold text-[32px] text-alert flex items-baseline gap-2 tabular-nums">
            {criticalRisks.length || 1} <span className="font-mono text-[12px] text-paper-dim font-normal">IMMEDIATE ACTION</span>
          </div>
          <p className="font-mono text-[10.5px] text-paper-faint mt-2.5 tracking-[0.01em]">
            SMIC 28nm MCU single-source restriction
          </p>
        </div>

        <div className="p-[22px_26px] border-b sm:border-b-0 lg:border-r border-line">
          <div className="flex items-center justify-between font-mono text-[10px] tracking-[0.08em] text-paper-faint mb-3.5">
            <span>MONITORED SIGNALS</span>
            <span className="text-signal text-[12px]">◉</span>
          </div>
          <div className="font-display font-semibold text-[32px] text-paper flex items-baseline gap-2 tabular-nums">
            {signals.length || 2} <span className="font-mono text-[12px] text-paper-dim font-normal">OSINT FEEDS</span>
          </div>
          <p className="font-mono text-[10.5px] text-paper-faint mt-2.5 tracking-[0.01em]">
            MOFCOM export &amp; Kaohsiung freight
          </p>
        </div>

        <div className="p-[22px_26px] border-b sm:border-b-0 sm:border-r border-line">
          <div className="flex items-center justify-between font-mono text-[10px] tracking-[0.08em] text-paper-faint mb-3.5">
            <span>REVENUE AT EXPOSURE</span>
            <span className="text-signal text-[12px]">▲</span>
          </div>
          <div className="font-display font-semibold text-[32px] text-paper flex items-baseline gap-2 tabular-nums">
            $450k <span className="font-mono text-[12px] text-paper-dim font-normal">/ DAY</span>
          </div>
          <p className="font-mono text-[10.5px] text-paper-faint mt-2.5 tracking-[0.01em]">
            SMT PCB assembly line stoppage
          </p>
        </div>

        <div className="p-[22px_26px]">
          <div className="flex items-center justify-between font-mono text-[10px] tracking-[0.08em] text-paper-faint mb-3.5">
            <span>AI TRANSFORMATION</span>
            <span className="text-signal text-[12px]">◆</span>
          </div>
          <div className="font-display font-semibold text-[32px] text-paper flex items-baseline gap-2 tabular-nums">
            2 <span className="font-mono text-[12px] text-paper-dim font-normal">INITIATIVES</span>
          </div>
          <p className="font-mono text-[10.5px] text-paper-faint mt-2.5 tracking-[0.01em]">
            Dual-sourcing &amp; dynamic AI buffers
          </p>
        </div>
      </section>

      {/* Main Section Grid */}
      <section className="grid grid-cols-1 lg:grid-cols-[1.35fr_1fr] gap-7 items-start mb-12">
        {/* Active Strategic Risk Assessments */}
        <div>
          <div className="flex items-center justify-between mb-3.5">
            <h2 className="font-display font-semibold text-[16px] text-paper flex items-center gap-2">
              <span className="text-signal text-[13px]">⛨</span> ACTIVE STRATEGIC RISK ASSESSMENTS
            </h2>
            <Link href="/risk-matrix" className="font-mono text-[11px] text-signal tracking-[0.02em] hover:underline">
              VIEW MATRIX →
            </Link>
          </div>

          <div className="border border-line bg-panel divide-y divide-line">
            {risks.map((risk) => {
              const isCrit = risk.risk_level === "Critical" || risk.normalized_score >= 80;
              return (
                <div
                  key={risk.id}
                  className={`p-5 relative grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-4 items-start border-l-2 ${
                    isCrit ? "border-l-alert" : "border-l-caution"
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className={`font-mono text-[9.5px] tracking-[0.06em] px-1.5 py-0.5 border ${
                        isCrit ? "text-alert border-alert" : "text-caution border-caution"
                      }`}>
                        {(risk.risk_level || "Critical").toUpperCase()} RISK — {risk.normalized_score}/100
                      </span>
                      <span className="font-mono text-[10.5px] text-paper-faint">
                        {risk.risk_category}
                      </span>
                    </div>
                    <h3 className="font-display font-semibold text-[15.5px] text-paper mb-1.5 leading-snug">
                      {risk.risk_title}
                    </h3>
                    <p className="font-sans text-[13px] text-paper-dim leading-relaxed max-w-[52ch]">
                      {risk.description}
                    </p>
                  </div>

                  <div className="sm:text-right font-mono flex-shrink-0">
                    <div className="text-[9px] text-paper-faint tracking-[0.06em] mb-1">
                      LIKELIHOOD × IMPACT
                    </div>
                    <div className="text-[14px] font-semibold text-paper">
                      {risk.likelihood}/5 × {risk.impact}/5
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent OSINT Signals */}
        <div>
          <div className="flex items-center justify-between mb-3.5">
            <h2 className="font-display font-semibold text-[16px] text-paper flex items-center gap-2">
              <span className="text-signal text-[13px]">◉</span> RECENT OSINT SIGNALS
            </h2>
            <Link href="/signals" className="font-mono text-[11px] text-signal tracking-[0.02em] hover:underline">
              TEST SURPRISE INPUT →
            </Link>
          </div>

          <div className="border border-line bg-panel divide-y divide-line">
            {signals.map((sig) => (
              <div key={sig.id} className="p-5 relative border-l-2 border-l-paper-faint">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="font-mono text-[10.5px] text-paper-faint">
                    {sig.signal_type}
                  </span>
                  <span className="font-mono text-[10px] text-paper-faint">
                    {sig.published_date}
                  </span>
                </div>
                <h3 className="font-display font-semibold text-[15.5px] text-paper mb-1.5 leading-snug">
                  {sig.title}
                </h3>
                <p className="font-sans text-[12.5px] text-paper-dim leading-relaxed mt-2">
                  {sig.summary}
                </p>
                <div className="flex items-center justify-between mt-3 pt-2 border-t border-line-soft font-mono text-[10px]">
                  <span className="text-paper-faint truncate max-w-[70%]">
                    Source: {sig.source_name}
                  </span>
                  <span className="text-confirmed flex items-center gap-1">
                    <span className="text-[6px]">●</span> TRACEABLE
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
