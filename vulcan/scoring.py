"""C1 disqualification + weighted rubric for selecting one breakthrough to build."""
from __future__ import annotations

from dataclasses import dataclass

# Buildability (can we make it real here, no mocks) is weighted highest:
# it is what separates ledge from nemesis.
WEIGHTS = {"novelty": 0.25, "adjacency": 0.20, "buildability": 0.35, "oss_value": 0.20}


@dataclass
class Candidate:
    title: str
    summary: str
    sources: list[str]
    needs_gpu: bool
    novelty: int
    adjacency: int
    buildability: int
    oss_value: int


def disqualified(c: Candidate) -> str | None:
    """C1: anything needing a GPU to be real is out — it would force mocks."""
    if c.needs_gpu:
        return "needs GPU — cannot be verified for real on CPU-only hardware (C1)"
    return None


def score(c: Candidate) -> float:
    if disqualified(c):
        return float("-inf")
    return (
        WEIGHTS["novelty"] * c.novelty
        + WEIGHTS["adjacency"] * c.adjacency
        + WEIGHTS["buildability"] * c.buildability
        + WEIGHTS["oss_value"] * c.oss_value
    )


def select(cands: list[Candidate]) -> Candidate | None:
    qualified = [c for c in cands if not disqualified(c)]
    if not qualified:
        return None
    return max(qualified, key=score)
