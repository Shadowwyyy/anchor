"""Ingest every document in a directory into a persistent Chroma collection.

Run from the project root with the venv active:
    python -m ingest.main
"""

from __future__ import annotations

import sys
from pathlib import Path

import chromadb
import tiktoken

from .chunker import chunk_text
from .embedder import OllamaEmbedder
from .loader import (
    PDF_EXTENSION,
    TEXT_EXTENSIONS,
    DocumentReadError,
    UnsupportedFileType,
    load_document,
)
from .store import store_chunks

DATA_DIR = Path("data")
CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "anchor"
SUPPORTED = TEXT_EXTENSIONS | {PDF_EXTENSION}


def find_documents(data_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in data_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED
    )


def ingest_file(path: Path, tokenizer, embedder, collection) -> int:
    document = load_document(path)
    chunks = chunk_text(document.text, tokenizer)
    return store_chunks(
        chunks,
        source_path=document.source_path,
        filename=document.filename,
        embedder=embedder,
        collection=collection,
    )


def main() -> int:
    if not DATA_DIR.is_dir():
        print(f"No data directory at {DATA_DIR.resolve()}", file=sys.stderr)
        return 1

    documents = find_documents(DATA_DIR)
    if not documents:
        print(f"No supported documents found in {DATA_DIR.resolve()}")
        return 0

    tokenizer = tiktoken.get_encoding("cl100k_base")
    embedder = OllamaEmbedder()
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    collection = client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    total = 0
    for path in documents:
        try:
            stored = ingest_file(path, tokenizer, embedder, collection)
        except (DocumentReadError, UnsupportedFileType) as exc:
            print(f"Skipped {path.name}: {exc}", file=sys.stderr)
            continue
        total += stored
        print(f"{path.name}: {stored} chunks")

    print(f"Done. {total} chunks from {len(documents)} documents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())