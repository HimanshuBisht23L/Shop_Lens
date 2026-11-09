"""
Automated Pytest Suite for Search V2 10-Query Evaluation Benchmark.
Validates production-grade accuracy:
- Zero non-matching category leakage on Type A specific queries.
- Broad semantic discovery on Type B conceptual queries.
- Strict filter enforcement (price, brand, sub-category).
"""

import pytest
import httpx

USER_LAT = 30.3256
USER_LON = 78.0322
RADIUS_KM = 15.0


@pytest.mark.anyio
async def test_eval_tc01_exact_search(async_client: httpx.AsyncClient):
    """
    TC-01: 'chocolate'
    Must activate Type A entity gate for 'Chocolates & Candies'.
    Zero non-matching category leakage!
    """
    resp = await async_client.post(
        "/api/v1/search/products",
        json={"query": "chocolate", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_results"] > 0
    # Every result MUST belong to Chocolates
    for item in data["results"]:
        assert item["sub_category_name"] == "Chocolates", (
            f"Leakage detected: {item['product_name']} is in {item['sub_category_name']}"
        )


@pytest.mark.anyio
async def test_eval_tc02_product_name_search(async_client: httpx.AsyncClient):
    """
    TC-02: 'cadbury dairy milk'
    Matches Cadbury Dairy Milk Silk with phrase precedence over single token 'milk'.
    """
    resp = await async_client.post(
        "/api/v1/search/products",
        json={"query": "cadbury dairy milk", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_results"] > 0
    top_item = data["results"][0]
    assert "Dairy Milk" in top_item["product_name"]
    assert top_item["brand"] == "Cadbury"
    assert top_item["sub_category_name"] == "Chocolates"


@pytest.mark.anyio
async def test_eval_tc03_misspelled_fuzzy_search(async_client: httpx.AsyncClient):
    """
    TC-03: 'choclate'
    Fuzzy matching resolves typo to 'Chocolates'. Zero leakage.
    """
    resp = await async_client.post(
        "/api/v1/search/products",
        json={"query": "choclate", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_results"] > 0
    for item in data["results"]:
        assert item["sub_category_name"] == "Chocolates"


@pytest.mark.anyio
async def test_eval_tc04_semantic_search(async_client: httpx.AsyncClient):
    """
    TC-04: 'sweet things'
    Broad conceptual query (Type B) retrieves sweet products across categories (chocolates, biscuits).
    """
    resp = await async_client.post(
        "/api/v1/search/products",
        json={"query": "sweet things", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_results"] > 0
    top_names = [r["product_name"].lower() for r in data["results"][:3]]
    assert any(
        w in " ".join(top_names)
        for w in ["chocolate", "biscuit", "star", "silk", "oreo", "parle"]
    )


@pytest.mark.anyio
async def test_eval_tc05_hinglish_translation(async_client: httpx.AsyncClient):
    """
    TC-05: 'doodh'
    Hinglish normalizer maps 'doodh' -> 'milk'.
    """
    resp = await async_client.post(
        "/api/v1/search/products",
        json={"query": "doodh", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["applied_filters"]["hinglish_mapped"].get("doodh") == "milk"
    assert data["total_results"] > 0
    top_names = [r["product_name"] for r in data["results"]]
    assert any("Milk" in n for n in top_names)


@pytest.mark.anyio
async def test_eval_tc06_price_filter_extraction(async_client: httpx.AsyncClient):
    """
    TC-06: 'cake under 500'
    Extracts max_price <= 500.0.
    """
    resp = await async_client.post(
        "/api/v1/search/products",
        json={"query": "cake under 500", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["applied_filters"]["max_price"] == 500.0
    for r in data["results"]:
        assert r["price"] <= 500.0


@pytest.mark.anyio
async def test_eval_tc07_brand_search(async_client: httpx.AsyncClient):
    """
    TC-07: 'amul milk'
    Gated to Brand='Amul' and SubCategory='Milk'.
    """
    resp = await async_client.post(
        "/api/v1/search/products",
        json={"query": "amul milk", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_results"] > 0
    top_item = data["results"][0]
    assert "Amul" in top_item["product_name"] and "Milk" in top_item["product_name"]
    assert top_item["brand"] == "Amul"
    assert top_item["sub_category_name"] == "Milk"


@pytest.mark.anyio
async def test_eval_tc08_category_search(async_client: httpx.AsyncClient):
    """
    TC-08: 'dairy products'
    Retrieves dairy items.
    """
    resp = await async_client.post(
        "/api/v1/search/products",
        json={"query": "dairy products", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp.status_code == 200
    data = resp.json()
    top_names = [r["product_name"] for r in data["results"][:3]]
    assert any("Milk" in n or "Butter" in n for n in top_names)


@pytest.mark.anyio
async def test_eval_tc09_location_search(async_client: httpx.AsyncClient):
    """
    TC-09: 'chocolate near me'
    Normalizer strips 'near me' filler tokens; preserves strict chocolate gating.
    """
    resp = await async_client.post(
        "/api/v1/search/products",
        json={"query": "chocolate near me", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "near me" not in data["normalized_query"]
    assert data["total_results"] > 0
    for item in data["results"]:
        assert item["sub_category_name"] == "Chocolates"


@pytest.mark.anyio
async def test_eval_tc10_combined_query(async_client: httpx.AsyncClient):
    """
    TC-10: 'amul doodh under 30'
    Amul pouch milks are priced at Rs 48 to 66.
    Asserts strict enforcement of price constraint: 0 items returned when price threshold is lower than catalog price.
    """
    resp = await async_client.post(
        "/api/v1/search/products",
        json={"query": "amul doodh under 30", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["applied_filters"]["max_price"] == 30.0
    assert "milk" in data["normalized_query"]
    assert data["total_results"] == 0, (
        f"Expected 0 results for Amul Milk under Rs 30 (minimum catalog price is Rs 32/48), got {data['total_results']}"
    )

    # Now verify that raising price ceiling to 70 correctly returns the item
    resp_70 = await async_client.post(
        "/api/v1/search/products",
        json={"query": "amul doodh under 70", "latitude": USER_LAT, "longitude": USER_LON, "radius_km": RADIUS_KM},
    )
    assert resp_70.status_code == 200
    data_70 = resp_70.json()
    assert data_70["total_results"] > 0
    assert data_70["results"][0]["price"] <= 70.0
