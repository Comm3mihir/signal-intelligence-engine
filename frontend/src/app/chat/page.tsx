"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import Markdown from "react-markdown";
import AnalystAccess from "@/components/AnalystAccess";
import { analystApi } from "@/lib/analyst-api";

type Source = { id: string; title: string; url: string | null; publisher: string; published_at: string; provenance: string };
type Message = { role: "user" | "assistant"; text: string; uncertainty?: string; sources?: Source[]; at: string };
type ThreadTitle = { id: string; title: string; updated_at: string };
type Thread = ThreadTitle & { messages: Message[] };

const examples = [
  "Summarize the latest developments in global trade policy.",
  "Compare the strategic priorities of India and Japan in the Indo-Pacific.",
  "Which indicators should I watch for in the latest IntelMap forecasts?",
];

export default function ChatPage() {
  const [thread, setThread] = useState<Thread | null>(null);
  const [history, setHistory] = useState<ThreadTitle[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [access, setAccess] = useState(0);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    analystApi<ThreadTitle[]>("/api/assistant/conversations", { signal: controller.signal })
      .then(rows => { if (!controller.signal.aborted) { setHistory(rows); setError(""); } })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message); });
    return () => controller.abort();
  }, [access]);

  useEffect(() => { end.current?.scrollIntoView({ block: "nearest" }); }, [thread, pending]);

  async function open(id: string) {
    if (busy) return;
    setBusy(true);
    setError("");
    try { setThread(await analystApi<Thread>(`/api/assistant/conversations/${encodeURIComponent(id)}`)); }
    catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); }
  }

  async function send(value: string) {
    const message = value.trim();
    if (message.length < 2 || busy) return;
    setBusy(true);
    setPending(message);
    setDraft("");
    setError("");
    try {
      const updated = await analystApi<Thread>("/api/assistant/messages", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, conversation_id: thread?.id || null }),
      });
      setThread(updated);
      setHistory(previous => [updated, ...previous.filter(item => item.id !== updated.id)].slice(0, 25));
    } catch (reason) {
      setError((reason as Error).message);
      setDraft(message);
    } finally {
      setBusy(false);
      setPending("");
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    send(draft);
  }

  function newConversation() {
    setThread(null);
    setDraft("");
    setError("");
  }

  return <div className="space-y-4">
    <header className="border-b border-line pb-4">
      <h1 className="font-display text-3xl font-semibold text-paper">Intelligence Assistant</h1>
      <p className="mt-1 text-paper-dim">Research geopolitical developments, examine sources, and discuss IntelMap forecasts.</p>
    </header>
    <AnalystAccess onChange={() => { setThread(null); setHistory([]); setAccess(value => value + 1); }} />
    <div className="grid gap-4 lg:grid-cols-[240px_minmax(0,1fr)]">
      <aside className="border border-line bg-panel p-4">
        <button type="button" disabled={busy} className="btn btn-primary w-full" onClick={newConversation}>New conversation</button>
        <h2 className="mb-2 mt-4 text-sm font-semibold text-paper">History</h2>
        {!history.length && <p className="text-sm text-paper-dim">No saved conversations.</p>}
        <ul className="max-h-64 space-y-1 overflow-auto">
          {history.map(item => <li key={item.id}>
            <button type="button" disabled={busy} aria-current={thread?.id === item.id ? "true" : undefined}
              className="block w-full truncate border border-line p-2 text-left text-sm text-paper-dim hover:text-signal"
              title={item.title} onClick={() => open(item.id)}>{item.title}</button>
          </li>)}
        </ul>
      </aside>
      <section aria-label="Conversation" className="min-w-0 border border-line bg-panel p-4">
        <div className="min-h-[20rem] max-h-[58vh] space-y-4 overflow-auto pr-1">
          {!thread && !pending && <div className="space-y-3 p-3">
            <h2 className="font-display text-lg text-paper">Start an intelligence query</h2>
            <div className="flex flex-wrap gap-2">{examples.map(example =>
              <button type="button" key={example} className="border border-line px-3 py-2 text-left text-sm text-signal hover:bg-panel-2"
                disabled={busy} onClick={() => send(example)}>{example}</button>)}</div>
          </div>}
          {thread?.messages.map((message, index) => <article key={index}
            className={`w-fit max-w-full border p-3 text-sm ${message.role === "user" ? "ml-auto border-signal-dim bg-panel-2 text-paper" : "border-line bg-ink text-paper-dim"}`}>
            <p className="mb-2 text-xs font-semibold text-paper-faint">{message.role === "user" ? "You" : "SIGNAL analysis"}</p>
            {message.role === "user" ? <p className="whitespace-pre-wrap">{message.text}</p> :
              <div className="space-y-2 break-words [&_h1]:text-paper [&_h2]:text-paper [&_li]:ml-4 [&_ol]:list-decimal [&_ul]:list-disc">
                <Markdown skipHtml allowedElements={["p", "h1", "h2", "h3", "h4", "strong", "em", "ul", "ol", "li", "blockquote", "code", "pre", "hr", "br"]} unwrapDisallowed>{message.text}</Markdown>
              </div>}
            {message.uncertainty && <p className="mt-3 text-sm text-caution"><strong>Uncertainty.</strong> {message.uncertainty}</p>}
            {!!message.sources?.length && <ul aria-label="Sources" className="mt-3 space-y-2">
              {message.sources.map(source => <li key={source.id} className="border border-line bg-panel p-2">
                {source.url && /^https?:\/\//i.test(source.url) ?
                  <a className="text-signal hover:underline" href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a> :
                  <span className="text-paper">{source.title}</span>}
                <p className="text-xs text-paper-faint">{source.publisher} · {source.published_at.slice(0,10)} · {source.provenance.replaceAll("_", " ")}</p>
              </li>)}
            </ul>}
          </article>)}
          {pending && <p className="ml-auto w-fit whitespace-pre-wrap border border-signal-dim bg-panel-2 p-3 text-sm text-paper">{pending}</p>}
          {busy && <p role="status" className="text-sm text-paper-dim">{pending ? "Retrieving evidence and preparing an answer…" : "Loading conversation…"}</p>}
          <div ref={end} />
        </div>
        {error && <p role="alert" className="mt-2 text-sm text-alert">{error}</p>}
        <form className="mt-4 flex flex-wrap items-end gap-2 border-t border-line pt-3" onSubmit={submit}>
          <label className="min-w-48 flex-1 text-sm text-paper-dim">Message
            <textarea required rows={2} maxLength={4000} value={draft} onChange={event => setDraft(event.target.value)}
              className="mt-1 block w-full border border-line bg-ink p-2 text-paper" />
          </label>
          <button type="submit" disabled={busy || draft.trim().length < 2} className="btn btn-primary">Send</button>
        </form>
      </section>
    </div>
  </div>;
}
