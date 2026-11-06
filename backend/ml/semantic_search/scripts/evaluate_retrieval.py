"""
ShopLens Semantic Search Retrieval Evaluator.

Evaluates a SentenceTransformer model (pretrained or fine-tuned) against the
ShopLens catalog and held-out test (or validation) queries.
Properly handles multi-positive relevance sets, computing:
- Recall@5
- Recall@10
- Precision@5
- Mean Reciprocal Rank (MRR)
- NDCG@10
"""

import math
from pathlib import Path
from typing import Any
import pandas as pd
from sentence_transformers import SentenceTransformer

# Product catalog with exact attributes and descriptions as stored in PostgreSQL
CATALOG_PRODUCTS = {
    1: {
        "name": "Cadbury Dairy Milk Chocholate",
        "category": "Snacks",
        "description": "Milk chocolate bar.",
        "attributes": ["chocolate", "dairy-product", "snack", "sweet"],
    },
    2: {
        "name": "Cadbury 5 Star Chocolate",
        "category": "Snacks",
        "description": "Caramel chocolate bar.",
        "attributes": ["chocolate", "snack", "sweet"],
    },
    3: {
        "name": "Amul Taaza Milk",
        "category": "Dairy",
        "description": "Fresh toned milk.",
        "attributes": ["breakfast", "dairy-product", "drinkable"],
    },
    4: {
        "name": "Amul Butter",
        "category": "Dairy",
        "description": "Pasteurized table butter.",
        "attributes": ["cooking", "dairy-product", "spread"],
    },
    5: {
        "name": "Britannia Bread",
        "category": "Bakery",
        "description": "Fresh white bread.",
        "attributes": ["bakery-product", "bread", "breakfast"],
    },
    6: {
        "name": "Harvest Brown Bread",
        "category": "Bakery",
        "description": "Whole wheat brown bread.",
        "attributes": ["bakery-product", "bread", "breakfast", "whole-grain"],
    },
    7: {
        "name": "Parle-G Biscuits",
        "category": "Snacks",
        "description": "Classic glucose biscuits.",
        "attributes": ["biscuit", "breakfast", "snack", "sweet"],
    },
    8: {
        "name": "Oreo Biscuits",
        "category": "Snacks",
        "description": "Chocolate sandwich biscuits.",
        "attributes": ["biscuit", "chocolate", "snack", "sweet"],
    },
    9: {
        "name": "Lays Classic Salted",
        "category": "Snacks",
        "description": "Classic salted potato chips.",
        "attributes": ["savory-snack", "snack"],
    },
    10: {
        "name": "Kurkure Masala Munch",
        "category": "Snacks",
        "description": "Masala flavored snack.",
        "attributes": ["savory-snack", "snack"],
    },
    11: {
        "name": "Coca Cola",
        "category": "Beverages",
        "description": "Carbonated soft drink.",
        "attributes": ["cold-drink", "drinkable"],
    },
    12: {
        "name": "Pepsi",
        "category": "Beverages",
        "description": "Carbonated soft drink.",
        "attributes": ["cold-drink", "drinkable"],
    },
    13: {
        "name": "Real Mixed Fruit Juice",
        "category": "Beverages",
        "description": "Mixed fruit juice.",
        "attributes": ["drinkable", "fruit", "juice"],
    },
    14: {
        "name": "Red Apple",
        "category": "Fruits",
        "description": "Fresh red apple.",
        "attributes": ["fresh-produce", "fruit"],
    },
    15: {
        "name": "Banana",
        "category": "Fruits",
        "description": "Fresh bananas.",
        "attributes": ["breakfast", "fresh-produce", "fruit"],
    },
    16: {
        "name": "Tomato",
        "category": "Vegetables",
        "description": "Fresh tomatoes.",
        "attributes": ["cooking", "fresh-produce", "vegetable"],
    },
    17: {
        "name": "Potato",
        "category": "Vegetables",
        "description": "Fresh potatoes.",
        "attributes": ["cooking", "fresh-produce", "vegetable"],
    },
    18: {
        "name": "Dove Soap",
        "category": "Personal Care",
        "description": "Moisturizing bathing soap.",
        "attributes": ["bathing", "personal-care"],
    },
    19: {
        "name": "Colgate Toothpaste",
        "category": "Personal Care",
        "description": "Fluoride toothpaste.",
        "attributes": ["oral-care", "personal-care"],
    },
    20: {
        "name": "Surf Excel Detergent",
        "category": "Household",
        "description": "Laundry detergent.",
        "attributes": ["laundry-care"],
    },
}


def build_catalog_document_text(product_id: int) -> str:
    """Build the exact document text formatted identically to generate_product_embeddings.py."""
    p = CATALOG_PRODUCTS[product_id]
    attrs = sorted(p["attributes"])
    attrs_txt = ", ".join(attrs) if attrs else "None"
    return (
        f"Product: {p['name']}. "
        f"Description: {p['description']}. "
        f"Category: {p['category']}. "
        f"Attributes: {attrs_txt}."
    )


