"use client";

import { useState } from "react";

export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([
    {
      sender: "ai",
      text: "Ask about current headlines, daily market closes, published scenarios, or your saved enterprise risks.",
      evidence: [],
      related_risks: []
    }
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState("");

  const exampleQuestions = [
    "What are our highest geopolitical risks?",
    "Show me the latest world news.",
    "What was the latest close for NVDA?",
    "Show me the latest forecasts."
  ];

  async function handleSend(queryText?: string) {
    const q = queryText || inputQuery;
    if (!q || !q.trim() || loading) return;

    const newMsgs = [...messages, { sender: "user", text: q }];
    setMessages(newMsgs);
    setInputQuery("");
    setRequestError("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages([
          ...newMsgs,
          {
            sender: "ai",
            text: data.answer,
            evidence: data.evidence || [],
            sources: data.sources || [],
            related_risks: data.related_risks || [],
            related_nodes: data.related_nodes || []
          }
        ]);
      } else {
        throw new Error(`Server status ${res.status}`);
      }
    } catch {
      setRequestError("Assistant unavailable. Retry when the API is reachable.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="border-b border-line pb-4">
        <div className="font-mono text-[10.5px] text-signal tracking-[0.1em] uppercase mb-1">
          INTELLIGENCE &amp; ENTERPRISE RECORDS
        </div>
        <h1 className="font-display font-bold text-2xl text-paper">
          SIGNAL Assistant
        </h1>
        <p className="font-sans text-[13px] text-paper-dim mt-1">
          This assistant searches SIGNAL’s collected news, market closes, published scenarios, and saved workspace records.
        </p>
      </div>

      {/* Bracketed Query Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 font-mono text-[11px]">
        <span className="text-paper-faint whitespace-nowrap">PRESET QUERIES:</span>
        {exampleQuestions.map((q, idx) => (
          <button
            key={idx}
            type="button"
            disabled={loading}
            onClick={() => handleSend(q)}
            className="btn btn-ghost px-3 py-1.5 whitespace-nowrap text-[11px] cursor-pointer"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Terminal Viewport */}
      <div className="reticle border border-line bg-panel p-6 space-y-6 min-h-[460px] flex flex-col justify-between">
        <div className="tick-tr" />
        <div className="tick-bl" />

        <div className="space-y-5 overflow-y-auto max-h-[480px] pr-1">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"} space-y-2`}
            >
              <div className="font-mono text-[9.5px] text-paper-faint tracking-wider">
                {msg.sender === "user" ? "USER COMMAND" : "SIGNAL INTELLIGENCE READOUT"}
              </div>
              <div
                className={`max-w-2xl whitespace-pre-line p-4 text-[13px] leading-relaxed border ${
                  msg.sender === "user"
                    ? "bg-signal text-ink font-semibold font-mono border-signal"
                    : "bg-ink text-paper font-sans border-line"
                }`}
              >
                {msg.text}
              </div>

              {msg.sources?.length > 0 && <ul aria-label="Sources" className="max-w-2xl space-y-1 text-sm">
                {msg.sources.map((source: { url: string; title: string }) => <li key={source.url}>
                  <a href={source.url} target="_blank" rel="noreferrer" className="text-signal hover:underline">{source.title} ↗</a>
                </li>)}
              </ul>}
              {/* Supporting Evidence Citations */}
              {msg.sender === "ai" && msg.evidence && msg.evidence.length > 0 && (
                <div className="max-w-2xl w-full p-3 bg-panel-2 border border-signal-dim space-y-2 font-mono text-[10.5px]">
                  <span className="text-signal font-bold tracking-wider block">SUPPORTING EVIDENCE CITATIONS:</span>
                  {msg.evidence.map((ev: any) => (
                    <div key={ev.id} className="p-2.5 bg-ink border border-line text-paper-dim italic">
                      "{ev.snippet}" — <strong className="text-confirmed not-italic font-normal">{ev.source_name} ({ev.publication_date})</strong>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {requestError && <p role="alert" className="text-alert">{requestError}</p>}
          {loading && (
            <div className="font-mono text-[11px] text-signal animate-pulse flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-signal rounded-full animate-ping" />
              TRAVERSING GRAPH RELATIONSHIPS &amp; EVALUATING OSINT EVIDENCE...
            </div>
          )}
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend(inputQuery);
          }}
          className="mt-4 pt-4 border-t border-line flex items-center gap-3"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask a strategic intelligence question (e.g. 'What happens if SMIC becomes unavailable?')..."
            className="flex-1 bg-ink border border-line p-3 font-mono text-[11.5px] text-paper focus:outline-none focus:border-signal placeholder:text-paper-faint"
          />
          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary px-6 py-3 text-[12px] font-mono tracking-wider font-semibold disabled:opacity-50 cursor-pointer"
          >
            ASK SIGNAL
          </button>
        </form>
      </div>
    </div>
  );
}
