"""Tests for retrieve with a fake embedder and Chroma-shaped fake collection."""

import pytest

from .retriever import RetrievedChunk, retrieve

META = {"source_path": "data/a.txt", "filename": "a.txt", "chunk_index": 0}


class FakeEmbedder:
    def __init__(self):
        self.calls = []

    def embed(self, text):
        self.calls.append(text)
        return [1.0, 2.0, 3.0]


class FakeCollection:
    def __init__(self, result):
        self.result = result
        self.last_n = None
        self.last_embeddings = None

    def query(self, query_embeddings, n_results):
        self.last_n = n_results
        self.last_embeddings = query_embeddings
        return self.result


def chroma_result(documents, metadatas, distances):
    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances],
    }


def test_empty_query_returns_nothing_without_embedding():
    embedder = FakeEmbedder()
    collection = FakeCollection(chroma_result([], [], []))
    assert retrieve("   ", embedder, collection) == []
    assert embedder.calls == []


def test_returns_retrieved_chunks_with_metadata():
    embedder = FakeEmbedder()
    collection = FakeCollection(
        chroma_result(
            ["chunk one", "chunk two"],
            [META, {"source_path": "data/b.txt", "filename": "b.txt", "chunk_index": 3}],
            [0.1, 0.4],
        )
    )
    results = retrieve("question", embedder, collection)
    assert len(results) == 2
    assert isinstance(results[0], RetrievedChunk)
    assert results[0].text == "chunk one"
    assert results[0].distance == 0.1
    assert results[1].filename == "b.txt"
    assert results[1].chunk_index == 3


def test_embeds_the_query_text():
    embedder = FakeEmbedder()
    collection = FakeCollection(chroma_result([], [], []))
    retrieve("my question", embedder, collection)
    assert embedder.calls == ["my question"]


def test_passes_top_k_to_collection():
    embedder = FakeEmbedder()
    collection = FakeCollection(chroma_result([], [], []))
    retrieve("q", embedder, collection, top_k=3)
    assert collection.last_n == 3


def test_default_top_k_is_five():
    embedder = FakeEmbedder()
    collection = FakeCollection(chroma_result([], [], []))
    retrieve("q", embedder, collection)
    assert collection.last_n == 5


@pytest.mark.parametrize("bad_top_k", [0, -1])
def test_invalid_top_k_raises(bad_top_k):
    embedder = FakeEmbedder()
    collection = FakeCollection(chroma_result([], [], []))
    with pytest.raises(ValueError):
        retrieve("q", embedder, collection, top_k=bad_top_k)


def test_preserves_result_order():
    embedder = FakeEmbedder()
    collection = FakeCollection(
        chroma_result(["near", "mid", "far"], [META, META, META], [0.05, 0.3, 0.9])
    )
    results = retrieve("q", embedder, collection)
    assert [c.distance for c in results] == [0.05, 0.3, 0.9]


def test_retrieved_chunk_is_frozen():
    embedder = FakeEmbedder()
    collection = FakeCollection(chroma_result(["x"], [META], [0.1]))
    chunk = retrieve("q", embedder, collection)[0]
    with pytest.raises(Exception):
        chunk.text = "mutated"  # type: ignore[misc]


def test_empty_collection_results():
    embedder = FakeEmbedder()
    collection = FakeCollection({"documents": [[]], "metadatas": [[]], "distances": [[]]})
    assert retrieve("q", embedder, collection) == []