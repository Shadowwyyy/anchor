"""Retrieve the most relevant stored chunks for a query."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .embedder import Embedder


class QueryableCollection(Protocol):
    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int,
    ) -> dict: ...


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source_path: str
    filename: str
    chunk_index: int
    distance: float


def retrieve(
    query: str,
    embedder: Embedder,
    collection: QueryableCollection,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Return up to top_k chunks most similar to the query, nearest first.

    Each result carries its source metadata and a distance score (lower is
    closer). Empty or whitespace-only queries return []. top_k must be positive.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if not query.strip():
        return []

    query_embedding = embedder.embed(query)
    result = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    documents = _first(result, "documents")
    metadatas = _first(result, "metadatas")
    distances = _first(result, "distances")

    retrieved: list[RetrievedChunk] = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        retrieved.append(
            RetrievedChunk(
                text=text,
                source_path=metadata["source_path"],
                filename=metadata["filename"],
                chunk_index=metadata["chunk_index"],
                distance=distance,
            )
        )
    return retrieved


def _first(result: dict, key: str) -> list:
    """Chroma nests each field one list deep per query; we send one query."""
    values = result.get(key)
    if not values:
        return []
    return values[0]