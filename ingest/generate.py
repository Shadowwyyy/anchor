"""Generate a grounded, cited answer from retrieved chunks, or refuse."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .confidence import Confidence
from .retriever import RetrievedChunk

DEFAULT_MODEL = "claude-haiku-4-5"
MAX_TOKENS = 1024

QUICK_PROMPT = (
    "You answer questions about US immigration status using only the provided "
    "context. Give the shortest accurate answer possible — ideally one sentence, "
    "never more than two. State only the core fact; omit elaboration, examples, "
    "and lists. Answer strictly from the context; never add legal specifics not "
    "present; if the context does not cover the question, say so plainly. "
    "Informational only, not legal advice."
)

DETAILED_PROMPT = (
    "You answer questions about US immigration status using only the provided "
    "context. Give a comprehensive answer: state the main rule, then walk through "
    "every relevant condition, exception, time limit, and procedural step found "
    "in the context. Be thorough and organize the answer clearly. Answer strictly "
    "from the context; never add legal specifics not present; if the context does "
    "not cover the question, say so plainly. Informational only, not legal advice."
)

REFUSAL_MESSAGE = (
    "I don't have a confident answer for that in my sources. Please check the "
    "official government guidance directly."
)

# Phrases that indicate Claude itself declined because the context didn't cover
# the question. Distance alone can't catch off-topic-but-similar questions
# (e.g. "rent a car on an F-1 visa"), so we also detect the model's own refusal.
MODEL_REFUSAL_SIGNALS = (
    "does not cover",
    "does not address",
    "does not contain",
    "not covered in",
    "not addressed in",
    "no information about",
    "does not provide information",
    "context does not",
    "i don't have",
    "i do not have",
)


class ClaudeClient(Protocol):
    def create_message(self, model: str, system: str, prompt: str) -> str: ...


@dataclass(frozen=True)
class Answer:
    text: str
    is_refusal: bool
    sources: list[str]


def _format_context(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(f"[Source: {chunk.filename}]\n{chunk.text}")
    return "\n\n".join(blocks)


def _unique_sources(chunks: list[RetrievedChunk]) -> list[str]:
    seen: list[str] = []
    for chunk in chunks:
        if chunk.filename not in seen:
            seen.append(chunk.filename)
    return seen


def _is_model_refusal(answer: str) -> bool:
    low = answer.lower()
    return any(sig in low for sig in MODEL_REFUSAL_SIGNALS)


def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
    confidence: Confidence,
    client: ClaudeClient,
    model: str = DEFAULT_MODEL,
    detailed: bool = False,
) -> Answer:
    """Answer the question from chunks, or refuse when confidence is low.

    Refuses in two ways: if retrieval confidence is too low (before calling the
    client), or if Claude's own answer indicates the context didn't cover the
    question. `detailed` selects a fuller prompt.
    """
    if not confidence.is_confident:
        return Answer(REFUSAL_MESSAGE, is_refusal=True, sources=[])

    system = DETAILED_PROMPT if detailed else QUICK_PROMPT
    context = _format_context(chunks)
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    reply = client.create_message(model=model, system=system, prompt=prompt)

    if _is_model_refusal(reply):
        return Answer(reply, is_refusal=True, sources=[])

    return Answer(reply, is_refusal=False, sources=_unique_sources(chunks))