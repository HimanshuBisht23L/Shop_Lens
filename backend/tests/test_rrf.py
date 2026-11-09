"""
Unit Tests for Search V2 Reciprocal Rank Fusion (RRF).
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from db.models.product import Product
from services.search.ranking.rrf import reciprocal_rank_fusion


def make_dummy_product(pid: int, name: str) -> Product:
    p = Product()
    p.id = pid
    p.name = name
    p.price = 100.0
    return p


def test_rrf_multi_channel_boost():
    p1 = make_dummy_product(1, "Dairy Milk Chocolate")
    p2 = make_dummy_product(2, "Amul Milk")
    p3 = make_dummy_product(3, "KitKat")

    # p1 is in both FTS and Vector
    fts_results = [(p1, 0.9), (p2, 0.5)]
    fuzzy_results = [(p3, 0.8)]
    vector_results = [(p1, 0.85), (p3, 0.7)]

    ranked = reciprocal_rank_fusion(
        fts_results=fts_results,
        fuzzy_results=fuzzy_results,
        vector_results=vector_results,
        k=60,
    )

    assert len(ranked) == 3
    # p1 appears at rank 1 in fts and rank 1 in vector -> highest score
    assert ranked[0].product.id == 1
    assert "fts" in ranked[0].sources
    assert "vector" in ranked[0].sources
    assert ranked[0].score > ranked[1].score


def test_rrf_empty_inputs():
    ranked = reciprocal_rank_fusion([], [], [], k=60)
    assert ranked == []


def test_rrf_single_channel():
    p1 = make_dummy_product(1, "A")
    p2 = make_dummy_product(2, "B")

    ranked = reciprocal_rank_fusion(
        fts_results=[(p1, 1.0), (p2, 0.5)],
        fuzzy_results=[],
        vector_results=[],
        k=60,
    )

    assert len(ranked) == 2
    assert ranked[0].product.id == 1
    assert ranked[0].sources == ["fts"]
    assert ranked[1].product.id == 2
