"""Abstain helpers for naive RAG."""

from __future__ import annotations


def should_abstain(*, best_similarity: float | None, min_score: float, insufficient_context: bool) -> bool:
    if insufficient_context:
        return True
    if best_similarity is None:
        return True
    return best_similarity < min_score


def abstain_answer() -> str:
    return (
        "I do not have enough grounded context in the selected documents "
        "to answer that question."
    )
