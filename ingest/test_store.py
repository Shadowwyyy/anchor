"""Tests for store_chunks with fake embedder and collection."""

from .chunker import Chunk
from .store import _chunk_id, store_chunks


class FakeEmbedder:
    def __init__(self):
        self.calls = []

    def embed(self, text):
        self.calls.append(text)
        return [float(len(text)), 1.0, 2.0]


class FakeCollection:
    def __init__(self):
        self.added = None

    def add(self, ids, embeddings, documents, metadatas):
        self.added = {
            "ids": ids,
            "embeddings": embeddings,
            "documents": documents,
            "metadatas": metadatas,
        }


def make_chunks(count):
    return [Chunk(text=f"chunk text {i}", index=i, token_count=3) for i in range(count)]


def test_empty_chunks_stores_nothing():
    embedder, collection = FakeEmbedder(), FakeCollection()
    assert store_chunks([], "p.txt", "p.txt", embedder, collection) == 0
    assert collection.added is None
    assert embedder.calls == []


def test_returns_stored_count():
    embedder, collection = FakeEmbedder(), FakeCollection()
    assert store_chunks(make_chunks(3), "p.txt", "p.txt", embedder, collection) == 3


def test_embeds_every_chunk_in_order():
    embedder, collection = FakeEmbedder(), FakeCollection()
    store_chunks(make_chunks(3), "p.txt", "p.txt", embedder, collection)
    assert embedder.calls == ["chunk text 0", "chunk text 1", "chunk text 2"]


def test_ids_are_unique_and_scoped_to_source():
    embedder, collection = FakeEmbedder(), FakeCollection()
    store_chunks(make_chunks(3), "docs/a.pdf", "a.pdf", embedder, collection)
    ids = collection.added["ids"]
    assert len(set(ids)) == 3
    assert ids[0] == "docs/a.pdf::chunk-0"


def test_metadata_carries_source_and_index():
    embedder, collection = FakeEmbedder(), FakeCollection()
    store_chunks(make_chunks(2), "docs/a.pdf", "a.pdf", embedder, collection)
    assert collection.added["metadatas"][1] == {
        "source_path": "docs/a.pdf",
        "filename": "a.pdf",
        "chunk_index": 1,
    }


def test_documents_are_preserved():
    embedder, collection = FakeEmbedder(), FakeCollection()
    store_chunks(make_chunks(2), "p.txt", "p.txt", embedder, collection)
    assert collection.added["documents"] == ["chunk text 0", "chunk text 1"]


def test_all_record_lists_are_parallel():
    embedder, collection = FakeEmbedder(), FakeCollection()
    store_chunks(make_chunks(4), "p.txt", "p.txt", embedder, collection)
    added = collection.added
    lengths = {len(added[key]) for key in ("ids", "embeddings", "documents", "metadatas")}
    assert lengths == {4}


def test_chunk_id_format():
    assert _chunk_id("x/y.txt", 5) == "x/y.txt::chunk-5"