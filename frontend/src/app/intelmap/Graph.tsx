"use client";

import { useMemo, useRef, useState } from "react";
import dagre from "@dagrejs/dagre";
import { Background, Controls, MiniMap, ReactFlow, Position, type Node, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { day, label, percent, type MapDetails } from "./types";

const width = 256;
const height = 98;

export default function Graph({ map, selected, onSelect }: {
  map: MapDetails; selected: string; onSelect: (id: string) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [filter, setFilter] = useState("");
  const [collapsed, setCollapsed] = useState<string[]>([]);
  const { nodes, edges } = useMemo(() => {
    const graph = new dagre.graphlib.Graph().setGraph({ rankdir: "LR", nodesep: 30, ranksep: 70 });
    graph.setDefaultEdgeLabel(() => ({}));
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    function add(id: string, title: string, subtitle: string, parent?: string, color = "#626b7b") {
      graph.setNode(id, { width, height });
      nodes.push({ id, position: { x: 0, y: 0 }, style: {
        width, height, background: "#151920", border: `1px solid ${color}`, color: "#e8e4dc",
        borderRadius: 3, textAlign: "left", padding: 10, overflow: "hidden",
      }, data: { label: <div><strong className="line-clamp-2 text-sm">{title}</strong>
        <p className="mt-1 text-xs text-paper-dim">{subtitle}</p></div> },
      sourcePosition: Position.Right, targetPosition: Position.Left });
      if (parent) {
        graph.setEdge(parent, id);
        edges.push({ id: `${parent}-${id}`, source: parent, target: id, type: "smoothstep", style: { stroke: color } });
      }
    }
    add("event", map.event.title, "Reported development", undefined, "#ff6a2e");
    const byId = new Map(map.forecasts.map(item => [item.id, item]));
    const visible = new Set<string>();
    for (const forecast of map.forecasts) {
      if (filter && forecast.verification_state !== filter) continue;
      let branch: string | null = forecast.id;
      while (branch) {
        visible.add(branch);
        branch = byId.get(branch)?.parent_id || null;
      }
    }
    for (const forecast of map.forecasts) {
      if (!visible.has(forecast.id)) continue;
      let parent = forecast.parent_id;
      let hidden = false;
      while (parent) {
        if (collapsed.includes(parent)) { hidden = true; break; }
        parent = byId.get(parent)?.parent_id || null;
      }
      if (hidden) continue;
      const { original, status, revisions, evidence } = forecast;
      const color = status === "confirmed" ? "#36c991" : status === "refuted" ? "#f76162"
        : original.scenario === "alternative" ? "#dbab58" : "#626b7b";
      add(forecast.id, original.title,
        `${percent(forecast.probability)} · ${day(forecast.deadline)} · ${original.domain} · ${label(forecast.verification_state)} · ${evidence.length} sources${revisions.length ? ` · rev. ${day(revisions[0].at)}` : ""}`,
        forecast.parent_id || "event", color);
      if (expanded && selected === forecast.id) {
        for (const item of evidence) {
          const color = item.stance === "contradicts" ? "#f76162" : "#36c991";
          add(item.id, item.article.title, `${label(item.stance)} · ${item.article.publisher}`, forecast.id, color);
        }
      }
    }
    dagre.layout(graph);
    for (const node of nodes) {
      const point = graph.node(node.id);
      node.position = { x: point.x - width / 2, y: point.y - height / 2 };
      if (node.id === selected) node.style = { ...node.style, boxShadow: "0 0 0 2px #ff6a2e" };
    }
    return { nodes, edges };
  }, [map, filter, expanded, selected, collapsed]);

  async function toggleFullscreen() {
    if (document.fullscreenElement === container.current) await document.exitFullscreen();
    else if (container.current?.requestFullscreen) await container.current.requestFullscreen();
    else setFullscreen(value => !value);
  }

  return <div ref={container} className={`bg-ink border border-line flex flex-col ${fullscreen ? "fixed inset-0 z-[100] h-screen" : "h-[540px]"}`}>
    <div className="flex shrink-0 flex-wrap items-center gap-2 border-b border-line bg-panel p-2">
      <label className="text-sm text-paper-dim">Status
        <select value={filter} onChange={event => setFilter(event.target.value)} className="ml-2 bg-ink p-1 text-paper">
          <option value="">All</option>
          {Array.from(new Set(map.forecasts.map(item => item.verification_state))).map(status =>
            <option key={status} value={status}>{label(status)}</option>)}
        </select>
      </label>
      <button type="button" className="btn btn-ghost" disabled={!map.forecasts.some(item => item.parent_id === selected)}
        onClick={() => setCollapsed(items => items.includes(selected) ? items.filter(id => id !== selected) : [...items, selected])}>
        {collapsed.includes(selected) ? "Expand branch" : "Collapse branch"}
      </button>
      <button className="btn btn-ghost" aria-pressed={expanded} onClick={() => setExpanded(value => !value)}>Evidence nodes</button>
      <button className="btn btn-ghost" onClick={() => toggleFullscreen().catch(() => setFullscreen(value => !value))}>Toggle fullscreen</button>
    </div>
    <div className="min-h-0 flex-1">
      <ReactFlow key={map.id} className="dark" nodes={nodes} edges={edges} nodesDraggable={false}
        nodesConnectable={false} fitView minZoom={0.15} maxZoom={2.5}
        onNodeClick={(_, node) => {
          const owner = map.forecasts.find(forecast => forecast.evidence.some(item => item.id === node.id));
          onSelect(owner?.id || node.id);
        }}>
        <Controls showInteractive={false} />
        <MiniMap pannable zoomable />
        <Background gap={22} color="#303641" />
      </ReactFlow>
    </div>
  </div>;
}
