"""Split document text into overlapping token-based chunks for embedding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Tokenizer(Protocol):
    def encode(self, text: str) -> list[int]: ...
    def decode(self, tokens: list[int]) -> str: ...


@dataclass(frozen=True)
class Chunk:
    text: str
    index: int
    token_count: int


def chunk_text(
    text: str,
    tokenizer: Tokenizer,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    """Split text into overlapping chunks of at most chunk_size tokens.

    Overlap must be non-negative and smaller than chunk_size. Empty or
    whitespace-only input returns [].
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    if not text.strip():
        return []

    tokens = tokenizer.encode(text)
    if not tokens:
        return []

    step = chunk_size - overlap
    chunks: list[Chunk] = []
    start = 0
    index = 0

    while start < len(tokens):
        window = tokens[start : start + chunk_size]
        chunk_str = tokenizer.decode(window).strip()

        if chunk_str:
            chunks.append(Chunk(text=chunk_str, index=index, token_count=len(window)))
            index += 1

        if start + chunk_size >= len(tokens):
            break
        start += step

    return chunks