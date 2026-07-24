"""Tests for the refuse-to-guess confidence gate."""

import pytest

from .confidence import DEFAULT_MAX_DISTANCE, assess_confidence
from .retriever import RetrievedChunk


def chunk_at(distance):
    return RetrievedChunk(
        text="t", source_path="p", filename="f", chunk_index=0, distance=distance
    )


def test_no_chunks_is_not_confident():
    result = assess_confidence([])
    assert result.is_confident is False
    assert result.best_distance is None
    assert "no chunks" in result.reason


def test_strong_match_is_confident():
    result = assess_confidence([chunk_at(0.2)])
    assert result.is_confident is True
    assert result.best_distance == 0.2


def test_weak_match_is_not_confident():
    result = assess_confidence([chunk_at(0.9)])
    assert result.is_confident is False
    assert result.best_distance == 0.9
    assert "exceeds" in result.reason


def test_uses_nearest_chunk():
    result = assess_confidence([chunk_at(0.9), chunk_at(0.3), chunk_at(0.7)])
    assert result.is_confident is True
    assert result.best_distance == 0.3


def test_distance_exactly_at_threshold_passes():
    assert assess_confidence([chunk_at(0.6)], max_distance=0.6).is_confident is True


def test_distance_just_over_threshold_fails():
    assert assess_confidence([chunk_at(0.61)], max_distance=0.6).is_confident is False


def test_custom_threshold():
    assert assess_confidence([chunk_at(0.4)], max_distance=0.3).is_confident is False
    assert assess_confidence([chunk_at(0.4)], max_distance=0.5).is_confident is True


@pytest.mark.parametrize("bad", [0, -0.1])
def test_non_positive_threshold_raises(bad):
    with pytest.raises(ValueError):
        assess_confidence([chunk_at(0.2)], max_distance=bad)


def test_default_threshold_value():
    assert DEFAULT_MAX_DISTANCE == 0.5


def test_confidence_is_frozen():
    result = assess_confidence([chunk_at(0.2)])
    with pytest.raises(Exception):
        result.is_confident = False  # type: ignore[misc]