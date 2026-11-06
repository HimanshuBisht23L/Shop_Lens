# ShopLens — Semantic Search Dataset Statistics & Validation Report

## 1. Executive Summary

This document reports the comprehensive recalculated statistics, coverage metrics, and validation results for the refined ShopLens semantic search dataset, prepared for fine-tuning `sentence-transformers/all-MiniLM-L6-v2`.

- **Total Validated Training Triples**: 351
- **Total Unique Search Queries**: 159
- **Catalog Product Coverage**: 20 / 20 products (100%)
- **Split Proportions**: Train 67.5% (237 triples across 107 queries) | Validation 17.1% (60 triples across 26 queries) | Test 15.4% (54 triples across 26 queries)
- **Multi-Positive Queries**: **66 queries total (41.5%)**
  - Train: **47** multi-positive queries (43.9% of train queries)
  - Validation: **10** multi-positive queries (38.5% of validation queries)
  - Test: **9** multi-positive queries (34.6% of test queries)
- **Single-Positive Queries**: **93 queries total (58.5%)**
  - Train: **60** single-positive queries
  - Validation: **16** single-positive queries
  - Test: **17** single-positive queries
- **Positives Per Query**: Range 1 to 5 (Average: 1.62 overall | Train: 1.64 | Val: 1.69 | Test: 1.42)
- **Borderline / Ambiguous Examples Flagged for Review**: 14 examples (100% confirmed absent from positive sets)
- **Cross-Split Query Leakage**: **0%** (Strict query-grouped partition verified)
- **Contradictory Labels (Pos ∩ Neg for same query)**: **0**
- **Data Integrity & Consistency Errors**: **0**

---

## 2. Dataset Split Breakdown

| Split | Total Triples | % of Triples | Unique Queries | % of Queries | Multi-Positive Queries | Single-Positive Queries | Multi-Positive % | Avg Pos / Query |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train (`train.csv`)** | 237 | 67.5% | 107 | 67.3% | **47** | 60 | 43.9% | 1.64 |
| **Validation (`validation.csv`)** | 60 | 17.1% | 26 | 16.4% | **10** | 16 | 38.5% | 1.69 |
| **Test (`test.csv`)** | 54 | 15.4% | 26 | 16.4% | **9** | 17 | 34.6% | 1.42 |
| **Total** | **351** | **100.0%** | **159** | **100.0%** | **66** | **93** | **41.5%** | **1.62** |

*Note: Multi-positive queries are defined as search queries associated with more than one distinct positive product candidate (e.g. `something to drink` maps to Coca Cola, Pepsi, Real Fruit Juice, and Amul Taaza Milk).*

---

## 3. Category & Domain Distribution

Queries were stratified by category across splits to ensure balanced domain representation:

| Domain Category | Total Queries | Train Queries | Val Queries | Test Queries | Total Triples | Train Triples | Val Triples | Test Triples |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Bakery** | 11 | 7 | 2 | 2 | 22 | 14 | 4 | 4 |
| **Beverages** | 14 | 10 | 2 | 2 | 31 | 21 | 6 | 4 |
| **Breakfast** | 11 | 7 | 2 | 2 | 30 | 22 | 4 | 4 |
| **Cooking** | 7 | 5 | 1 | 1 | 17 | 12 | 3 | 2 |
| **Dairy** | 13 | 9 | 2 | 2 | 26 | 18 | 4 | 4 |
| **Fruits** | 13 | 9 | 2 | 2 | 26 | 18 | 4 | 4 |
| **General Grocery** | 10 | 6 | 2 | 2 | 35 | 22 | 7 | 6 |
| **Laundry** | 10 | 6 | 2 | 2 | 20 | 12 | 4 | 4 |
| **Oral Care** | 11 | 7 | 2 | 2 | 22 | 14 | 4 | 4 |
| **Personal Care** | 11 | 7 | 2 | 2 | 22 | 14 | 4 | 4 |
| **Salty Snacks** | 12 | 8 | 2 | 2 | 24 | 16 | 4 | 4 |
| **Spreads** | 9 | 7 | 1 | 1 | 19 | 15 | 2 | 2 |
| **Sweet Snacks** | 14 | 10 | 2 | 2 | 31 | 21 | 6 | 4 |
| **Vegetables** | 13 | 9 | 2 | 2 | 26 | 18 | 4 | 4 |
| **Total** | **159** | **107** | **26** | **26** | **351** | **237** | **60** | **54** |

---

## 4. Product Catalog Coverage

Every product in the ShopLens catalog is represented as both positive and negative candidates across the dataset:

