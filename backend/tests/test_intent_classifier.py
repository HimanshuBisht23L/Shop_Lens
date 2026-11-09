"""
Unit Tests for Search V2 Query Intent Classifier.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from services.search.query.intent_classifier import (
    classify_query_intent,
    TYPE_A_SPECIFIC,
    TYPE_B_CONCEPTUAL,
)


def test_type_a_single_subcategory():
    res = classify_query_intent("chocolate")
    assert res.intent_type == TYPE_A_SPECIFIC
    assert res.matched_sub_category == "Chocolates"

    res_milk = classify_query_intent("doodh")
    assert res_milk.intent_type == TYPE_A_SPECIFIC
    assert res_milk.matched_sub_category == "Milk"


def test_type_a_single_brand():
    res = classify_query_intent("amul")
    assert res.intent_type == TYPE_A_SPECIFIC
    assert res.matched_brand == "Amul"


def test_type_a_phrase_priority_dairy_milk():
    # "dairy milk" should match "Chocolates", NOT the single token "milk"
    res = classify_query_intent("cadbury dairy milk")
    assert res.intent_type == TYPE_A_SPECIFIC
    assert res.matched_brand == "Cadbury"
    assert res.matched_sub_category == "Chocolates"


def test_type_a_brand_and_subcategory():
    res = classify_query_intent("amul milk")
    assert res.intent_type == TYPE_A_SPECIFIC
    assert res.matched_brand == "Amul"
    assert res.matched_sub_category == "Milk"


def test_type_a_fuzzy_typo_matching():
    # 'choclate' has similarity > 0.85 to 'chocolate' -> matches Chocolates
    res = classify_query_intent("choclate")
    assert res.intent_type == TYPE_A_SPECIFIC
    assert res.matched_sub_category == "Chocolates"


def test_type_b_conceptual_queries():
    conceptual_queries = [
        "sweet things",
        "party snacks",
        "quick breakfast",
        "healthy snacks",
        "something spicy",
    ]
    for q in conceptual_queries:
        res = classify_query_intent(q)
        assert res.intent_type == TYPE_B_CONCEPTUAL, f"Expected TYPE_B for query: {q}"
        assert res.matched_brand is None
        assert res.matched_sub_category is None


def test_empty_query():
    res = classify_query_intent("")
    assert res.intent_type == TYPE_B_CONCEPTUAL
