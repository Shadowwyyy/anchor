"""Tests for OllamaEmbedder with mocked HTTP; no live Ollama server needed."""

from unittest.mock import MagicMock, patch

import pytest

from .embedder import OllamaEmbedder


def fake_response(json_data, ok=True):
    response = MagicMock()
    response.json.return_value = json_data
    if not ok:
        response.raise_for_status.side_effect = RuntimeError("HTTP 500")
    return response


def test_returns_embedding_vector():
    embedder = OllamaEmbedder()
    with patch("ingest.embedder.requests.post", return_value=fake_response({"embedding": [0.1, 0.2, 0.3]})):
        assert embedder.embed("hello") == [0.1, 0.2, 0.3]


def test_sends_model_and_prompt():
    embedder = OllamaEmbedder(model="nomic-embed-text")
    with patch("ingest.embedder.requests.post", return_value=fake_response({"embedding": [1.0]})) as post:
        embedder.embed("some text")
    _, kwargs = post.call_args
    assert kwargs["json"] == {"model": "nomic-embed-text", "prompt": "some text"}


def test_empty_text_raises():
    with pytest.raises(ValueError):
        OllamaEmbedder().embed("   ")


def test_missing_embedding_field_raises():
    embedder = OllamaEmbedder()
    with patch("ingest.embedder.requests.post", return_value=fake_response({})):
        with pytest.raises(RuntimeError):
            embedder.embed("hello")


def test_http_error_propagates():
    embedder = OllamaEmbedder()
    with patch("ingest.embedder.requests.post", return_value=fake_response({}, ok=False)):
        with pytest.raises(RuntimeError):
            embedder.embed("hello")