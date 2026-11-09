"""
Integration Tests for ShopLens Search FastAPI Endpoints.
"""

import pytest
import httpx


@pytest.mark.anyio
async def test_get_search_products_exact(async_client: httpx.AsyncClient):
    response = await async_client.get(
        "/api/v1/search",
        params={
            "q": "chocolate",
            "latitude": 30.3256,
            "longitude": 78.0322,
            "radius_km": 15.0,
            "limit": 10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "chocolate"
    assert data["total_results"] > 0
    first_item = data["results"][0]
    assert "product_name" in first_item
    assert "brand" in first_item
    assert "sub_category_name" in first_item
    assert "net_quantity" in first_item
    assert "store" in first_item
    assert "distance_km" in first_item
    assert "score" in first_item
    assert len(first_item["sources"]) > 0


@pytest.mark.anyio
async def test_post_search_products_exact(async_client: httpx.AsyncClient):
    payload = {
        "query": "chocolate",
        "latitude": 30.3256,
        "longitude": 78.0322,
        "radius_km": 15.0,
        "limit": 10,
    }
    response = await async_client.post("/api/v1/search/products", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "chocolate"
    assert data["total_results"] > 0
    first_item = data["results"][0]
    assert "product_name" in first_item
    assert "brand" in first_item
    assert "sub_category_name" in first_item
    assert "net_quantity" in first_item
    assert "store" in first_item
    assert "distance_km" in first_item
    assert "score" in first_item
    assert len(first_item["sources"]) > 0


@pytest.mark.anyio
async def test_post_search_something_to_drink(async_client: httpx.AsyncClient):
    payload = {
        "query": "something to drink",
        "latitude": 30.3256,
        "longitude": 78.0322,
        "radius_km": 20.0,
        "limit": 10,
    }
    response = await async_client.post("/api/v1/search/products", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    allowed_categories = ["Drinks & Juices", "Dairy, Bread & Eggs", "Beverages"]
    for item in data["results"][:5]:
        assert item["category_name"] in allowed_categories, f"Unexpected category {item['category_name']} for drinks"


@pytest.mark.anyio
async def test_post_search_something_sweet(async_client: httpx.AsyncClient):
    payload = {
        "query": "something sweet",
        "latitude": 30.3256,
        "longitude": 78.0322,
        "radius_km": 20.0,
        "limit": 10,
    }
    response = await async_client.post("/api/v1/search/products", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    top_names = [item["product_name"].lower() for item in data["results"][:5]]
    # Ensure chips are excluded and sweet items are returned
    assert not any("chips" in n for n in top_names)
    assert any(
        w in " ".join(top_names)
        for w in ["chocolate", "biscuit", "sweet", "rusk", "sugar", "cookie", "cake", "ice cream"]
    )


@pytest.mark.anyio
async def test_post_search_household_things(async_client: httpx.AsyncClient):
    payload = {
        "query": "household things",
        "latitude": 30.3256,
        "longitude": 78.0322,
        "radius_km": 20.0,
        "limit": 10,
    }
    response = await async_client.post("/api/v1/search/products", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    top_categories = [item["category_name"] for item in data["results"][:5]]
    assert any("Cleaning & Household" in c for c in top_categories)


@pytest.mark.anyio
async def test_post_search_with_price_filter(async_client: httpx.AsyncClient):
    payload = {
        "query": "biscuit",
        "latitude": 30.3256,
        "longitude": 78.0322,
        "max_price": 50.0,
        "radius_km": 15.0,
        "limit": 10,
    }
    response = await async_client.post("/api/v1/search/products", json=payload)
    assert response.status_code == 200
    data = response.json()
    for item in data["results"]:
        assert item["price"] <= 50.0