| Product ID | Product Name | Category | Train (Pos/Neg) | Val (Pos/Neg) | Test (Pos/Neg) | Total Positives | Total Negatives | Total Appearances |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
|  1 | Cadbury Dairy Milk Chocholate | Snacks | 8 / 7 | 2 / 2 | 0 / 2 | 10 | 11 | 21 |
|  2 | Cadbury 5 Star Chocolate | Snacks | 5 / 4 | 3 / 0 | 0 / 1 | 8 | 5 | 13 |
|  3 | Amul Taaza Milk | Dairy | 16 / 5 | 5 / 1 | 3 / 4 | 24 | 10 | 34 |
|  4 | Amul Butter | Dairy | 28 / 5 | 5 / 1 | 6 / 4 | 39 | 10 | 49 |
|  5 | Britannia Bread | Bakery | 14 / 9 | 2 / 2 | 3 / 0 | 19 | 11 | 30 |
|  6 | Harvest Brown Bread | Bakery | 14 / 4 | 3 / 0 | 3 / 0 | 20 | 4 | 24 |
|  7 | Parle-G Biscuits | Snacks | 6 / 9 | 5 / 1 | 1 / 1 | 12 | 11 | 23 |
|  8 | Oreo Biscuits | Snacks | 8 / 9 | 1 / 2 | 3 / 1 | 12 | 12 | 24 |
|  9 | Lays Classic Salted | Snacks | 11 / 13 | 2 / 6 | 3 / 2 | 16 | 21 | 37 |
| 10 | Kurkure Masala Munch | Snacks | 9 / 6 | 3 / 4 | 3 / 3 | 15 | 13 | 28 |
| 11 | Coca Cola | Beverages | 7 / 14 | 2 / 2 | 3 / 3 | 12 | 19 | 31 |
| 12 | Pepsi | Beverages | 7 / 10 | 2 / 3 | 2 / 1 | 11 | 14 | 25 |
| 13 | Real Mixed Fruit Juice | Beverages | 9 / 3 | 1 / 1 | 0 / 0 | 10 | 4 | 14 |
| 14 | Red Apple | Fruits | 11 / 5 | 1 / 4 | 3 / 2 | 15 | 11 | 26 |
| 15 | Banana | Fruits | 15 / 5 | 3 / 0 | 5 / 2 | 23 | 7 | 30 |
| 16 | Tomato | Vegetables | 13 / 9 | 6 / 3 | 2 / 5 | 21 | 17 | 38 |
| 17 | Potato | Vegetables | 16 / 17 | 2 / 2 | 2 / 1 | 20 | 20 | 40 |
| 18 | Dove Soap | Personal Care | 12 / 43 | 4 / 13 | 4 / 10 | 20 | 66 | 86 |
| 19 | Colgate Toothpaste | Personal Care | 16 / 22 | 4 / 6 | 4 / 5 | 24 | 33 | 57 |
| 20 | Surf Excel Detergent | Household | 12 / 38 | 4 / 7 | 4 / 7 | 20 | 52 | 72 |

---

## 5. Query Leakage & Integrity Verification

1. **Query Leakage Verification**:
   - Train ∩ Validation: **0 queries**
   - Train ∩ Test: **0 queries**
   - Validation ∩ Test: **0 queries**
   - *Result*: **100% strict query isolation.**

2. **Label Contradiction Check**:
   - For every query, the set of positive product IDs and negative product IDs was verified to have zero intersection across all splits.
   - *Result*: **0 contradictory labels.**

3. **Duplicate Pair Check**:
   - Within each split, every `(query, positive_product_id, negative_product_id)` triple was checked for uniqueness.
   - *Result*: **0 duplicate triples.**

4. **Negative Quality Check**:
   - Every negative product was checked to ensure it is not in the set of valid positive products for that query.
   - Hard negatives were explicitly structured to teach the model subtle boundaries (e.g. White Bread vs Brown Bread, Raw Potato vs Potato Chips, Bath Soap vs Laundry Detergent, Bread vs Butter Spread).

5. **Review Query Exclusion Check**:
   - All 14 questionable positive pairs documented in `dataset_review.csv` were checked against `train.csv`, `validation.csv`, and `test.csv`.
   - *Result*: **0 questionable pairs appear as positive labels in any dataset.**

---

## 6. Review Dataset Summary (`dataset_review.csv`)

14 borderline or ambiguous cases were isolated for review. Highlights:

1. **`personal hygiene products` → Surf Excel Detergent**: Rejected as positive. Corrected to Laundry/Household.
2. **`things to spread on bread` → Britannia Bread**: Rejected as positive. Bread is the substrate; butter is the spread.
3. **`cooking oil`**: Marked as unsupported intent (no cooking oil exists in the 20-product catalog).
4. **`oral hygiene` → Dove Soap**: Rejected as positive. Dove is bathing soap; Colgate is oral care.
5. **`healthy diet snack` → Cadbury Chocolate**: Rejected as positive. Fresh fruits (Apple, Banana) are the true healthy snacks.
6. **`dishwashing liquid` & `hair shampoo`**: Documented as unsupported query intents.
7. **`breakfast items` → Real Mixed Fruit Juice**: Excluded from primary breakfast training pairs until attribute taxonomy is expanded.
8. **`dairy items` → Cadbury Chocolate**: Excluded from dairy items queries; kept positive strictly on Amul Milk and Amul Butter.

---

## 7. Known Scope Limitations & Guidance

1. **Catalog Scale**: The dataset reflects the active 20-product catalog. When the store catalog expands, query generation should be rerun using `generate_datasets.py`.
2. **Recommended Training Objective**: Use `MultipleNegativesRankingLoss` (MNRL) or `TripletLoss` with small batch size (16) and a conservative learning rate ($2 \times 10^{-5}$).
3. **Test Set Protection**: The `test.csv` split is preserved as an independent test set and must NOT be used for gradient updates or early stopping.
