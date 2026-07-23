"""Tests for generate_answer with a fake Claude client (no API calls)."""

from .confidence import Confidence
from .generate import (
    DEFAULT_MODEL,
    REFUSAL_MESSAGE,
    SYSTEM_PROMPT,
    generate_answer,
)
from .retriever import RetrievedChunk


class FakeClient:
    def __init__(self, reply="Claude answer"):
        self.reply = reply
        self.calls = []

    def create_message(self, model, system, prompt):
        self.calls.append({"model": model, "system": system, "prompt": prompt})
        return self.reply


def chunk(filename="a.txt", text="chunk text", distance=0.2):
    return RetrievedChunk(
        text=text,
        source_path="data/" + filename,
        filename=filename,
        chunk_index=0,
        distance=distance,
    )


CONFIDENT = Confidence(True, 0.2, "ok")
NOT_CONFIDENT = Confidence(False, 0.9, "too far")
NO_CHUNKS = Confidence(False, None, "no chunks")


def test_refuses_when_not_confident_without_calling_claude():
    client = FakeClient()
    answer = generate_answer("q", [chunk()], NOT_CONFIDENT, client)
    assert answer.is_refusal is True
    assert answer.text == REFUSAL_MESSAGE
    assert answer.sources == []
    assert client.calls == []


def test_refuses_when_no_chunks():
    client = FakeClient()
    answer = generate_answer("q", [], NO_CHUNKS, client)
    assert answer.is_refusal is True
    assert client.calls == []


def test_answers_when_confident():
    client = FakeClient("The answer is 20 hours.")
    answer = generate_answer("q", [chunk()], CONFIDENT, client)
    assert answer.is_refusal is False
    assert answer.text == "The answer is 20 hours."
    assert len(client.calls) == 1


def test_prompt_includes_context_and_question():
    client = FakeClient()
    generate_answer("How many hours?", [chunk(text="up to 20 hours")], CONFIDENT, client)
    prompt = client.calls[0]["prompt"]
    assert "up to 20 hours" in prompt
    assert "How many hours?" in prompt
    assert "a.txt" in prompt


def test_uses_system_prompt():
    client = FakeClient()
    generate_answer("q", [chunk()], CONFIDENT, client)
    assert client.calls[0]["system"] == SYSTEM_PROMPT


def test_default_model_used():
    client = FakeClient()
    generate_answer("q", [chunk()], CONFIDENT, client)
    assert client.calls[0]["model"] == DEFAULT_MODEL


def test_custom_model_used():
    client = FakeClient()
    generate_answer("q", [chunk()], CONFIDENT, client, model="claude-haiku-4-5")
    assert client.calls[0]["model"] == "claude-haiku-4-5"


def test_sources_are_deduplicated():
    client = FakeClient()
    answer = generate_answer(
        "q", [chunk("a.txt"), chunk("a.txt"), chunk("b.txt")], CONFIDENT, client
    )
    assert answer.sources == ["a.txt", "b.txt"]


def test_multiple_sources_appear_in_context():
    client = FakeClient()
    generate_answer(
        "q", [chunk("a.txt", "text A"), chunk("b.txt", "text B")], CONFIDENT, client
    )
    prompt = client.calls[0]["prompt"]
    assert "text A" in prompt and "text B" in prompt
    assert "a.txt" in prompt and "b.txt" in prompt


def test_answer_is_frozen():
    client = FakeClient()
    answer = generate_answer("q", [chunk()], CONFIDENT, client)
    import pytest

    with pytest.raises(Exception):
        answer.text = "mutated"  # type: ignore[misc]