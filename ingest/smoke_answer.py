"""End-to-end smoke test: real Ollama + real Claude.

Run with Ollama up and ANTHROPIC_API_KEY in .env:
    python -m ingest.smoke_answer
"""

from __future__ import annotations

import chromadb
from dotenv import load_dotenv

from .claude_client import AnthropicClaudeClient
from .confidence import assess_confidence
from .embedder import OllamaEmbedder
from .generate import generate_answer
from .retriever import retrieve

CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "anchor"


def main() -> None:
    load_dotenv()

    embedder = OllamaEmbedder()
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)
    claude = AnthropicClaudeClient()

    question = "How many hours can an F-1 student work on campus?"
    print(f"Q: {question}\n")

    chunks = retrieve(question, embedder, collection, top_k=3)
    confidence = assess_confidence(chunks)
    answer = generate_answer(question, chunks, confidence, claude)

    print(f"Confident: {confidence.is_confident} (distance {confidence.best_distance})")
    print(f"\nA: {answer.text}")
    if answer.sources:
        print(f"\nSources: {', '.join(answer.sources)}")


if __name__ == "__main__":
    main()