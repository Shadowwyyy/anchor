"""Adapter around the Anthropic SDK implementing the ClaudeClient protocol."""

from __future__ import annotations

import os

import anthropic

from .generate import MAX_TOKENS


class AnthropicClaudeClient:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._client = anthropic.Anthropic(api_key=key)

    def create_message(self, model: str, system: str, prompt: str) -> str:
        response = self._client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")