def load_ground_truth(csv_path: str | Path) -> dict[str, set[int]]:
    """Load query -> set of relevant positive product IDs."""
    df = pd.read_csv(csv_path)
    ground_truth: dict[str, set[int]] = {}
    for _, row in df.iterrows():
        q = str(row["query"]).strip()
        pos_id = int(row["positive_product_id"])
        if q not in ground_truth:
            ground_truth[q] = set()
        ground_truth[q].add(pos_id)
    return ground_truth


def compute_metrics(
    ranked_product_ids: list[int],
    relevant_product_ids: set[int],
) -> dict[str, float]:
    """
    Compute standard ranking metrics for a single query with multi-positive relevance.
    """
    if not relevant_product_ids:
        return {
            "recall@5": 0.0,
            "recall@10": 0.0,
            "precision@5": 0.0,
            "mrr": 0.0,
            "ndcg@10": 0.0,
        }

    # Recall@5 and Recall@10
    top5 = set(ranked_product_ids[:5])
    top10 = set(ranked_product_ids[:10])

    num_relevant = len(relevant_product_ids)
    recall5 = len(top5 & relevant_product_ids) / num_relevant
    recall10 = len(top10 & relevant_product_ids) / num_relevant
    precision5 = len(top5 & relevant_product_ids) / 5.0

    # MRR (first relevant product rank)
    mrr = 0.0
    for rank_idx, pid in enumerate(ranked_product_ids, start=1):
        if pid in relevant_product_ids:
            mrr = 1.0 / rank_idx
            break

    # NDCG@10 (binary relevance in multi-positive set)
    dcg = 0.0
    for i in range(min(10, len(ranked_product_ids))):
        pid = ranked_product_ids[i]
        rel = 1.0 if pid in relevant_product_ids else 0.0
        dcg += rel / math.log2(i + 2)  # i+2 because i is 0-indexed (rank 1 -> log2(2))

    idcg = 0.0
    for i in range(min(10, num_relevant)):
        idcg += 1.0 / math.log2(i + 2)

    ndcg10 = (dcg / idcg) if idcg > 0 else 0.0

    return {
        "recall@5": recall5,
        "recall@10": recall10,
        "precision@5": precision5,
        "mrr": mrr,
        "ndcg@10": ndcg10,
    }


def evaluate_model(
    model: SentenceTransformer,
    csv_path: str | Path,
    use_rich_text: bool = True,
) -> dict[str, Any]:
    """
    Evaluate a SentenceTransformer model on the queries from csv_path against all 20 catalog products.
    """
    ground_truth = load_ground_truth(csv_path)

    # 1. Encode all 20 products
    product_ids = sorted(CATALOG_PRODUCTS.keys())
    if use_rich_text:
        product_texts = [build_catalog_document_text(pid) for pid in product_ids]
    else:
        product_texts = [CATALOG_PRODUCTS[pid]["name"] for pid in product_ids]

    product_embeddings = model.encode(
        product_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    # 2. Encode all queries
    queries = list(ground_truth.keys())
    query_embeddings = model.encode(
        queries,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    all_metrics: list[dict[str, float]] = []
    query_details: list[dict[str, Any]] = []

    for q, q_emb in zip(queries, query_embeddings):
        rel_ids = ground_truth[q]

        # Dot product of normalized vectors = cosine similarity
        similarities = [float(q_emb @ p_emb) for p_emb in product_embeddings]

        # Rank product IDs by descending similarity
        scored = list(zip(product_ids, similarities))
        scored.sort(key=lambda x: x[1], reverse=True)
        ranked_ids = [pid for pid, _ in scored]

        m = compute_metrics(ranked_ids, rel_ids)
        all_metrics.append(m)

        # Store top 5 details
        top5_info = [
            (pid, CATALOG_PRODUCTS[pid]["name"], round(sim, 4), pid in rel_ids)
            for pid, sim in scored[:5]
        ]
        query_details.append({
            "query": q,
            "relevant_ids": sorted(list(rel_ids)),
            "relevant_names": [CATALOG_PRODUCTS[pid]["name"] for pid in sorted(list(rel_ids))],
            "top5": top5_info,
            "metrics": m,
        })

    # Macro-average across queries
    avg_metrics = {
        "recall@5": sum(m["recall@5"] for m in all_metrics) / len(all_metrics),
        "recall@10": sum(m["recall@10"] for m in all_metrics) / len(all_metrics),
        "precision@5": sum(m["precision@5"] for m in all_metrics) / len(all_metrics),
        "mrr": sum(m["mrr"] for m in all_metrics) / len(all_metrics),
        "ndcg@10": sum(m["ndcg@10"] for m in all_metrics) / len(all_metrics),
    }

    return {
        "summary": avg_metrics,
        "query_details": query_details,
        "total_queries": len(queries),
    }


if __name__ == "__main__":
    import json
    import os

    # Allow offline execution if explicitly set by environment
    if os.environ.get("HF_HUB_OFFLINE") is None:
        pass
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    test_csv = Path("backend/ml/semantic_search/datasets/test.csv")
    results = evaluate_model(model, test_csv)
    print("Baseline Test Evaluation Results:")
    print(json.dumps(results["summary"], indent=2))
