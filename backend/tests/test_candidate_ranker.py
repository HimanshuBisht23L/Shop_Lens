"""
Unit tests for candidate ranker and fusion logic.
"""

from types import SimpleNamespace
import pytest

from services.search_flow.candidate_ranker import (
    CandidateRankItem,
    rank_candidates,
    _extract_query_tokens,
    _check_attribute_alignment,
)


def make_product(id: int, name: str, attributes: list[str] | None = None):
    """Helper to create a mock Product with optional attributes."""
    p_attrs = []
    for a in (attributes or []):
        p_attrs.append(SimpleNamespace(attribute=SimpleNamespace(name=a)))

    return SimpleNamespace(
        id=id,
        name=name,
        normalized_name=name.lower(),
        description=f"Description for {name}",
        product_attributes=p_attrs,
    )


def test_empty_query_returns_empty():
    results = rank_candidates(
        query="",
        keyword_products=[make_product(1, "Amul Butter")],
        fuzzy_results=[],
        semantic_results=[],
    )
    assert results == []


def test_exact_match_guarantee():
    p1 = make_product(1, "Amul Butter")
    p2 = make_product(2, "Britannia Bread")

    # p1 is exact keyword match; p2 is semantic match with high raw similarity
    results = rank_candidates(
        query="Amul Butter",
        keyword_products=[p1],
        fuzzy_results=[(p1, 1.0)],
        semantic_results=[(p1, 0.45), (p2, 0.55)],
    )

    assert len(results) >= 1
    assert results[0].product_id == 1
    assert results[0].final_score == 1.00
    assert results[0].match_tier == "exact_match"


def test_keyword_beats_weak_semantic():
    p_kw = make_product(1, "Cadbury 5 Star Chocolate")
    p_sem = make_product(2, "Banana")

    results = rank_candidates(
        query="Cadbury",
        keyword_products=[p_kw],
        fuzzy_results=[],
        semantic_results=[(p_kw, 0.30), (p_sem, 0.15)],
    )

    assert results[0].product_id == 1
    assert results[0].final_score > 0.85
    # Weak semantic noise (Banana) should be pruned because a strong keyword match exists
    assert len(results) == 1 or results[0].final_score > results[1].final_score


def test_fuzzy_match_retains_typos():
    p = make_product(1, "Cadbury Dairy Milk Chocholate")

    results = rank_candidates(
        query="chocolate",
        keyword_products=[],
        fuzzy_results=[(p, 0.82)],
        semantic_results=[(p, 0.40)],
    )

    assert len(results) == 1
    assert results[0].product_id == 1
    assert "fuzzy" in results[0].sources
    assert "semantic" in results[0].sources
    assert results[0].final_score > 0.70


def test_semantic_only_query():
    p_pepsi = make_product(11, "Pepsi", ["cold-drink", "drinkable"])
    p_coke = make_product(12, "Coca Cola", ["cold-drink", "drinkable"])
    p_banana = make_product(15, "Banana", ["fruit"])

    results = rank_candidates(
        query="something to drink",
        keyword_products=[],
        fuzzy_results=[],
        semantic_results=[(p_pepsi, 0.27), (p_coke, 0.268), (p_banana, 0.15)],
    )

    assert len(results) >= 2
    assert results[0].product_id in (11, 12)
    assert results[0].match_tier == "semantic_only"
    # Both drinks should be ranked above banana
    drink_ids = {results[0].product_id, results[1].product_id}
    assert 11 in drink_ids and 12 in drink_ids


def test_attribute_bonus_applies_correctly():
    p_drink = make_product(1, "Pepsi", ["drinkable", "cold-drink"])
    p_nodrink = make_product(2, "Cadbury 5 Star", ["chocolate", "sweet"])

    results = rank_candidates(
        query="cold drinks",
        keyword_products=[],
        fuzzy_results=[],
        semantic_results=[(p_drink, 0.25), (p_nodrink, 0.25)],
    )

    assert len(results) == 2
    # p_drink should receive attribute bonus (+0.05) and rank first
    assert results[0].product_id == 1
    assert results[0].attribute_bonus == 0.05
    assert results[1].attribute_bonus == 0.00
    assert results[0].final_score > results[1].final_score


def test_channel_corroboration_bonus():
    p_multi = make_product(1, "Amul Butter")
    p_single = make_product(2, "Britannia Bread")

    results = rank_candidates(
        query="butter",
        keyword_products=[p_multi, p_single],
        fuzzy_results=[(p_multi, 0.90)],
        semantic_results=[(p_multi, 0.40)],
    )

    item_multi = next(r for r in results if r.product_id == 1)
    item_single = next(r for r in results if r.product_id == 2)

    assert item_multi.corroboration_bonus > item_single.corroboration_bonus


def test_deterministic_ranking():
    p1 = make_product(1, "Product A")
    p2 = make_product(2, "Product B")

    run1 = rank_candidates(
        query="prod",
        keyword_products=[p1, p2],
        fuzzy_results=[],
        semantic_results=[],
    )

    run2 = rank_candidates(
        query="prod",
        keyword_products=[p2, p1], # reversed input order
        fuzzy_results=[],
        semantic_results=[],
    )

    assert [r.product_id for r in run1] == [r.product_id for r in run2]
    assert [r.final_score for r in run1] == [r.final_score for r in run2]


def test_deduplication_of_candidates():
    p = make_product(1, "Amul Butter")

    results = rank_candidates(
        query="butter",
        keyword_products=[p],
        fuzzy_results=[(p, 0.75)],
        semantic_results=[(p, 0.35)],
    )

    # Product 1 appeared in all 3 channels, must be merged into 1 item
    assert len(results) == 1
    assert set(results[0].sources) == {"keyword", "fuzzy", "semantic"}
