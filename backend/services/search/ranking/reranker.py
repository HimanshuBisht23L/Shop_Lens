"""
Cross-Encoder Reranker Module for ShopLens Search V2.

Applies a deep transformer Cross-Encoder (e.g. ms-marco-MiniLM-L-6-v2) to score
(query, candidate_document) pairs directly for high-precision semantic relevance.

Features:
- Threadpool execution to prevent event loop blocking.
- Graceful fallback to RRF rankings if the model is disabled or unavailable.
- Sigmoid activation on logits for standardized [0, 1] relevance scores.
"""

import asyncio
from functools import lru_cache
from typing import Optional

from config import settings
from core.logging import logger
from services.search.ranking.rrf import RankedCandidate


_RERANKER_INSTANCE = None
_RERANKER_INITIALIZATION_ATTEMPTED = False


def get_reranker_model():
    global _RERANKER_INSTANCE, _RERANKER_INITIALIZATION_ATTEMPTED
    if _RERANKER_INITIALIZATION_ATTEMPTED:
        return _RERANKER_INSTANCE

    _RERANKER_INITIALIZATION_ATTEMPTED = True
    if not settings.ENABLE_RERANKER:
        logger.info("Search V2 Cross-Encoder reranker is disabled by configuration.")
        return None

    try:
        from sentence_transformers import CrossEncoder
        logger.info(f"Loading CrossEncoder model: {settings.RERANKER_MODEL_NAME}")
        # CrossEncoder may use local cache ~/.cache/huggingface/hub
        _RERANKER_INSTANCE = CrossEncoder(settings.RERANKER_MODEL_NAME)
        logger.info("Search V2 CrossEncoder loaded successfully.")
    except Exception as exc:
        logger.warning(
            f"Failed to initialize CrossEncoder ({settings.RERANKER_MODEL_NAME}): {exc}. "
            "Falling back to Reciprocal Rank Fusion scores."
        )
        _RERANKER_INSTANCE = None

    return _RERANKER_INSTANCE


def _sync_rerank(
    query: str,
    candidates: list[RankedCandidate],
    top_k: int,
) -> list[RankedCandidate]:
    model = get_reranker_model()
    if model is None or not candidates:
        return candidates

    to_rerank = candidates[:top_k]
    remaining = candidates[top_k:]

    pairs = [
        (query, f"{c.product.name}. {c.product.description or ''}".strip())
        for c in to_rerank
    ]

    try:
        import numpy as np

        scores = model.predict(pairs, show_progress_bar=False)
        # Apply sigmoid if scores are raw logits
        if hasattr(scores, "__iter__"):
            sigmoid_scores = 1.0 / (1.0 + np.exp(-np.array(scores, dtype=float)))
        else:
            sigmoid_scores = [float(scores)]

        for cand, ce_score in zip(to_rerank, sigmoid_scores):
            # Combined score: 60% Cross-Encoder + 40% normalized RRF
            # RRF is usually in [0, 0.05], we record cross_encoder score
            cand.raw_scores["cross_encoder"] = float(round(ce_score, 4))
            cand.score = float(round(cand.score + 0.5 * ce_score, 6))

        to_rerank.sort(key=lambda c: c.score, reverse=True)
        return to_rerank + remaining
    except Exception as exc:
        logger.warning(f"Error during CrossEncoder reranking: {exc}. Using RRF order.")
        return candidates


async def rerank_candidates(
    query: str,
    candidates: list[RankedCandidate],
    top_k: int = settings.RERANK_TOP_K,
) -> list[RankedCandidate]:
    """
    Asynchronously reranks the top_k candidates using Cross-Encoder.
    """
    if not candidates or not settings.ENABLE_RERANKER:
        return candidates

    return await asyncio.to_thread(_sync_rerank, query, candidates, top_k)
