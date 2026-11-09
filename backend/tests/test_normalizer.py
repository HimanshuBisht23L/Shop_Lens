"""
Unit Tests for Search V2 Query Normalizer.
"""

import sys
from pathlib import Path

# Add backend to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from services.search.query.normalizer import (
    normalize_query,
    extract_max_price,
    extract_min_price,
    extract_price_range,
    extract_radius,
    remove_fillers,
    map_hinglish_terms,
)


def test_clean_text_basic():
    res = normalize_query("  Chocolate   Cadbury   ")
    assert res.cleaned_query == "chocolate cadbury"
    assert res.min_price is None
    assert res.max_price is None


def test_extract_price_under_english():
    res = normalize_query("cake under 500")
    assert res.cleaned_query == "cake"
    assert res.max_price == 500.0


def test_extract_price_below_with_currency():
    res = normalize_query("biscuit below Rs. 40")
    assert res.cleaned_query == "biscuit"
    assert res.max_price == 40.0


def test_extract_price_hinglish_se_kam():
    res = normalize_query("chips 50 se kam")
    assert res.cleaned_query == "chips"
    assert res.max_price == 50.0


def test_extract_price_range():
    res = normalize_query("milk between 30 and 80")
    assert res.cleaned_query == "milk"
    assert res.min_price == 30.0
    assert res.max_price == 80.0


def test_extract_radius_km():
    res = normalize_query("ice cream within 5km")
    assert res.cleaned_query == "ice cream"
    assert res.radius_km == 5.0


def test_extract_radius_miles():
    res = normalize_query("butter under 3 miles")
    assert res.cleaned_query == "butter"
    assert round(res.radius_km, 2) == round(3 * 1.60934, 2)


def test_filler_word_removal():
    res = normalize_query("please show me chocolate near me")
    assert res.cleaned_query == "chocolate"


def test_hinglish_translation_doodh():
    res = normalize_query("amul doodh")
    assert res.cleaned_query == "amul milk"
    assert "doodh" in res.hinglish_terms_mapped
    assert res.hinglish_terms_mapped["doodh"] == "milk"


def test_hinglish_translation_multiple():
    res = normalize_query("pyaz aur tamatar")
    assert "onion" in res.cleaned_query
    assert "tomato" in res.cleaned_query


def test_combined_hinglish_and_price():
    res = normalize_query("amul doodh under 50")
    assert res.cleaned_query == "amul milk"
    assert res.max_price == 50.0
