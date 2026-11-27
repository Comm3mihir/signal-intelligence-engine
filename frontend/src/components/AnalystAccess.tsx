"use client";

import { useState, type FormEvent } from "react";
import { saveAnalystToken } from "@/lib/analyst-api";

export default function AnalystAccess({ onChange }: { onChange: () => void }) {
  const [token, setToken] = useState("");
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveAnalystToken(token);
    setToken("");
    onChange();
  }
  return <details className="border border-line bg-panel p-3 text-sm text-paper-dim">
    <summary className="cursor-pointer text-paper">Analyst access</summary>
    <form onSubmit={submit} className="mt-2 flex flex-wrap items-end gap-2">
      <label className="min-w-56">Workspace access token
        <input type="password" autoComplete="off" value={token} onChange={event => setToken(event.target.value)}
          className="mt-1 block w-full border border-line bg-ink p-2 text-paper" />
      </label>
      <button type="submit" disabled={!token.trim()} className="btn btn-primary">Use token</button>
      <button type="button" className="btn btn-ghost" onClick={() => { saveAnalystToken(""); setToken(""); onChange(); }}>Clear token</button>
    </form>
  </details>;
}
