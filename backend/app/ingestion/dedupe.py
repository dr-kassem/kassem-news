"""Duplicate detection and event clustering helpers.

Similarity uses a weighted blend of token-set Jaccard and sequence ratio,
which is robust for short Arabic headlines without external embeddings.
"""
from __future__ import annotations

from difflib import SequenceMatcher

from app.ingestion import significant_tokens

# Thresholds are seeded as publishing rules and can be tuned in the dashboard.
DUPLICATE_THRESHOLD = 0.80
EVENT_THRESHOLD = 0.40


def similarity(a: str, b: str) -> float:
    """Sequence ratio over the ordered significant-token streams.

    This measures headline similarity much better than raw character diffs,
    because it normalises Arabic and ignores stopwords first.
    """
    ta = " ".join(significant_tokens(a))
    tb = " ".join(significant_tokens(b))
    if not ta or not tb:
        return 0.0
    return round(SequenceMatcher(None, ta, tb).ratio(), 4)


def is_duplicate(a: str, b: str, threshold: float = DUPLICATE_THRESHOLD) -> bool:
    return similarity(a, b) >= threshold


def same_event(a: str, b: str, threshold: float = EVENT_THRESHOLD) -> bool:
    return similarity(a, b) >= threshold


def best_match(title: str, candidates, threshold: float):
    """Return (candidate, score) with the highest similarity above threshold."""
    best, best_score = None, 0.0
    for candidate in candidates:
        score = similarity(title, candidate.normalized_title or candidate.title_ar)
        if score > best_score:
            best, best_score = candidate, score
    if best is not None and best_score >= threshold:
        return best, best_score
    return None, 0.0
