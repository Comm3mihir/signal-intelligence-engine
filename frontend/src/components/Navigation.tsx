"use client";

import { apiUrl } from "@/lib/api-url";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

export default function Navigation() {
  const pathname = usePathname();
  const [backendStatus, setBackendStatus] = useState<"CHECKING" | "ONLINE" | "OFFLINE">("CHECKING");
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
    fetch(apiUrl("/"))
      .then((res) => (res.ok ? setBackendStatus("ONLINE") : setBackendStatus("OFFLINE")))
      .catch(() => setBackendStatus("OFFLINE"));

    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { href: "/", label: "OVERVIEW" },
    { href: "/intelmap", label: "INTELMAP" },
    { href: "/signals", label: "OSINT INGESTION" },
    { href: "/risk-matrix", label: "RISK & TRACEABILITY" },
    { href: "/transformation", label: "AI TRANSFORMATION" },
    { href: "/chat", label: "ASSISTANT" },
  ];

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-line bg-[#0A0C10]/90 backdrop-blur-md">
        <div className="max-w-[1320px] mx-auto px-4 sm:px-8 min-h-16 flex flex-wrap items-center justify-between gap-y-2 py-2">
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
          <nav className="flex order-last w-full overflow-x-auto lg:order-none lg:w-auto items-center gap-0.5">
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
            <span className={`flex items-center gap-1.5 font-mono text-[10.5px] border border-line px-2.5 py-1 ${backendStatus === "ONLINE" ? "text-confirmed" : "text-caution"}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-current" />
              API {backendStatus}
            </span>
          </div>
        </div>
      </header>

    </>
  );
}
