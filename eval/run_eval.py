"""Run the eval question set against the live Anchor API and score the results.

Start the API first (uvicorn ingest.app:app --port 8000) with Ollama running,
then run:  python -m eval.run_eval
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import requests

API_URL = "http://localhost:8000/ask"
QUESTIONS = Path(__file__).parent / "questions.jsonl"


@dataclass
class Case:
    question: str
    expect_refusal: bool
    expect_source: str | None
    expect_contains: list[str]


@dataclass
class Result:
    case: Case
    is_refusal: bool
    sources: list[str]
    answer: str
    best_distance: float | None
    refusal_correct: bool
    source_correct: bool
    content_correct: bool


def load_cases(path: Path) -> list[Case]:
    cases = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        cases.append(
            Case(
                question=d["question"],
                expect_refusal=d["expect_refusal"],
                expect_source=d.get("expect_source"),
                expect_contains=d.get("expect_contains", []),
            )
        )
    return cases


def ask(question: str) -> dict:
    resp = requests.post(API_URL, json={"question": question}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def score(case: Case, response: dict) -> Result:
    is_refusal = response["is_refusal"]
    sources = response.get("sources", [])
    answer = response.get("answer", "")
    best_distance = response.get("best_distance")

    refusal_correct = is_refusal == case.expect_refusal

    if case.expect_refusal or case.expect_source is None:
        source_correct = True
    else:
        source_correct = case.expect_source in sources

    if case.expect_refusal or not case.expect_contains:
        content_correct = True
    else:
        low = answer.lower()
        content_correct = all(phrase.lower() in low for phrase in case.expect_contains)

    return Result(
        case=case,
        is_refusal=is_refusal,
        sources=sources,
        answer=answer,
        best_distance=best_distance,
        refusal_correct=refusal_correct,
        source_correct=source_correct,
        content_correct=content_correct,
    )


def main() -> int:
    cases = load_cases(QUESTIONS)
    try:
        results = [score(c, ask(c.question)) for c in cases]
    except requests.exceptions.RequestException as exc:
        print(f"Could not reach the API at {API_URL}: {exc}", file=sys.stderr)
        print("Is the server running (uvicorn ingest.app:app --port 8000)?", file=sys.stderr)
        return 1

    total = len(results)
    refusal_ok = sum(r.refusal_correct for r in results)
    source_ok = sum(r.source_correct for r in results)
    content_ok = sum(r.content_correct for r in results)

    print("=" * 70)
    for r in results:
        flags = []
        if not r.refusal_correct:
            flags.append("REFUSAL")
        if not r.source_correct:
            flags.append("SOURCE")
        if not r.content_correct:
            flags.append("CONTENT")
        status = "PASS" if not flags else "FAIL(" + ",".join(flags) + ")"
        dist = f"{r.best_distance:.3f}" if r.best_distance is not None else "  -  "
        print(f"[{status}] d={dist}  {r.case.question}")
        if flags:
            exp = "refuse" if r.case.expect_refusal else "answer"
            got = "refused" if r.is_refusal else "answered"
            print(f"        expected {exp}, got {got}; sources={r.sources}")

    print("=" * 70)
    print(f"Refusal accuracy (answer vs refuse): {refusal_ok}/{total} = {refusal_ok/total:.0%}")
    print(f"Source accuracy (right doc cited):   {source_ok}/{total} = {source_ok/total:.0%}")
    print(f"Content accuracy (expected fact):    {content_ok}/{total} = {content_ok/total:.0%}")
    overall = sum(r.refusal_correct and r.source_correct and r.content_correct for r in results)
    print(f"Fully correct (all three):           {overall}/{total} = {overall/total:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())