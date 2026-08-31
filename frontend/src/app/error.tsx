"use client";

import React, { useEffect } from "react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Next.js Error Boundary caught error:", error);
  }, [error]);

  return (
    <div className="border border-alert bg-panel p-8 max-w-xl mx-auto my-12 space-y-4 font-mono text-[11px]">
      <div className="text-alert font-bold tracking-wider uppercase">
        [ SYSTEM RUNTIME EXCEPTION CAUGHT ]
      </div>
      <p className="font-sans text-[13px] text-paper-dim leading-relaxed">
        SIGNAL recovered from an unexpected component execution error:
      </p>
      <div className="bg-ink p-3 border border-line text-alert overflow-x-auto max-h-40">
        {error?.message || String(error)}
      </div>
      <button
        onClick={() => reset()}
        className="btn btn-primary font-bold text-xs"
      >
        RESET SYSTEM VIEW
      </button>
    </div>
  );
}
