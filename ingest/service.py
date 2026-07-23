"""Core service logic for answering a question, independent of the web layer."""

from __future__ import annotations

from dataclasses import dataclass

from .confidence import assess_confidence
from .embedder import Embedder
from .generate import ClaudeClient, generate_answer
from .retriever import QueryableCollection, retrieve


@dataclass(frozen=True)
class AskResult:
    answer: str
    is_refusal: bool
    sources: list[str]
    is_confident: bool
    best_distance: float | None


def answer_question(
    question: str,
    embedder: Embedder,
    collection: QueryableCollection,
    claude: ClaudeClient,
    top_k: int = 5,
) -> AskResult:
    """Run retrieve -> assess -> generate and return a flat result.

    Raises ValueError for an empty question so the web layer can return 400.
    """
    if not question.strip():
        raise ValueError("question must not be empty")

    chunks = retrieve(question, embedder, collection, top_k=top_k)
    confidence = assess_confidence(chunks)
    answer = generate_answer(question, chunks, confidence, claude)

    return AskResult(
        answer=answer.text,
        is_refusal=answer.is_refusal,
        sources=answer.sources,
        is_confident=confidence.is_confident,
        best_distance=confidence.best_distance,
    )