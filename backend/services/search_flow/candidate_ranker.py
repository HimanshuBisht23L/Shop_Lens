"""
Candidate Ranker and Fusion Module for ShopLens Search.

Combines retrieval candidates from three heterogeneous channels:
1. Exact / Substring Keyword Search (SQL ILIKE)
2. Fuzzy Trigram Search (PostgreSQL pg_trgm similarity)
3. Semantic Vector Search (Sentence Transformers + pgvector cosine similarity)

Key Principles:
- Scales are calibrated independently before fusion.
- Exact product name matches are guaranteed the top score (1.00).
- Misspellings via fuzzy search are ranked above unrelated semantic tail items.
- Natural-language queries without keyword matches surface semantic candidates.
- Admin-managed product attributes provide a gentle relevance signal (+0.05)
  without acting as hard filters.
- Channel corroboration gives a bonus when multiple sources retrieve a product.
- Weak semantic noise is pruned when strong keyword/fuzzy matches exist.
- Deterministic ordering: ties are broken predictably by product ID.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Sequence


@dataclass
class CandidateRankItem:
    product_id: int
    product: Any
    final_score: float
    keyword_score: float = 0.0
    fuzzy_score: float = 0.0
    semantic_score: float = 0.0
    raw_semantic: float = 0.0
    attribute_bonus: float = 0.0
    corroboration_bonus: float = 0.0
    sources: list[str] = field(default_factory=list)
    match_tier: str = "none"


# Stop words for attribute query matching
_QUERY_STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "for", "with", "from", "to", "and", "or",
    "me", "my", "i", "we", "you", "item", "items", "thing", "things", "product",
    "products", "some", "something", "any", "good", "best", "want", "need",
    "please", "find", "show", "give", "store", "nearby", "near", "under", "above",
}


def _extract_query_tokens(query: str) -> set[str]:
    """Extract meaningful lowercase word stems/tokens from query text."""
    words = re.findall(r"[a-z0-9]+", query.lower())
    return {w for w in words if w not in _QUERY_STOP_WORDS and len(w) > 1}


def _extract_product_attribute_names(product: Any) -> set[str]:
    """Safely extract set of attribute names from a Product instance."""
    if not hasattr(product, "product_attributes") or not product.product_attributes:
        return set()

    names = set()
    for pa in product.product_attributes:
        attr = getattr(pa, "attribute", None)
        if attr and hasattr(attr, "name") and attr.name:
            names.add(attr.name.lower())
    return names


def _check_attribute_alignment(query_tokens: set[str], attribute_names: set[str]) -> bool:
    """
    Check if any query token semantically aligns with an attribute name.
    Examples:
    - token 'drink' aligns with 'drinkable' or 'cold-drink'
    - token 'snack' aligns with 'savory-snack' or 'snack'
    - token 'bread' aligns with 'bread' or 'bakery-product'
    - token 'butter' or 'spread' aligns with 'spread'
    - token 'dairy' or 'milk' aligns with 'dairy-product'
    - token 'soap' or 'hygiene' aligns with 'bathing' or 'personal-care'
    """
    if not query_tokens or not attribute_names:
        return False

    for token in query_tokens:
        for attr in attribute_names:
            # Direct match
            if token == attr:
                return True
            # Substring / compound match (e.g., 'drink' in 'drinkable', 'snack' in 'savory-snack')
            if token in attr or attr in token:
                return True
            # Specific domain equivalences
            if token == "milk" and "dairy-product" in attr:
                return True
            if token == "butter" and "spread" in attr:
                return True
            if token in {"soap", "hygiene", "wash"} and ("bathing" in attr or "personal-care" in attr):
                return True
            if token in {"toothpaste", "teeth", "brush"} and ("oral-care" in attr or "personal-care" in attr):
                return True
            if token in {"detergent", "laundry", "wash"} and "laundry-care" in attr:
                return True
            if token in {"juice", "cola", "pepsi", "soda", "beverage"} and ("drinkable" in attr or "cold-drink" in attr):
                return True

    return False


def rank_candidates(
    query: str,
    keyword_products: Sequence[Any],
    fuzzy_results: Sequence[Any],
    semantic_results: Sequence[Any],
    limit: int = 20,
) -> list[CandidateRankItem]:
    """
    Merge, calibrate, corroboration-boost, and rank candidates from
    keyword, fuzzy, and semantic retrieval stages.

    Returns deterministic list of CandidateRankItem sorted by final_score descending.
    """
    clean_q = query.strip().lower()
    if not clean_q:
        return []

    query_tokens = _extract_query_tokens(clean_q)

    # Dictionary to aggregate candidate signals: product_id -> dict
    candidate_map: dict[int, dict[str, Any]] = {}

    def get_or_create(p: Any) -> dict[str, Any]:
        pid = p.id
        if pid not in candidate_map:
            candidate_map[pid] = {
                "product": p,
                "keyword_score": 0.0,
                "fuzzy_score": 0.0,
                "raw_semantic": 0.0,
                "sources": [],
                "match_tier": "none",
            }
        return candidate_map[pid]

    # 1. Process Keyword Candidates
    for product in keyword_products:
        entry = get_or_create(product)
        entry["sources"].append("keyword")

        p_name = product.name.strip().lower()

        if p_name == clean_q:
            entry["keyword_score"] = 1.00
            entry["match_tier"] = "exact_match"
        elif re.search(rf"\b{re.escape(clean_q)}\b", p_name):
            # Query appears as a distinct word in product name
            entry["keyword_score"] = 0.95
            entry["match_tier"] = "keyword_word"
        elif p_name.startswith(clean_q):
            # Query is a prefix
            entry["keyword_score"] = 0.92
            entry["match_tier"] = "keyword_prefix"
        else:
            # Substring match
            entry["keyword_score"] = 0.85
            entry["match_tier"] = "keyword_substr"

    # 2. Process Fuzzy Candidates
    for item in fuzzy_results:
        # fuzzy_search returns (Product, similarity)
        product = item[0]
        similarity = float(item[1])

        entry = get_or_create(product)
        if "fuzzy" not in entry["sources"]:
            entry["sources"].append("fuzzy")
        entry["fuzzy_score"] = max(entry["fuzzy_score"], max(0.0, min(1.0, similarity)))

    # 3. Process Semantic Candidates
    max_raw_semantic = 0.0
    for item in semantic_results:
        # semantic_search returns (Product, similarity)
        product = item[0]
        similarity = float(item[1])

        entry = get_or_create(product)
        if "semantic" not in entry["sources"]:
            entry["sources"].append("semantic")
        entry["raw_semantic"] = max(entry["raw_semantic"], similarity)
        if similarity > max_raw_semantic:
            max_raw_semantic = similarity

    if not candidate_map:
        return []

    # Check whether strong keyword or high-confidence fuzzy matches exist
    has_strong_keyword = any(
        entry["keyword_score"] >= 0.85 for entry in candidate_map.values()
    )
    has_strong_fuzzy = any(
        entry["fuzzy_score"] >= 0.75 for entry in candidate_map.values()
    )
    has_strong_anchor = has_strong_keyword or has_strong_fuzzy

    ranked_items: list[CandidateRankItem] = []

    for pid, entry in candidate_map.items():
        product = entry["product"]
        p_name = product.name.strip().lower()
        k_score = entry["keyword_score"]
        f_score = entry["fuzzy_score"]
        raw_sem = entry["raw_semantic"]
        sources = entry["sources"]

        # 4. Calibrate Semantic Score
        if "semantic" in sources and max_raw_semantic > 0.0:
            # Absolute calibration: maps typical MiniLM range [0.10, 0.60] to [0.0, 1.0]
            sem_abs = max(0.0, min(1.0, (raw_sem - 0.10) / 0.50))
            # Relative calibration: score relative to top semantic match for this query
            sem_rel = max(0.0, min(1.0, raw_sem / max_raw_semantic))
            # Blended semantic score
            semantic_score = round(0.40 * sem_abs + 0.60 * sem_rel, 4)
        else:
            sem_abs = 0.0
            sem_rel = 0.0
            semantic_score = 0.0

        # 5. Semantic Noise Pruning
        # If strong keyword or fuzzy anchor exists, prune weak semantic-only candidates
        if has_strong_anchor:
            if "keyword" not in sources and "fuzzy" not in sources:
                # Semantic only: prune if below anchor threshold
                if raw_sem < 0.20 or sem_rel < 0.55:
                    continue
        else:
            # Semantic only query: prune very low tail noise
            if "keyword" not in sources and "fuzzy" not in sources:
                if raw_sem < 0.12 or sem_rel < 0.35:
                    continue

        # 6. Attribute Alignment Bonus
        attr_names = _extract_product_attribute_names(product)
        has_attr_align = _check_attribute_alignment(query_tokens, attr_names)
        attr_bonus = 0.05 if has_attr_align else 0.00

        # 7. Channel Corroboration Bonus
        channel_count = len(sources)
        if channel_count >= 3:
            corr_bonus = 0.10
        elif channel_count == 2:
            corr_bonus = 0.05
        else:
            corr_bonus = 0.00

        # 8. Compute Final Score
        tier = entry["match_tier"]

        if p_name == clean_q:
            # Tier 1: Exact Name Match Guarantee
            final_score = 1.00
            tier = "exact_match"
        elif "keyword" in sources:
            # Tier 2: Keyword match
            # Base keyword score + small semantic bonus + attribute + corroboration
            base = k_score
            sem_contribution = 0.03 * semantic_score
            final_score = min(0.99, base + sem_contribution + attr_bonus + corr_bonus)
            if channel_count > 1:
                tier = f"hybrid_{tier}"
        elif "fuzzy" in sources and "semantic" in sources:
            # Tier 3: Corroborated Fuzzy + Semantic
            final_score = min(
                0.88,
                0.50 * f_score + 0.40 * semantic_score + attr_bonus + corr_bonus,
            )
            tier = "hybrid_fuzzy_semantic"
        elif "fuzzy" in sources:
            # Tier 4: Fuzzy only
            final_score = min(0.80, f_score * 0.85 + attr_bonus)
            tier = "fuzzy_only"
        else:
            # Tier 5: Semantic only
            final_score = min(0.75, semantic_score * 0.65 + attr_bonus)
            tier = "semantic_only"

        ranked_items.append(
            CandidateRankItem(
                product_id=pid,
                product=product,
                final_score=round(final_score, 4),
                keyword_score=round(k_score, 4),
                fuzzy_score=round(f_score, 4),
                semantic_score=round(semantic_score, 4),
                raw_semantic=round(raw_sem, 4),
                attribute_bonus=round(attr_bonus, 4),
                corroboration_bonus=round(corr_bonus, 4),
                sources=sources,
                match_tier=tier,
            )
        )

    # 9. Deterministic Sorting
    # Order by (-final_score, -keyword_score, -fuzzy_score, -semantic_score, product_id)
    ranked_items.sort(
        key=lambda item: (
            -item.final_score,
            -item.keyword_score,
            -item.fuzzy_score,
            -item.semantic_score,
            item.product_id,
        )
    )

    return ranked_items[:limit]
