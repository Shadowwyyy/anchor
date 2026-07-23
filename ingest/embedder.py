"""Embed text via a local Ollama model."""

from __future__ import annotations

from typing import Protocol

import requests

DEFAULT_MODEL = "nomic-embed-text"
DEFAULT_URL = "http://localhost:11434/api/embeddings"


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class OllamaEmbedder:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        url: str = DEFAULT_URL,
        timeout: float = 30.0,
    ) -> None:
        self._model = model
        self._url = url
        self._timeout = timeout

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("cannot embed empty text")

        response = requests.post(
            self._url,
            json={"model": self._model, "prompt": text},
            timeout=self._timeout,
        )
        response.raise_for_status()
        embedding = response.json().get("embedding")

        if not embedding:
            raise RuntimeError("Ollama returned no embedding")
        return embedding