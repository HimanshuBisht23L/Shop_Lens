"""
Integration tests for ShopLens search pipeline with the database.
Tests all retrieval stages: keyword, fuzzy, semantic, fusion, inventory/PostGIS filtering.
"""

import pytest
from apis.v1.schemas.search import UIFilters
from services.search_flow.keyword_search import keyword_search
from services.search_flow.fuzzy_search import fuzzy_search
from services.search_flow.semantic_search import semantic_search
from services.search_service.search_service import search_products


# Reference coordinates (e.g. Dehradun center)
LAT = 30.3165
LON = 78.0322


@pytest.mark.anyio
async def test_keyword_search_exact_and_partial(db_session):
    session = db_session
    # Exact name match
    exact_results = await keyword_search(session, "Amul Butter")
    assert len(exact_results) >= 1
    assert any(p.name == "Amul Butter" for p in exact_results)

    # Partial name match
    partial_results = await keyword_search(session, "Cadbury")
    assert len(partial_results) >= 2
    names = [p.name for p in partial_results]
    assert any("Cadbury 5 Star" in n for n in names)
    assert any("Cadbury Dairy Milk" in n for n in names)

    # No match
    no_match = await keyword_search(session, "CompletelyNonExistentItem12345")
    assert len(no_match) == 0

    # Empty / whitespace
    assert await keyword_search(session, "") == []
    assert await keyword_search(session, "   ") == []


@pytest.mark.anyio
async def test_fuzzy_search_typo_correction(db_session):
    session = db_session
    # Typo: 'chocholate' matches Cadbury chocolates
    fuzzy_results = await fuzzy_search(session, "chocholate", limit=10)
    assert len(fuzzy_results) > 0
    products = [item[0] for item in fuzzy_results]
    scores = [float(item[1]) for item in fuzzy_results]

    # Top result should have similarity >= FUZZY_THRESHOLD (0.25)
    assert scores[0] >= 0.25
    assert any("Chocolate" in p.name or "Chocholate" in p.name for p in products)

    # Empty query
    assert await fuzzy_search(session, "") == []


@pytest.mark.anyio
async def test_semantic_search_retrieval_and_ordering(db_session):
    session = db_session
    # Semantic query with no exact keyword
    results = await semantic_search(session, "something to drink", limit=10)
    assert len(results) > 0

    # Similarity scores must be descending
    similarities = [float(r[1]) for r in results]
    assert similarities == sorted(similarities, reverse=True)

    # Top items should include beverages like Pepsi or Coca Cola
    top_names = [r[0].name for r in results[:3]]
    assert any(n in ("Pepsi", "Coca Cola", "Real Mixed Fruit Juice") for n in top_names)

    # Empty query returns empty
    assert await semantic_search(session, "") == []
    assert await semantic_search(session, "   ") == []


@pytest.mark.anyio
async def test_search_products_exact_match_end_to_end(db_session):
    session = db_session
    res = await search_products(
        session=session,
        query="Amul Butter",
        ui_filters=UIFilters(),
        latitude=LAT,
        longitude=LON,
    )

    assert "results" in res
    assert "query" in res
    assert "filters" in res
    assert res["query"] == "amul butter"

    results = res["results"]
    assert len(results) > 0

    # Exact match should have top candidate score 1.00
    first_item = results[0]
    assert first_item["product_name"] == "Amul Butter"
    assert first_item["score"] == 1.00
    assert "store" in first_item
    assert "distance_km" in first_item
    assert first_item["is_available"] is True
    assert first_item["quantity"] > 0



@pytest.mark.anyio
async def test_search_products_semantic_only_end_to_end(db_session):
    res = await search_products(
        session=db_session,
        query="something to drink",
        ui_filters=UIFilters(),
        latitude=LAT,
        longitude=LON,
    )

    assert len(res["results"]) > 0

    # Relevant beverages must be returned.
    product_names = [r["product_name"] for r in res["results"]]

    assert any(
        p in (
            "Pepsi",
            "Coca Cola",
            "Real Mixed Fruit Juice",
            "Amul Taaza Milk",
        )
        for p in product_names
    )

    # All results must have valid relevance scores and distances.
    for item in res["results"]:
        assert 0.0 <= item["score"] <= 1.0
        assert item["distance_km"] >= 0

    # Results must be ordered by relevance score descending.
    scores = [r["score"] for r in res["results"]]

    assert scores == sorted(scores, reverse=True)

    # When the same product appears at multiple stores,
    # its stores should be ordered by distance ascending.
    product_ids = {
        item["product_id"]
        for item in res["results"]
    }

    for product_id in product_ids:
        product_rows = [
            item
            for item in res["results"]
            if item["product_id"] == product_id
        ]

        distances = [
            item["distance_km"]
            for item in product_rows
        ]

        assert distances == sorted(distances)



@pytest.mark.anyio
async def test_search_products_price_filter(db_session):
    session = db_session
    # Price constraint: max_price = 50.0
    res = await search_products(
        session=session,
        query="chocolate",
        ui_filters=UIFilters(max_price=50.0),
        latitude=LAT,
        longitude=LON,
    )

    for item in res["results"]:
        assert item["price"] <= 50.0

    # Price constraint: min_price = 40.0
    res_min = await search_products(
        session=session,
        query="bread",
        ui_filters=UIFilters(min_price=40.0),
        latitude=LAT,
        longitude=LON,
    )

    for item in res_min["results"]:
        assert item["price"] >= 40.0


@pytest.mark.anyio
async def test_search_products_radius_filter(db_session):
    session = db_session
    # Search with tight radius: 1 km
    res = await search_products(
        session=session,
        query="milk",
        ui_filters=UIFilters(radius_km=1.0),
        latitude=LAT,
        longitude=LON,
    )

    for item in res["results"]:
        assert item["distance_km"] <= 1.0


@pytest.mark.anyio
async def test_search_products_empty_query(db_session):
    session = db_session
    res = await search_products(
        session=session,
        query="   ",
        ui_filters=UIFilters(),
        latitude=LAT,
        longitude=LON,
    )

    assert res["results"] == []
    assert res["query"] == ""


@pytest.mark.anyio
async def test_search_products_response_contract_fields(db_session):
    session = db_session
    res = await search_products(
        session=session,
        query="Dove Soap",
        ui_filters=UIFilters(),
        latitude=LAT,
        longitude=LON,
    )

    assert set(res.keys()) == {"query", "filters", "results"}
    assert set(res["filters"].keys()) == {"min_price", "max_price", "radius_km"}

    if res["results"]:
        item = res["results"][0]
        required_fields = {
            "product_id",
            "product_name",
            "description",
            "price",
            "quantity",
            "is_available",
            "store",
            "distance_km",
            "score",
        }
        assert required_fields.issubset(set(item.keys()))
        assert set(item["store"].keys()) == {"id", "name", "address"}
