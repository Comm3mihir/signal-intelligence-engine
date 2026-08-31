import React from "react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="border border-line bg-panel p-8 max-w-xl mx-auto my-12 space-y-4 font-mono text-[11px] text-center">
      <div className="text-signal font-bold tracking-wider uppercase">
        [ ERROR 404: RESOURCE NOT LOCATED ]
      </div>
      <p className="font-sans text-[13px] text-paper-dim leading-relaxed">
        The requested command-center address does not map to any active SIGNAL radar views.
      </p>
      <Link href="/" className="btn btn-primary font-bold text-xs inline-block">
        RETURN TO SYSTEM RADAR
      </Link>
    </div>
  );
}
