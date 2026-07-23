"""Tests for answer_question with fully faked dependencies."""

import pytest

from .service import AskResult, answer_question

META = {"source_path": "data/sample.txt", "filename": "sample.txt", "chunk_index": 0}


class FakeEmbedder:
    def embed(self, text):
        return [1.0, 2.0, 3.0]


class FakeCollection:
    def __init__(self, documents, metadatas, distances):
        self.result = {
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
        }

    def query(self, query_embeddings, n_results):
        return self.result


class FakeClaude:
    def __init__(self, reply="Answer text"):
        self.reply = reply
        self.called = False

    def create_message(self, model, system, prompt):
        self.called = True
        return self.reply


def test_empty_question_raises():
    with pytest.raises(ValueError):
        answer_question("  ", FakeEmbedder(), FakeCollection([], [], []), FakeClaude())


def test_confident_answer_flow():
    collection = FakeCollection(["F-1 students may work 20 hours"], [META], [0.2])
    claude = FakeClaude("Up to 20 hours per week.")
    result = answer_question("hours?", FakeEmbedder(), collection, claude)
    assert isinstance(result, AskResult)
    assert result.is_refusal is False
    assert result.is_confident is True
    assert result.answer == "Up to 20 hours per week."
    assert result.sources == ["sample.txt"]
    assert result.best_distance == 0.2
    assert claude.called is True


def test_weak_match_refuses_without_claude():
    collection = FakeCollection(["unrelated text"], [META], [0.95])
    claude = FakeClaude()
    result = answer_question("hours?", FakeEmbedder(), collection, claude)
    assert result.is_refusal is True
    assert result.is_confident is False
    assert result.sources == []
    assert claude.called is False


def test_empty_store_refuses_without_claude():
    collection = FakeCollection([], [], [])
    claude = FakeClaude()
    result = answer_question("hours?", FakeEmbedder(), collection, claude)
    assert result.is_refusal is True
    assert result.best_distance is None
    assert claude.called is False


def test_result_is_frozen():
    collection = FakeCollection(["x"], [META], [0.2])
    result = answer_question("q", FakeEmbedder(), collection, FakeClaude())
    with pytest.raises(Exception):
        result.answer = "mutated"  # type: ignore[misc]