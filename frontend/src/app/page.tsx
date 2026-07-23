"use client";

import { useState } from "react";
import { askQuestion, type AskResult } from "./lib/api";

const SUGGESTIONS = ["Can I work off campus on F-1?", "What is CPT?"];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        <div className="brand">
          <div className="mark" aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                    <div
                      className="fill"
                      style={{ width: `${matchStrength(result.best_distance)}%` }}
                    />
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