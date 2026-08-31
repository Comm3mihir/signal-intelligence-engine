"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function DependencyMapPage() {
  const [graph, setGraph] = useState<any>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [filterType, setFilterType] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/organisations/org_auratech/graph")
      .then((res) => (res.ok ? res.json() : Promise.reject("Fetch failed")))
      .then((data) => {
        setGraph(data);
        if (data.nodes && data.nodes.length > 0) {
          setSelectedNode(data.nodes[0]);
        }
      })
      .catch((err) => {
        console.error(err);
        // Resilient fallback topology
        const fallbackGraph = {
          nodes: [
            { id: "org_auratech", label: "AuraTech Electronics Pvt Ltd", type: "Organisation", data: { industry: "Electronics & Semiconductor Assembly", headquarters: "Bengaluru, India" } },
            { id: "proc_smt", label: "Automated SMT PCB Assembly", type: "Process", data: { criticality: "Mission Critical", revenue_impact: 450000.0 } },
            { id: "dep_microcontrollers", label: "28nm Automotive Microcontrollers (MCU)", type: "Component", data: { dependency_type: "Single Source", lead_time_weeks: 16 } },
            { id: "sup_smic", label: "SMIC Microelectronics", type: "Supplier", data: { tier: "Tier 1", risk_level: "High" } },
            { id: "cnt_cn", label: "China", type: "Country", data: { region: "East Asia", risk_rating: "High" } },
            { id: "risk_smic_export_control", label: "SMIC 28nm MCU Export Restriction & Production Line Stoppage", type: "Risk", data: { score: 95.0, level: "Critical" } },
            { id: "sig_china_export_2026", label: "China MOFCOM Export Control Policy on Dual-Use Legacy Chips", type: "Signal", data: { signal_type: "Geopolitical Policy / Export Control", published_date: "2026-08-15" } }
          ],
          edges: [
            { id: "e1", source: "org_auratech", target: "proc_smt", relationship: "OWNS_PROCESS" },
            { id: "e2", source: "dep_microcontrollers", target: "proc_smt", relationship: "REQUIRED_BY" },
            { id: "e3", source: "sup_smic", target: "dep_microcontrollers", relationship: "SUPPLIES" },
            { id: "e4", source: "sup_smic", target: "cnt_cn", relationship: "LOCATED_IN" },
            { id: "e5", source: "sig_china_export_2026", target: "risk_smic_export_control", relationship: "TRIGGERS_RISK" },
            { id: "e6", source: "risk_smic_export_control", target: "dep_microcontrollers", relationship: "THREATENS_COMPONENT" }
          ]
        };
        setGraph(fallbackGraph);
        setSelectedNode(fallbackGraph.nodes[0]);
      })
      .finally(() => setLoading(false));
  }, []);

  const filteredNodes = filterType === "ALL"
    ? graph.nodes
    : graph.nodes.filter((n: any) => n.type === filterType);

  const getNodeTagColor = (type: string) => {
    switch (type) {
      case "Risk": return "text-alert border-alert";
      case "Supplier": return "text-signal border-signal";
      case "Process": return "text-caution border-caution";
      case "Component": return "text-paper border-paper-faint";
      case "Country": return "text-confirmed border-confirmed";
      default: return "text-paper-dim border-line";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-line pb-4">
        <div>
          <div className="font-mono text-[10.5px] text-signal tracking-[0.1em] uppercase mb-1">
            NETWORK TOPOLOGY &amp; CORRIDOR MATRIX
          </div>
          <h1 className="font-display font-bold text-2xl text-paper">
            Enterprise Dependency &amp; Exposure Graph
          </h1>
          <p className="font-sans text-[13px] text-paper-dim mt-1">
            Bi-directional graph traversal connecting suppliers, countries, components, PCB assembly processes, and geopolitical risks.
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
          {["ALL", "Supplier", "Component", "Process", "Risk", "Country"].map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setFilterType(type)}
              className={`font-mono text-[11px] tracking-[0.04em] px-3 py-1.5 border transition-all cursor-pointer ${
                filterType === type
                  ? "bg-signal text-ink font-semibold border-signal"
                  : "bg-panel text-paper-dim border-line hover:text-paper hover:border-paper-dim"
              }`}
            >
              {type.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.5fr_1fr] gap-7 items-start">
        {/* Topology Nodes Grid Viewport */}
        <div className="border border-line bg-panel p-6 min-h-[480px] flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-line pb-3 mb-4 font-mono text-[10.5px] text-paper-faint">
            <span>GRAPH READOUT: {filteredNodes.length} NODES, {graph.edges.length} EDGES</span>
            <span className="text-confirmed flex items-center gap-1">
              <span className="text-[6px]">●</span> BI-DIRECTIONAL TRAVERSAL
            </span>
          </div>

          {/* Interactive Topology Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 overflow-y-auto max-h-[420px] pr-1">
            {filteredNodes.map((node: any) => {
              const isSelected = selectedNode?.id === node.id;
              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`p-3.5 border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-panel-2 border-signal"
                      : "bg-ink border-line hover:border-paper-dim"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`font-mono text-[9px] uppercase tracking-[0.06em] px-1.5 py-0.5 border ${getNodeTagColor(node.type)}`}>
                      {node.type}
                    </span>
                    <span className="font-mono text-[9px] text-paper-faint">ID:{node.id.slice(0,6)}</span>
                  </div>
                  <h4 className="font-display font-semibold text-[13.5px] text-paper line-clamp-2 leading-snug">
                    {node.label}
                  </h4>
                </div>
              );
            })}
          </div>

          <div className="mt-4 pt-3 border-t border-line font-mono text-[10px] text-paper-faint flex justify-between">
            <span>Select any node to inspect operational dependencies and risk properties.</span>
            <span className="text-signal">SIGNAL ENGINE</span>
          </div>
        </div>

        {/* Node Inspector Drawer */}
        <div className="reticle border border-line bg-panel p-6 space-y-5">
          <div className="tick-tr" />
          <div className="tick-bl" />

          <div className="border-b border-line pb-3">
            <div className="font-mono text-[10px] uppercase text-signal tracking-[0.1em]">NODE INSPECTOR</div>
            <h3 className="font-display font-bold text-lg text-paper mt-1">{selectedNode?.label || "Select a node"}</h3>
            <span className="font-mono text-[10.5px] text-paper-faint">ID: {selectedNode?.id}</span>
          </div>

          {selectedNode && (
            <div className="space-y-4 font-mono text-[11px]">
              <div>
                <span className="text-[10px] uppercase font-bold text-paper-faint block mb-1">NODE TYPE</span>
                <span className={`inline-block font-mono text-[9.5px] tracking-[0.06em] px-2 py-0.5 border ${getNodeTagColor(selectedNode.type)}`}>
                  {selectedNode.type}
                </span>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-paper-faint block mb-1.5">METADATA &amp; PROPERTIES</span>
                <div className="bg-ink p-3 border border-line space-y-2">
                  {Object.entries(selectedNode.data || {}).map(([key, val]: [string, any]) => (
                    <div key={key} className="flex justify-between border-b border-line-soft pb-1 text-[11px]">
                      <span className="text-paper-faint capitalize">{key.replace('_', ' ')}:</span>
                      <span className="text-paper font-semibold">{String(val)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-paper-faint block mb-1.5">CONNECTED EDGES ({graph.edges.filter((e: any) => e.source === selectedNode.id || e.target === selectedNode.id).length})</span>
                <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
                  {graph.edges
                    .filter((e: any) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((e: any) => {
                      const isSource = e.source === selectedNode.id;
                      const otherId = isSource ? e.target : e.source;
                      const otherNode = graph.nodes.find((n: any) => n.id === otherId);
                      return (
                        <div key={e.id} className="p-2 bg-ink border border-line flex items-center justify-between text-[10.5px]">
                          <span className="text-paper font-sans">{otherNode?.label || otherId}</span>
                          <span className="font-mono text-[9px] text-signal border border-signal-dim px-1.5 py-0.5">
                            {e.relationship}
                          </span>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
