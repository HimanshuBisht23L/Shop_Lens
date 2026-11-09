"""
Unit Tests for Search V2 Filter Resolver.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from services.search.query.normalizer import NormalizedQueryOutput
from services.search.query.filter_resolver import resolve_filters


def test_ui_precedence_over_parsed():
    parsed = NormalizedQueryOutput(
        original_query="cake under 300",
        cleaned_query="cake",
        max_price=300.0,
        radius_km=2.0,
    )
    resolved = resolve_filters(
        parsed=parsed,
        ui_max_price=500.0,
        ui_radius_km=10.0,
    )
    assert resolved.search_text == "cake"
    assert resolved.max_price == 500.0
    assert resolved.radius_km == 10.0


def test_fallback_to_parsed_when_ui_absent():
    parsed = NormalizedQueryOutput(
        original_query="doodh under 60",
        cleaned_query="milk",
        max_price=60.0,
        radius_km=3.0,
    )
    resolved = resolve_filters(
        parsed=parsed,
        ui_max_price=None,
        ui_radius_km=None,
    )
    assert resolved.search_text == "milk"
    assert resolved.max_price == 60.0
    assert resolved.radius_km == 3.0


def test_radius_defaults_to_none_when_unspecified():
    parsed = NormalizedQueryOutput(
        original_query="chocolate",
        cleaned_query="chocolate",
        radius_km=None,
    )
    resolved = resolve_filters(parsed=parsed)
    assert resolved.radius_km is None, "Radius must remain None unless explicitly provided"


def test_radius_preserved_when_explicitly_in_query():
    parsed = NormalizedQueryOutput(
        original_query="milk within 5km",
        cleaned_query="milk",
        radius_km=5.0,
    )
    resolved = resolve_filters(parsed=parsed)
    assert resolved.radius_km == 5.0


def test_invalid_price_range_raises_error():
    parsed = NormalizedQueryOutput(
        original_query="biscuit",
        cleaned_query="biscuit",
    )
    with pytest.raises(ValueError, match="cannot exceed max_price"):
        resolve_filters(
            parsed=parsed,
            ui_min_price=100.0,
            ui_max_price=50.0,
        )


def test_invalid_negative_radius_raises_error():
    parsed = NormalizedQueryOutput(
        original_query="biscuit",
        cleaned_query="biscuit",
    )
    with pytest.raises(ValueError, match="must be positive"):
        resolve_filters(
            parsed=parsed,
            ui_radius_km=-5.0,
        )
