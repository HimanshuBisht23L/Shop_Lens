"""
Reciprocal Rank Fusion (RRF) Ranking Module for ShopLens Search V2.

Merges multi-channel retrieval candidates (FTS, Word-level Trigram Fuzzy, Dense Vector):
RRF(d) = sum_{c in channels} ( weight_c / (k + rank_c(d)) )

Ensures robust hybrid retrieval by rewarding candidates found across multiple retrieval methods.
"""

from dataclasses import dataclass, field
from db.models.product import Product
from config import settings


@dataclass
class RankedCandidate:
    product: Product
    score: float
    sources: list[str] = field(default_factory=list)
    raw_scores: dict[str, float] = field(default_factory=dict)


def reciprocal_rank_fusion(
    fts_results: list[tuple[Product, float]],
    fuzzy_results: list[tuple[Product, float]],
    vector_results: list[tuple[Product, float]],
    k: int = settings.RRF_K,
    weights: dict[str, float] | None = None,
) -> list[RankedCandidate]:
    """
    Combines ranked candidate lists using Reciprocal Rank Fusion.

    :param fts_results: Ranked tuples of (Product, fts_score)
    :param fuzzy_results: Ranked tuples of (Product, fuzzy_score)
    :param vector_results: Ranked tuples of (Product, similarity_score)
    :param k: RRF smoothing constant (default: 60)
    :param weights: Channel weights, e.g. {"fts": 1.0, "fuzzy": 0.8, "vector": 1.0}
    :return: List of RankedCandidate sorted by descending fused score.
    """
    if weights is None:
        weights = {
            "fts": 1.0,
            "fuzzy": 0.8,
            "vector": 1.0,
        }

    channels: dict[str, list[tuple[Product, float]]] = {
        "fts": fts_results,
        "fuzzy": fuzzy_results,
        "vector": vector_results,
    }

    product_map: dict[int, Product] = {}
    fused_scores: dict[int, float] = {}
    candidate_sources: dict[int, list[str]] = {}
    candidate_raw_scores: dict[int, dict[str, float]] = {}

    for channel_name, results in channels.items():
        w = weights.get(channel_name, 1.0)
        for rank_idx, (product, raw_score) in enumerate(results):
            pid = product.id
            if pid not in product_map:
                product_map[pid] = product
                fused_scores[pid] = 0.0
                candidate_sources[pid] = []
                candidate_raw_scores[pid] = {}

            # 1-based rank
            rank = rank_idx + 1
            fused_scores[pid] += w / (k + rank)
            if channel_name not in candidate_sources[pid]:
                candidate_sources[pid].append(channel_name)
            candidate_raw_scores[pid][channel_name] = raw_score

    # Build and sort candidate list
    ranked_candidates = [
        RankedCandidate(
            product=product_map[pid],
            score=round(fused_scores[pid], 6),
            sources=candidate_sources[pid],
            raw_scores=candidate_raw_scores[pid],
        )
        for pid in product_map
    ]

    ranked_candidates.sort(key=lambda c: c.score, reverse=True)
    return ranked_candidates
