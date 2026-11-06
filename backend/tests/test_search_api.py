"""
API regression tests for FastAPI /api/v1/search endpoint.
Verifies HTTP status codes, query validation, and response contracts using httpx.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from db.database import get_db


LAT = 30.3165
LON = 78.0322


@pytest.mark.anyio
async def test_search_api_requires_location():
    # Location (latitude & longitude) is mandatory for consumer search
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Omitting latitude and longitude should result in 422 Unprocessable Entity
        response = await client.get("/api/v1/search", params={"q": "milk"})
        assert response.status_code == 422


@pytest.mark.anyio
async def test_search_api_exact_match(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/search",
                params={
                    "q": "Amul Butter",
                    "latitude": LAT,
                    "longitude": LON,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "amul butter"
            assert isinstance(data["results"], list)
            assert len(data["results"]) > 0

            first = data["results"][0]
            assert first["product_name"] == "Amul Butter"
            assert first["score"] == 1.0
            assert "store" in first
            assert "distance_km" in first
            assert "price" in first
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_search_api_semantic_search(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/search",
                params={
                    "q": "something to drink",
                    "latitude": LAT,
                    "longitude": LON,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) > 0

            # Must contain drinks
            product_names = [r["product_name"] for r in data["results"]]
            assert any(p in ("Pepsi", "Coca Cola", "Real Mixed Fruit Juice", "Amul Taaza Milk") for p in product_names)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_search_api_filters_applied(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/search",
                params={
                    "q": "chocolate",
                    "latitude": LAT,
                    "longitude": LON,
                    "max_price": 50.0,
                    "radius_km": 5.0,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["filters"]["max_price"] == 50.0
            assert data["filters"]["radius_km"] == 5.0

            for item in data["results"]:
                assert item["price"] <= 50.0
                assert item["distance_km"] <= 5.0
    finally:
        app.dependency_overrides.clear()
