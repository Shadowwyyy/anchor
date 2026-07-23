"""Throwaway smoke test: query the persisted store and print results.

Run with Ollama up:  python -m ingest.smoke_retrieve
"""

from __future__ import annotations

import chromadb

from .embedder import OllamaEmbedder
from .retriever import retrieve

CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "anchor"


def main() -> None:
    embedder = OllamaEmbedder()
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    question = "How many hours can an F-1 student work on campus?"
    print(f"Q: {question}\n")

    results = retrieve(question, embedder, collection, top_k=3)
    if not results:
        print("No results.")
        return

    for i, chunk in enumerate(results, 1):
        print(f"[{i}] {chunk.filename}#chunk-{chunk.chunk_index}  distance={chunk.distance:.4f}")
        print(f"    {chunk.text[:200]}\n")


if __name__ == "__main__":
    main()