"""
Automated validation test suite for semantic search training datasets.
Tests all 10 dataset requirements from ShopLens Training Dataset Requirement specification.
"""

from pathlib import Path
import pandas as pd
import pytest


DATASET_DIR = Path(__file__).resolve().parent.parent / "ml" / "semantic_search" / "datasets"

EXPECTED_COLUMNS = [
    "query",
    "positive_product_id",
    "positive_product_name",
    "negative_product_id",
    "negative_product_name",
]

# Database catalog snapshot (exact names)
DB_CATALOG = {
    1: "Cadbury Dairy Milk Chocholate",
    2: "Cadbury 5 Star Chocolate",
    3: "Amul Taaza Milk",
    4: "Amul Butter",
    5: "Britannia Bread",
    6: "Harvest Brown Bread",
    7: "Parle-G Biscuits",
    8: "Oreo Biscuits",
    9: "Lays Classic Salted",
    10: "Kurkure Masala Munch",
    11: "Coca Cola",
    12: "Pepsi",
    13: "Real Mixed Fruit Juice",
    14: "Red Apple",
    15: "Banana",
    16: "Tomato",
    17: "Potato",
    18: "Dove Soap",
    19: "Colgate Toothpaste",
    20: "Surf Excel Detergent",
}


def test_dataset_files_exist():
    assert (DATASET_DIR / "train.csv").is_file(), "train.csv missing"
    assert (DATASET_DIR / "validation.csv").is_file(), "validation.csv missing"
    assert (DATASET_DIR / "test.csv").is_file(), "test.csv missing"
    assert (DATASET_DIR / "dataset_review.csv").is_file(), "dataset_review.csv missing"


def test_csv_schemas_and_columns():
    for name in ["train.csv", "validation.csv", "test.csv"]:
        df = pd.read_csv(DATASET_DIR / name)
        assert list(df.columns) == EXPECTED_COLUMNS, f"{name} columns do not match required schema"
        assert len(df) > 0, f"{name} is empty"

    df_review = pd.read_csv(DATASET_DIR / "dataset_review.csv")
    assert list(df_review.columns) == EXPECTED_COLUMNS + ["review_reason", "recommended_action"]
    assert len(df_review) > 0


def test_referenced_products_exist_and_match_database():
    for name in ["train.csv", "validation.csv", "test.csv"]:
        df = pd.read_csv(DATASET_DIR / name)
        for _, row in df.iterrows():
            pos_id = row["positive_product_id"]
            pos_name = row["positive_product_name"]
            neg_id = row["negative_product_id"]
            neg_name = row["negative_product_name"]

            assert pos_id in DB_CATALOG, f"Unknown positive_product_id {pos_id} in {name}"
            assert neg_id in DB_CATALOG, f"Unknown negative_product_id {neg_id} in {name}"
            assert pos_name == DB_CATALOG[pos_id], f"Positive name mismatch for ID {pos_id} in {name}"
            assert neg_name == DB_CATALOG[neg_id], f"Negative name mismatch for ID {neg_id} in {name}"


def test_positive_and_negative_are_distinct():
    for name in ["train.csv", "validation.csv", "test.csv"]:
        df = pd.read_csv(DATASET_DIR / name)
        for _, row in df.iterrows():
            assert row["positive_product_id"] != row["negative_product_id"], (
                f"Positive and negative product IDs are identical for query '{row['query']}' in {name}"
            )


def test_no_duplicate_pairs_within_splits():
    for name in ["train.csv", "validation.csv", "test.csv"]:
        df = pd.read_csv(DATASET_DIR / name)
        duplicates = df.duplicated(subset=["query", "positive_product_id", "negative_product_id"])
        assert not duplicates.any(), f"Found duplicate training pairs in {name}"


def test_no_contradictory_labels():
    # A product cannot be both positive and negative for the exact same query
    for name in ["train.csv", "validation.csv", "test.csv"]:
        df = pd.read_csv(DATASET_DIR / name)
        grouped = df.groupby("query")
        for q, group in grouped:
            pos_ids = set(group["positive_product_id"])
            neg_ids = set(group["negative_product_id"])
            overlap = pos_ids.intersection(neg_ids)
            assert not overlap, f"Contradictory labels in {name} for query '{q}': {overlap}"


