"""Embed document chunks and store them in a vector collection for retrieval."""

from __future__ import annotations

from typing import Protocol

from .chunker import Chunk
from .embedder import Embedder


class Collection(Protocol):
    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None: ...


def _chunk_id(source_path: str, index: int) -> str:
    return f"{source_path}::chunk-{index}"


def store_chunks(
    chunks: list[Chunk],
    source_path: str,
    filename: str,
    embedder: Embedder,
    collection: Collection,
) -> int:
    """Embed each chunk and add it to the collection. Returns the count stored.

    Each record carries source_path, filename, and chunk index as metadata so
    retrieval can cite where an answer came from.
    """
    if not chunks:
        return 0

    ids: list[str] = []
    embeddings: list[list[float]] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for chunk in chunks:
        ids.append(_chunk_id(source_path, chunk.index))
        embeddings.append(embedder.embed(chunk.text))
        documents.append(chunk.text)
        metadatas.append(
            {
                "source_path": source_path,
                "filename": filename,
                "chunk_index": chunk.index,
            }
        )

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    return len(chunks)