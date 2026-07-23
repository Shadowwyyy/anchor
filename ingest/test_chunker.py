"""Tests for chunk_text using a fake one-token-per-word tokenizer."""

import pytest

from .chunker import Chunk, chunk_text


class WordTokenizer:
    def __init__(self) -> None:
        self._vocab: list[str] = []

    def encode(self, text: str) -> list[int]:
        tokens = []
        for word in text.split():
            self._vocab.append(word)
            tokens.append(len(self._vocab) - 1)
        return tokens

    def decode(self, tokens: list[int]) -> str:
        return " ".join(self._vocab[token] for token in tokens)


@pytest.fixture
def tokenizer() -> WordTokenizer:
    return WordTokenizer()


def make_text(word_count: int) -> str:
    return " ".join(f"w{i}" for i in range(word_count))


def test_empty_string_returns_no_chunks(tokenizer):
    assert chunk_text("", tokenizer) == []


def test_whitespace_only_returns_no_chunks(tokenizer):
    assert chunk_text("   \n\t  ", tokenizer) == []


def test_short_text_fits_in_single_chunk(tokenizer):
    text = make_text(10)
    chunks = chunk_text(text, tokenizer, chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].token_count == 10
    assert chunks[0].text == text


def test_exact_multiple_of_step(tokenizer):
    chunks = chunk_text(make_text(100), tokenizer, chunk_size=50, overlap=0)
    assert len(chunks) == 2
    assert [c.token_count for c in chunks] == [50, 50]


def test_indices_are_contiguous_and_ordered(tokenizer):
    chunks = chunk_text(make_text(120), tokenizer, chunk_size=50, overlap=10)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_overlap_shares_tokens_between_neighbors(tokenizer):
    chunks = chunk_text(make_text(90), tokenizer, chunk_size=50, overlap=10)
    first_words = chunks[0].text.split()
    second_words = chunks[1].text.split()
    assert first_words[-10:] == second_words[:10]


def test_no_all_overlap_tail_chunk(tokenizer):
    chunks = chunk_text(make_text(60), tokenizer, chunk_size=50, overlap=10)
    assert len(chunks) == 2
    assert chunks[-1].token_count == 20


def test_all_tokens_are_covered(tokenizer):
    text = make_text(200)
    chunks = chunk_text(text, tokenizer, chunk_size=50, overlap=10)
    covered = set()
    for chunk in chunks:
        covered.update(chunk.text.split())
    assert covered == set(text.split())


def test_chunk_is_frozen(tokenizer):
    chunk = chunk_text(make_text(3), tokenizer)[0]
    with pytest.raises(Exception):
        chunk.text = "mutated"  # type: ignore[misc]


@pytest.mark.parametrize(
    "chunk_size, overlap",
    [(0, 0), (-1, 0), (10, -1), (10, 10), (10, 20)],
)
def test_invalid_parameters_raise(tokenizer, chunk_size, overlap):
    with pytest.raises(ValueError):
        chunk_text("some text here", tokenizer, chunk_size=chunk_size, overlap=overlap)


def test_returns_chunk_dataclass_instances(tokenizer):
    chunks = chunk_text(make_text(5), tokenizer)
    assert all(isinstance(c, Chunk) for c in chunks)