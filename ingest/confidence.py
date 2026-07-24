"""Decide whether retrieved chunks are strong enough to answer from.

The refuse-to-guess gate. Cosine distance runs 0 (identical) to 2 (opposite);
with nomic-embed-text, strong topical matches land near 0.2 and unrelated
chunks score higher. If the nearest chunk is beyond the threshold, the system
should decline rather than answer from weak context.
"""

from __future__ import annotations

from dataclasses import dataclass

from .retriever import RetrievedChunk

DEFAULT_MAX_DISTANCE = 0.5


@dataclass(frozen=True)
class Confidence:
    is_confident: bool
    best_distance: float | None
    reason: str


def assess_confidence(
    chunks: list[RetrievedChunk],
    max_distance: float = DEFAULT_MAX_DISTANCE,
) -> Confidence:
    """Judge whether the best chunk is close enough to answer from.

    Returns a Confidence with is_confident False when there are no chunks or
    the nearest exceeds max_distance. best_distance is None only when there are
    no chunks.
    """
    if max_distance <= 0:
        raise ValueError("max_distance must be positive")

    if not chunks:
        return Confidence(False, None, "no chunks retrieved")

    best = min(chunk.distance for chunk in chunks)

    if best > max_distance:
        return Confidence(
            False,
            best,
            f"nearest chunk distance {best:.3f} exceeds {max_distance:.3f}",
        )

    return Confidence(True, best, "sufficient match")