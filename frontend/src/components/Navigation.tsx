"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

export default function Navigation() {
  const pathname = usePathname();
  const [backendStatus, setBackendStatus] = useState<"ONLINE" | "OFFLINE">("ONLINE");
  const [utcTime, setUtcTime] = useState<string>("");

  useEffect(() => {
    // Live UTC Clock
    const tick = () => {
      const d = new Date();
      const hh = String(d.getUTCHours()).padStart(2, '0');
      const mm = String(d.getUTCMinutes()).padStart(2, '0');
      const ss = String(d.getUTCSeconds()).padStart(2, '0');
      setUtcTime(`${hh}:${mm}:${ss}`);
    };
    tick();
    const interval = setInterval(tick, 1000);

    // Health check
    fetch("http://localhost:8000/")
      .then((res) => (res.ok ? setBackendStatus("ONLINE") : setBackendStatus("OFFLINE")))
      .catch(() => setBackendStatus("OFFLINE"));

    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { href: "/", label: "OVERVIEW" },
    { href: "/dependency-map", label: "ENTERPRISE GRAPH" },
    { href: "/signals", label: "OSINT INGESTION" },
    { href: "/risk-matrix", label: "RISK & TRACEABILITY" },
    { href: "/transformation", label: "AI TRANSFORMATION" },
    { href: "/chat", label: "ASSISTANT" },
  ];

  const tickerItems = [
    { sev: "CRITICAL", text: "SMIC 28nm MCU export restriction — production line exposure $450k/day" },
    { sev: "MEDIUM", text: "Kaohsiung freight backlog extends to 6 days, power-IC buffer depleting" },
    { sev: "INFO", text: "MOFCOM licensing notice filed 2026-08-15, effective immediately" },
    { sev: "INFO", text: "Dual-sourcing initiative — 2 alternate MCU vendors under evaluation" },
  ];

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-line bg-[#0A0C10]/90 backdrop-blur-md">
        <div className="max-w-[1320px] mx-auto px-4 sm:px-8 h-16 flex items-center justify-between">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-3">
            <div className="w-[34px] h-[34px] border border-signal-dim flex items-center justify-center relative flex-shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-signal shadow-[0_0_8px_1px_#FF6A2E] animate-blip" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="font-display font-bold text-[16px] tracking-[0.12em] text-paper">SIGNAL</span>
              <span className="font-mono text-[9.5px] text-paper-faint tracking-[0.06em] mt-1">STRATEGIC GEOPOLITICAL INTELLIGENCE</span>
            </div>
            <span className="font-mono text-[9.5px] text-signal border border-signal-dim px-1.5 py-0.5 ml-2 tracking-[0.04em]">
              ENGINE V1.0
            </span>
          </Link>

          {/* Navigation Items */}
          <nav className="hidden md:flex items-center gap-0.5">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`font-mono text-[11.5px] tracking-[0.05em] px-3.5 py-2 relative transition-colors ${
                    isActive ? "text-paper" : "text-paper-dim hover:text-paper"
                  }`}
                >
                  {item.label}
                  {isActive && (
                    <span className="absolute left-3.5 right-3.5 bottom-0 h-[2px] bg-signal" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Status & Clock */}
          <div className="flex items-center gap-4">
            <span className="hidden sm:inline font-mono text-[11px] text-paper-dim tracking-[0.03em]">
              UTC <b className="text-paper font-medium">{utcTime || "00:00:00"}</b>
            </span>
            <span className="flex items-center gap-1.5 font-mono text-[10.5px] tracking-[0.05em] text-confirmed border border-confirmed/30 px-2.5 py-1">
              <span className="w-1.5 h-1.5 rounded-full bg-confirmed" />
              API {backendStatus}
            </span>
          </div>
        </div>
      </header>

      {/* Wire Ticker */}
      <div className="ticker">
        <div className="ticker-track">
          {[...tickerItems, ...tickerItems].map((item, idx) => (
            <span key={idx} className="font-mono text-[11px] text-paper-dim inline-flex items-center gap-2 px-5 tracking-[0.02em]">
              <span className={`font-semibold ${item.sev === "CRITICAL" ? "text-alert" : item.sev === "MEDIUM" ? "text-caution" : "text-signal"}`}>
                {item.sev}
              </span>
              <span className="text-line">/</span>
              <span>{item.text}</span>
              <span className="text-line ml-3">•</span>
            </span>
          ))}
        </div>
      </div>
    </>
  );
}
