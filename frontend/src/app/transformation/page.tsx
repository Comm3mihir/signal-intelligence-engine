"use client";

import { useEffect, useState } from "react";

export default function TransformationPage() {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [initiatives, setInitiatives] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("http://localhost:8000/api/transformation/opportunities").then(r => r.ok ? r.json() : Promise.reject()),
      fetch("http://localhost:8000/api/transformation/initiatives").then(r => r.ok ? r.json() : Promise.reject())
    ]).then(([oppsData, initsData]) => {
      setOpportunities(oppsData);
      setInitiatives(initsData);
    }).catch((err) => {
      console.error(err);
      const fallbackOpps = [
        {
          id: "trans_dual_sourcing",
          risk_id: "risk_smic_export_control",
          title: "Qualcomm / STMicroelectronics Automotive MCU Dual-Sourcing Qualification",
          category: "Supplier Diversification & Nearshoring",
          description: "Qualify European or US secondary semiconductor foundries for 28nm MCUs to eliminate single-region concentration risk in East Asia.",
          estimated_cost_reduction: 22.5,
          implementation_complexity: "High",
          priority: "Immediate"
        },
        {
          id: "trans_ai_buffer_opt",
          risk_id: "risk_tsmc_shipping_delay",
          title: "AI Dynamic Safety Buffer & Predictive Freight Allocation",
          category: "AI Supply Chain Intelligence",
          description: "Deploy predictive inventory models to automatically adjust order lead times and safety stock levels 4 weeks in advance upon Kaohsiung port congestion alerts.",
          estimated_cost_reduction: 14.0,
          implementation_complexity: "Medium",
          priority: "High"
        }
      ];
      const fallbackInits = [
        {
          id: "init_001",
          opportunity_id: "trans_dual_sourcing",
          title: "Initiate Secondary MCU Validation in Bengaluru R&D Lab",
          status: "Active",
          owner: "Head of Hardware Engineering",
          timeline_months: 3
        },
        {
          id: "init_002",
          opportunity_id: "trans_ai_buffer_opt",
          title: "Integrate AI Maritime Freight Tracking API into SAP ERP",
          status: "Planning",
          owner: "VP of Supply Chain Operations",
          timeline_months: 2
        }
      ];
      setOpportunities(fallbackOpps);
      setInitiatives(fallbackInits);
    }).finally(() => setLoading(false));
  }, []);

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
                  -{opp.estimated_cost_reduction}% EXPOSURE
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
