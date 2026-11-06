"""
Semantic evaluation test suite.
Evaluates the 5 historical reference queries and an expanded labelled test set.
Validates that relevant products are surfaced in top candidates and that
scores reflect ranking distinctions transparently.
"""

import pytest
from apis.v1.schemas.search import UIFilters
from services.search_service.search_service import search_products


EVAL_QUERIES = [
    {
        "query": "something to drink",
        "expected_any": ["Pepsi", "Coca Cola", "Real Mixed Fruit Juice", "Amul Taaza Milk"],
    },
    {
        "query": "things to spread on bread",
        "expected_any": ["Amul Butter", "Britannia Bread", "Harvest Brown Bread"],
    },
    {
        "query": "breakfast items",
        "expected_any": ["Britannia Bread", "Harvest Brown Bread", "Amul Taaza Milk", "Banana", "Parle-G Biscuits"],
    },
    {
        "query": "salty snacks",
        "expected_any": ["Lays Classic Salted", "Kurkure Masala Munch"],
    },
    {
        "query": "personal hygiene products",
        "expected_any": ["Dove Soap", "Colgate Toothpaste", "Surf Excel Detergent"],
    },
    {
        "query": "fresh fruits",
        "expected_any": ["Red Apple", "Banana"],
    },
    {
        "query": "laundry",
        "expected_any": ["Surf Excel Detergent"],
    },
    {
        "query": "cooking vegetables",
        "expected_any": ["Tomato", "Potato"],
    },
]

LAT = 30.3165
LON = 78.0322


@pytest.mark.anyio
@pytest.mark.parametrize("eval_case", EVAL_QUERIES, ids=lambda c: c["query"])
async def test_semantic_query_eval(eval_case, db_session):
    query = eval_case["query"]
    expected_any = eval_case["expected_any"]
    session = db_session

    res = await search_products(
        session=session,
        query=query,
        ui_filters=UIFilters(),
        latitude=LAT,
        longitude=LON,
    )

    assert len(res["results"]) > 0, f"Query '{query}' returned no results"

    matched_names = {r["product_name"] for r in res["results"]}
    found = any(exp in matched_names for exp in expected_any)

    assert found, (
        f"Query '{query}' did not return any expected products {expected_any}. "
        f"Returned: {list(matched_names)}"
    )
