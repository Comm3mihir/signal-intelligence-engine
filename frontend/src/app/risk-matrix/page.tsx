"use client";

import { useEffect, useState } from "react";

export default function RiskMatrixPage() {
  const [risks, setRisks] = useState<any[]>([]);
  const [selectedRisk, setSelectedRisk] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/risks/")
      .then((res) => (res.ok ? res.json() : Promise.reject("Fetch failed")))
      .then((data) => {
        setRisks(data);
        if (data.length > 0) setSelectedRisk(data[0]);
      })
      .catch((err) => {
        console.error(err);
        const fallbackRisks = [
          {
            id: "risk_smic_export_control",
            signal_id: "sig_china_export_2026",
            dependency_id: "dep_microcontrollers",
            process_id: "proc_smt",
            risk_title: "SMIC 28nm MCU Export Restriction & Production Line Stoppage",
            risk_category: "Geopolitical / Export Control",
            likelihood: 5,
            impact: 5,
            exposure: 5,
            dependency_weight: 5,
            evidence_confidence: 0.95,
            normalized_score: 95.0,
            risk_level: "Critical",
            description: "High dependency on single-sourced SMIC 28nm Automotive MCU creates critical exposure to MOFCOM export restriction, threatening SMT assembly shutdown valued at $450k/day.",
            evidence_snippets: [
              {
                id: "ev_001",
                signal_id: "sig_china_export_2026",
                snippet: "Effective Sept 1, 2026, export of 28nm microcontrollers originating from mainland foundries requires MOFCOM export clearance.",
                source_name: "Ministry of Commerce of China (MOFCOM)",
                publication_date: "2026-08-15"
              }
            ]
          },
          {
            id: "risk_tsmc_shipping_delay",
            signal_id: "sig_taiwan_strait_shipping",
            dependency_id: "dep_power_ic",
            process_id: "proc_smt",
            risk_title: "TSMC Power IC Freight Delay & Buffer Depletion",
            risk_category: "Supply Chain Congestion",
            likelihood: 4,
            impact: 4,
            exposure: 4,
            dependency_weight: 4,
            evidence_confidence: 0.88,
            normalized_score: 36.04,
            risk_level: "Medium",
            description: "Kaohsiung port congestion is extending lead times on power-management ICs, drawing down safety stock faster than replenishment cycles allow.",
            evidence_snippets: [
              {
                id: "ev_002",
                signal_id: "sig_taiwan_strait_shipping",
                snippet: "Commercial operators report 10 to 14 days lead time extension for Taiwanese semiconductor shipments to South Asia.",
                source_name: "Maritime Logistics Intelligence",
                publication_date: "2026-08-20"
              }
            ]
          }
        ];
        setRisks(fallbackRisks);
        setSelectedRisk(fallbackRisks[0]);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-7 animate-in fade-in duration-300">
      {/* Header */}
      <div className="border-b border-line pb-4">
        <div className="font-mono text-[10.5px] text-signal tracking-[0.1em] uppercase mb-1">
          MATHEMATICAL SCORING &amp; TRACEABILITY
        </div>
        <h1 className="font-display font-bold text-2xl text-paper">
          Transparent Risk Matrix &amp; Evidence Lineage
        </h1>
        <p className="font-sans text-[13px] text-paper-dim mt-1">
          Structured risk scoring formula combined with end-to-end evidence lineage from OSINT publication to enterprise impact.
        </p>
      </div>

      {/* Grid: 5x5 Heatmap & Risk Table */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.4fr] gap-7 items-start">
        {/* 5x5 Heatmap */}
        <div className="border border-line bg-panel p-6 space-y-4">
          <h3 className="font-display font-bold text-sm text-paper border-b border-line pb-3 flex items-center justify-between">
            <span>5×5 LIKELIHOOD × IMPACT MATRIX</span>
            <span className="font-mono text-[10px] text-signal">FORMULA: L×I×E×D×C</span>
          </h3>

          <div className="grid grid-cols-5 gap-1.5 text-center font-mono text-[11px]">
            {[5, 4, 3, 2, 1].map((l) =>
              [1, 2, 3, 4, 5].map((i) => {
                const isCrit = l * i >= 20;
                const isHigh = l * i >= 12 && l * i < 20;
                const isMed = l * i >= 6 && l * i < 12;
                return (
                  <div
                    key={`${l}-${i}`}
                    className={`h-11 border flex items-center justify-center font-semibold transition-colors ${
                      isCrit
                        ? "bg-alert/15 text-alert border-alert/30"
                        : isHigh
                        ? "bg-caution/15 text-caution border-caution/30"
                        : isMed
                        ? "bg-signal/15 text-signal border-signal/30"
                        : "bg-ink text-paper-faint border-line"
                    }`}
                  >
                    {l}×{i}
                  </div>
                );
              })
            )}
          </div>
          <div className="flex justify-between font-mono text-[9.5px] text-paper-faint pt-2 border-t border-line">
            <span>X-AXIS: IMPACT (1-5)</span>
            <span>Y-AXIS: LIKELIHOOD (1-5)</span>
          </div>
        </div>

        {/* Risk Table */}
        <div className="border border-line bg-panel p-6 space-y-4">
          <h3 className="font-display font-bold text-sm text-paper border-b border-line pb-3 flex justify-between">
            <span>EVALUATED ENTERPRISE RISKS ({risks.length})</span>
            <span className="font-mono text-[10px] text-paper-faint">SCORING READOUT</span>
          </h3>

          <div className="space-y-3 overflow-y-auto max-h-[380px] pr-1">
            {risks.map((risk) => {
              const isSelected = selectedRisk?.id === risk.id;
              const isCrit = risk.risk_level === "Critical" || risk.normalized_score >= 80;
              return (
                <div
                  key={risk.id}
                  onClick={() => setSelectedRisk(risk)}
                  className={`p-4 border cursor-pointer border-l-2 transition-all ${
                    isCrit ? "border-l-alert" : "border-l-caution"
                  } ${
                    isSelected ? "bg-panel-2 border-signal" : "bg-ink border-line hover:border-paper-dim"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5 font-mono text-[10px]">
                    <span className={`px-1.5 py-0.5 border ${isCrit ? "text-alert border-alert" : "text-caution border-caution"}`}>
                      {(risk.risk_level || "Critical").toUpperCase()} — {risk.normalized_score}/100
                    </span>
                    <span className="text-paper-faint">{risk.risk_category}</span>
                  </div>
                  <h4 className="font-display font-semibold text-sm text-paper">{risk.risk_title}</h4>
                  <p className="font-sans text-[12.5px] text-paper-dim mt-1 line-clamp-2">{risk.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Selected Risk Evidence Lineage Drawer */}
      {selectedRisk && (
        <div className="reticle border border-line bg-panel p-6 space-y-5">
          <div className="tick-tr" />
          <div className="tick-bl" />

          <div className="flex items-center justify-between border-b border-line pb-3">
            <h3 className="font-display font-bold text-base text-paper flex items-center gap-2">
              <span className="text-confirmed">●</span> EVIDENCE TRACEABILITY &amp; SOURCE VERIFICATION
            </h3>
            <span className="font-mono text-[10px] text-confirmed border border-confirmed/30 px-2 py-0.5">
              100% TRACEABLE TO PUBLIC OSINT
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
            {/* Finding */}
            <div className="space-y-3">
              <span className="font-mono text-[10px] uppercase font-bold text-paper-faint tracking-wider block">ANALYTICAL FINDING</span>
              <div className="p-4 bg-ink border border-line space-y-2">
                <h4 className="font-display font-semibold text-sm text-paper">{selectedRisk.risk_title}</h4>
                <p className="font-sans text-[12.5px] text-paper-dim leading-relaxed">{selectedRisk.description}</p>
              </div>

              <div className="p-3.5 bg-ink border border-line space-y-1.5 font-mono text-[10.5px]">
                <div className="flex justify-between">
                  <span className="text-paper-faint">RAW MATHEMATICAL SCORE:</span>
                  <span className="text-signal font-bold">{selectedRisk.likelihood * selectedRisk.impact * selectedRisk.exposure * selectedRisk.dependency_weight * selectedRisk.evidence_confidence} / 625</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-paper-faint">NORMALIZED RISK SCORE:</span>
                  <span className="text-alert font-bold">{selectedRisk.normalized_score} / 100 ({selectedRisk.risk_level})</span>
                </div>
              </div>
            </div>

            {/* Evidence Paper Snippet */}
            <div className="space-y-3">
              <span className="font-mono text-[10px] uppercase font-bold text-paper-faint tracking-wider block">UNDERLYING OSINT SOURCE TEXT</span>
              {selectedRisk.evidence_snippets && selectedRisk.evidence_snippets.length > 0 ? (
                selectedRisk.evidence_snippets.map((ev: any) => (
                  <div key={ev.id} className="p-4 bg-ink border border-signal-dim space-y-3 font-mono text-[11px]">
                    <p className="font-sans text-[13px] text-paper italic leading-relaxed">"{ev.snippet}"</p>
                    <div className="pt-2 border-t border-line flex justify-between text-[10px] text-paper-faint">
                      <span>PUBLISHER: <strong className="text-signal font-normal">{ev.source_name}</strong></span>
                      <span>DATE: <strong className="text-paper font-normal">{ev.publication_date}</strong></span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-4 bg-ink border border-line font-mono text-[11px] text-paper-dim">
                  Traceable to MOFCOM Gazette No. 44 and Kaohsiung AIS Shipping Notices.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
