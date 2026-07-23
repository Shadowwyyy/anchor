"use client";

import { useEffect, useState } from "react";
import { askQuestion, type AskResult } from "./lib/api";

const SUGGESTIONS = ["Can I work off campus on F-1?", "What is CPT?"];

type Theme = "dark" | "light";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    const saved = (localStorage.getItem("anchor-theme") as Theme) || "dark";
    setTheme(saved);
    document.documentElement.setAttribute("data-theme", saved);
  }, []);

  function toggleTheme() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("anchor-theme", next);
  }

  async function handleAsk(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const answer = await askQuestion(trimmed);
      setResult(answer);
    } catch {
      setError("Couldn't reach Anchor. Make sure the server is running, then try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <div className="wrap">
        <div className="topbar">
          <button
            className="themeToggle"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
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
          </button>
        </div>

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

        <div className="hero">
          <h1>Clear answers about your status in the U.S.</h1>
          <p>
            Ask about F-1 rules, work authorization, travel, and more. Every answer comes
            straight from official guidance, with the source shown.
          </p>
        </div>

        <form
          className="ask"
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk(question);
          }}
        >
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="How many hours can I work on campus?"
            aria-label="Your question"
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? "Asking…" : "Ask"}
          </button>
        </form>

        <div className="hint">
          Try:{" "}
          {SUGGESTIONS.map((s, i) => (
            <span key={s}>
              {i > 0 && " · "}
              <button
                type="button"
                className="suggestion"
                onClick={() => {
                  setQuestion(s);
                  handleAsk(s);
                }}
              >
                {s}
              </button>
            </span>
          ))}
        </div>

        <div className="result" aria-live="polite">
          {loading && (
            <div className="loadingCard">
              <span className="spinner" />
              Searching official guidance…
            </div>
          )}

          {error && <div className="errorCard">{error}</div>}

          {result && !result.is_refusal && (
            <div className="answerCard">
              <span className="tag grounded">
                <span className="dot" />
                Grounded in sources
              </span>
              <p className="answerText">{result.answer}</p>
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
                  <div className="sourcesLabel">
                    {result.sources.length === 1 ? "Source" : "Sources"}
                  </div>
                  <div className="chips">
                    {result.sources.map((s) => (
                      <span key={s} className="chip">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {result && result.is_refusal && (
            <div className="answerCard refusal">
              <span className="tag unsure">
                <span className="dot" />
                Not sure enough to answer
              </span>
              <p className="answerText">{result.answer}</p>
            </div>
          )}
        </div>

        <div className="disclaimer">
          Anchor is informational only and not legal advice. Immigration rules change and
          depend on your situation — always confirm with your DSO or an immigration attorney.
        </div>
      </div>
    </main>
  );
}

function matchStrength(distance: number): number {
  const strength = Math.round((1 - distance / 0.6) * 100);
  return Math.max(8, Math.min(100, strength));
}