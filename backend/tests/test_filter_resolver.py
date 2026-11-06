"""
Unit tests for filter resolver and search filter validation.
"""

import pytest
from apis.v1.schemas.search import NormalizedQuery, UIFilters, SearchFilters
from services.search_flow.filter_resolver import resolve_filters


def test_ui_filters_precedence():
    # When both UI and query filters are provided, UI filters must take precedence
    parsed = NormalizedQuery(
        query="chocolate",
        min_price=10.0,
        max_price=50.0,
        radius_km=5.0,
    )

    ui = UIFilters(
        min_price=20.0,
        max_price=100.0,
        radius_km=10.0,
    )

    resolved = resolve_filters(parsed, ui)

    assert resolved.min_price == 20.0
    assert resolved.max_price == 100.0
    assert resolved.radius_km == 10.0


def test_fallback_to_query_filters():
    # When UI filters are None, query filters should be used
    parsed = NormalizedQuery(
        query="milk",
        min_price=30.0,
        max_price=60.0,
        radius_km=3.0,
    )

    ui = UIFilters(
        min_price=None,
        max_price=None,
        radius_km=None,
    )

    resolved = resolve_filters(parsed, ui)

    assert resolved.min_price == 30.0
    assert resolved.max_price == 60.0
    assert resolved.radius_km == 3.0


def test_search_filters_validation_negative_min_price():
    with pytest.raises(ValueError, match="Minimum price cannot be negative"):
        SearchFilters(min_price=-5.0)


def test_search_filters_validation_negative_max_price():
    with pytest.raises(ValueError, match="Maximum price cannot be negative"):
        SearchFilters(max_price=-10.0)


def test_search_filters_validation_min_greater_than_max():
    with pytest.raises(ValueError, match="Minimum price cannot be greater than maximum price"):
        SearchFilters(min_price=100.0, max_price=50.0)


def test_search_filters_validation_radius_zero_or_negative():
    with pytest.raises(ValueError, match="Radius must be greater than 0"):
        SearchFilters(radius_km=0.0)

    with pytest.raises(ValueError, match="Radius must be greater than 0"):
        SearchFilters(radius_km=-2.0)
