"""Generate a grounded, cited answer from retrieved chunks, or refuse."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .confidence import Confidence
from .retriever import RetrievedChunk

DEFAULT_MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 1024

SYSTEM_PROMPT = (
    "You answer questions about US immigration status using only the provided "
    "context. Rules: answer in 2-4 plain sentences; answer strictly from the "
    "context; never add legal specifics that are not present; do not use "
    "markdown formatting or inline source tags; if the context does not cover "
    "the question, say so plainly. This is informational only, not legal advice."
)

REFUSAL_MESSAGE = (
    "I don't have a confident answer for that in my sources. Please check the "
    "official government guidance directly."
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


def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
    confidence: Confidence,
    client: ClaudeClient,
    model: str = DEFAULT_MODEL,
) -> Answer:
    """Answer the question from chunks, or refuse when confidence is low.

    When confidence.is_confident is False, returns a refusal without calling
    the client. Otherwise sends the grounded prompt to Claude and returns its
    answer with the list of source filenames used.
    """
    if not confidence.is_confident:
        return Answer(REFUSAL_MESSAGE, is_refusal=True, sources=[])

    context = _format_context(chunks)
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    reply = client.create_message(model=model, system=SYSTEM_PROMPT, prompt=prompt)

    return Answer(reply, is_refusal=False, sources=_unique_sources(chunks))