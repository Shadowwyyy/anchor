"use client";

import { useEffect, useRef, useState } from "react";
import { askQuestion, type AskResult } from "./lib/api";

type Theme = "dark" | "light";

type Message = {
  id: number;
  role: "user" | "assistant";
  question?: string;
  result?: AskResult | null;
  error?: string | null;
};

type Conversation = {
  id: number;
  title: string;
  messages: Message[];
};

const SUGGESTIONS = ["How many hours can I work on campus?", "Can I work off campus on F-1?", "What is CPT?"];

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState<Theme>("dark");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [detailed, setDetailed] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const savedTheme = (localStorage.getItem("anchor-theme") as Theme) || "dark";
    setTheme(savedTheme);
    document.documentElement.setAttribute("data-theme", savedTheme);

    const saved = localStorage.getItem("anchor-conversations");
    if (saved) {
      try {
        const parsed: Conversation[] = JSON.parse(saved);
        setConversations(parsed);
        if (parsed.length > 0) setActiveId(parsed[0].id);
      } catch {
        // ignore corrupt data
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("anchor-conversations", JSON.stringify(conversations));
  }, [conversations]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversations, loading, activeId]);

  const active = conversations.find((c) => c.id === activeId) ?? null;

  function toggleTheme() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("anchor-theme", next);
  }

  function newChat() {
    setActiveId(null);
    setInput("");
  }

  function deleteConversation(id: number) {
    setConversations((prev) => {
      const next = prev.filter((c) => c.id !== id);
      if (id === activeId) setActiveId(next[0]?.id ?? null);
      return next;
    });
  }

  function truncate(text: string, max = 40): string {
    return text.length > max ? text.slice(0, max).trimEnd() + "…" : text;
  }

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setInput("");
    setLoading(true);

    const userMsg: Message = { id: Date.now(), role: "user", question: trimmed };

    let convId = activeId;

    if (convId === null) {
      convId = Date.now();
      const conv: Conversation = {
        id: convId,
        title: truncate(trimmed),
        messages: [userMsg],
      };
      setConversations((prev) => [conv, ...prev]);
      setActiveId(convId);
    } else {
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, userMsg] } : c))
      );
    }

    try {
      const result = await askQuestion(trimmed, detailed);
      const answerMsg: Message = { id: Date.now() + 1, role: "assistant", result };
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, answerMsg] } : c))
      );
    } catch {
      const errorMsg: Message = {
        id: Date.now() + 1,
        role: "assistant",
        error: "Couldn't reach Anchor. Make sure the server is running, then try again.",
      };
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, errorMsg] } : c))
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app" data-sidebar={sidebarOpen ? "open" : "closed"}>
      <aside className="sidebar">
        <div className="sidebarTop">
          <div className="brand">
            <div className="mark" aria-hidden>
              <svg viewBox="0 0 24 24" fill="none" stroke="var(--mark-fg)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="5" r="2.4" />
                <line x1="12" y1="7.4" x2="12" y2="21" />
                <line x1="7" y1="11" x2="17" y2="11" />
                <path d="M4 14 a8 8 0 0 0 16 0" />
              </svg>
            </div>
            <span className="brandName">Anchor</span>
          </div>
        </div>

        <button className="newChatButton" onClick={newChat}>
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New chat
        </button>

        <div className="convList">
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`convItem ${c.id === activeId ? "active" : ""}`}
              onClick={() => setActiveId(c.id)}
            >
              <span className="convTitle">{c.title}</span>
              <button
                className="convDelete"
                aria-label="Delete conversation"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConversation(c.id);
                }}
              >
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        <div className="sidebarBottom">
          <button className="themeToggle" onClick={toggleTheme} aria-label="Toggle theme">
            {theme === "dark" ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
            <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
          </button>
        </div>
      </aside>

      <main className="chat">
        <div className="chatHeader">
          <button className="sidebarToggle" onClick={() => setSidebarOpen((v) => !v)} aria-label="Toggle sidebar">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <span className="chatTitle">{active ? active.title : "New chat"}</span>
        </div>

        <div className="messages">
          {!active && (
            <div className="empty">
              <div className="emptyMark" aria-hidden>
                <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="var(--mark-fg)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="5" r="2.4" />
                  <line x1="12" y1="7.4" x2="12" y2="21" />
                  <line x1="7" y1="11" x2="17" y2="11" />
                  <path d="M4 14 a8 8 0 0 0 16 0" />
                </svg>
              </div>
              <h1>Clear answers about your status in the U.S.</h1>
              <p>Ask about F-1 rules, work authorization, travel, and more — every answer comes from official guidance, with the source shown.</p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="suggestionChip" onClick={() => send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {active?.messages.map((m) => (
            <div key={m.id} className={`msgRow ${m.role}`}>
              {m.role === "user" ? (
                <div className="bubble user">{m.question}</div>
              ) : m.error ? (
                <div className="bubble assistant errorBubble">{m.error}</div>
              ) : m.result && !m.result.is_refusal ? (
                <div className="bubble assistant">
                  <p className="answerText">{m.result.answer}</p>
                  <AnswerDetails result={m.result} />
                </div>
              ) : m.result ? (
                <div className="bubble assistant refusal">
                  <span className="tag unsure">
                    <span className="dot" />
                    Not sure enough to answer
                  </span>
                  <p className="answerText">{m.result.answer}</p>
                </div>
              ) : null}
            </div>
          ))}

          {loading && (
            <div className="msgRow assistant">
              <div className="bubble assistant loadingBubble">
                <span className="spinner" />
                Searching official guidance…
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="composer">
          <form
            className="composerInner"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <button
              type="button"
              className={`modeToggle ${detailed ? "on" : ""}`}
              onClick={() => setDetailed((v) => !v)}
              aria-label="Toggle answer length"
              title={detailed ? "Detailed answers" : "Quick answers"}
            >
              {detailed ? "Detailed" : "Quick"}
            </button>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your status…"
              aria-label="Your question"
            />
            <button type="submit" disabled={loading || !input.trim()} aria-label="Send">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="5 12 12 5 19 12" />
              </svg>
            </button>
          </form>
          <div className="composerNote">
            Informational only, not legal advice — always confirm with your DSO or an attorney.
          </div>
        </div>
      </main>
    </div>
  );
}

function AnswerDetails({ result }: { result: AskResult }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="details">
      <button className="detailsToggle" onClick={() => setOpen((v) => !v)}>
        {open ? "Hide details" : "Details"}
      </button>
      {open && (
        <div className="detailsBody">
          <span className="tag grounded">
            <span className="dot" />
            Grounded in sources
          </span>
          {result.best_distance !== null && (
            <div className="meter">
              <span>Match strength</span>
              <div className="track">
                <div className="fill" style={{ width: `${matchStrength(result.best_distance)}%` }} />
              </div>
            </div>
          )}
          {result.sources.length > 0 && (
            <div className="sources">
              <div className="sourcesLabel">{result.sources.length === 1 ? "Source" : "Sources"}</div>
              <div className="chips">
                {result.sources.map((s) => (
                  <span key={s} className="chip">{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function matchStrength(distance: number): number {
  const strength = Math.round((1 - distance / 0.6) * 100);
  return Math.max(8, Math.min(100, strength));
}