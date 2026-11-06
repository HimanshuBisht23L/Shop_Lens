"""
Unit tests for query normalizer (services/search_flow/normalizer.py).
"""

from services.search_flow.normalizer import normalize_query


def test_normalize_exact_product_name():
    result = normalize_query("Amul Butter")
    assert result.query == "amul butter"
    assert result.min_price is None
    assert result.max_price is None
    assert result.radius_km is None


def test_normalize_max_price_extraction():
    result = normalize_query("sweet things under 500 ruppee")
    assert result.query == "sweet things"
    assert result.max_price == 500.0
    assert result.min_price is None


def test_normalize_price_range():
    result = normalize_query("chips between 20 and 50 rs")
    assert result.query == "chips"
    assert result.min_price == 20.0
    assert result.max_price == 50.0


def test_normalize_min_price():
    result = normalize_query("milk above 30")
    assert result.query == "milk"
    assert result.min_price == 30.0
    assert result.max_price is None


def test_normalize_radius_km():
    result = normalize_query("chocolate within 5 km")
    assert result.query == "chocolate"
    assert result.radius_km == 5.0


def test_normalize_radius_miles_conversion():
    result = normalize_query("bread within 2 miles")
    assert result.query == "bread"
    assert result.radius_km is not None
    assert round(result.radius_km, 2) == round(2 * 1.60934, 2)


def test_normalize_removes_filler_and_location():
    result = normalize_query("please find me cold drinks near me")
    assert result.query == "cold drinks"
    assert result.min_price is None
    assert result.max_price is None


def test_normalize_empty_and_whitespace():
    result1 = normalize_query("")
    assert result1.query == ""

    result2 = normalize_query("     ")
    assert result2.query == ""


def test_normalize_preserves_product_terms():
    result = normalize_query("bread in store")
    assert result.query == "bread in store"

    result2 = normalize_query("Cadbury Dairy Milk Chocholate")
    assert result2.query == "cadbury dairy milk chocholate"