def test_no_query_leakage_across_splits():
    df_train = pd.read_csv(DATASET_DIR / "train.csv")
    df_val = pd.read_csv(DATASET_DIR / "validation.csv")
    df_test = pd.read_csv(DATASET_DIR / "test.csv")

    train_queries = set(df_train["query"])
    val_queries = set(df_val["query"])
    test_queries = set(df_test["query"])

    assert len(train_queries.intersection(val_queries)) == 0, "Query leakage between train and validation"
    assert len(train_queries.intersection(test_queries)) == 0, "Query leakage between train and test"
    assert len(val_queries.intersection(test_queries)) == 0, "Query leakage between validation and test"


def test_dataset_split_proportions():
    df_train = pd.read_csv(DATASET_DIR / "train.csv")
    df_val = pd.read_csv(DATASET_DIR / "validation.csv")
    df_test = pd.read_csv(DATASET_DIR / "test.csv")

    total_queries = len(set(df_train["query"])) + len(set(df_val["query"])) + len(set(df_test["query"]))
    train_pct = len(set(df_train["query"])) / total_queries
    val_pct = len(set(df_val["query"])) / total_queries
    test_pct = len(set(df_test["query"])) / total_queries

    # Proportions should be approximately 70% / 15% / 15% (within 5% tolerance)
    assert 0.60 <= train_pct <= 0.75, f"Train query proportion unexpected: {train_pct:.2f}"
    assert 0.10 <= val_pct <= 0.20, f"Val query proportion unexpected: {val_pct:.2f}"
    assert 0.10 <= test_pct <= 0.20, f"Test query proportion unexpected: {test_pct:.2f}"


def test_surf_excel_not_labeled_personal_hygiene():
    for name in ["train.csv", "validation.csv", "test.csv"]:
        df = pd.read_csv(DATASET_DIR / name)
        for _, row in df.iterrows():
            q_lower = row["query"].lower()
            if any(term in q_lower for term in ["personal hygiene", "personal care", "shower", "bath soap", "body wash"]):
                assert row["positive_product_id"] != 20, (
                    f"Surf Excel Detergent (ID 20) incorrectly marked positive for personal hygiene query: '{row['query']}' in {name}"
                )


def test_multi_positive_query_counts():
    df_train = pd.read_csv(DATASET_DIR / "train.csv")
    df_val = pd.read_csv(DATASET_DIR / "validation.csv")
    df_test = pd.read_csv(DATASET_DIR / "test.csv")

    train_multi = (df_train.groupby("query")["positive_product_id"].nunique() > 1).sum()
    val_multi = (df_val.groupby("query")["positive_product_id"].nunique() > 1).sum()
    test_multi = (df_test.groupby("query")["positive_product_id"].nunique() > 1).sum()

    assert train_multi == 47, f"Expected 47 train multi-positive queries, got {train_multi}"
    assert val_multi == 10, f"Expected 10 val multi-positive queries, got {val_multi}"
    assert test_multi == 9, f"Expected 9 test multi-positive queries, got {test_multi}"
    assert train_multi + val_multi + test_multi == 66


def test_reviewed_questionable_pairs_absent_from_positives():
    df_review = pd.read_csv(DATASET_DIR / "dataset_review.csv")
    all_df = pd.concat([
        pd.read_csv(DATASET_DIR / "train.csv"),
        pd.read_csv(DATASET_DIR / "validation.csv"),
        pd.read_csv(DATASET_DIR / "test.csv"),
    ], ignore_index=True)

    for _, row in df_review.iterrows():
        rq = row["query"]
        r_pos_id = row["positive_product_id"]
        # Confirm this questionable query-positive pair is never used as a positive in any split
        matched = all_df[(all_df["query"] == rq) & (all_df["positive_product_id"] == r_pos_id)]
        assert len(matched) == 0, (
            f"Questionable pair ('{rq}', product_id={r_pos_id}) was found as positive in the dataset!"
        )

