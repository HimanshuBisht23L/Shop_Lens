"""
Unit Tests for Search V2 Automated Tag Generator.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from services.search.query.tag_generator import (
    tokenize_text,
    generate_product_tags,
    SUBCATEGORY_SYNONYMS,
    BRAND_ALIASES,
)


def test_tokenize_text_removes_stopwords_and_digits():
    raw_title = "Amul Taaza Toned Fresh Milk (500 ml) pack of 2"
    tokens = tokenize_text(raw_title)
    assert "amul" in tokens
    assert "taaza" in tokens
    assert "toned" in tokens
    assert "fresh" in tokens
    assert "milk" in tokens
    # Stopwords and measurements should be excluded
    assert "500" not in tokens
    assert "ml" not in tokens
    assert "pack" not in tokens
    assert "of" not in tokens
    assert "2" not in tokens


def test_generate_product_tags_chocolates():
    tags = generate_product_tags(
        name="Cadbury Dairy Milk Silk Chocolate (150 g)",
        brand="Cadbury",
        sub_category_name="Chocolates & Candies",
    )
    # Title tokens
    assert "silk" in tags
    assert "chocolate" in tags
    # Brand alias expansion
    assert "cadbury" in tags
    assert "cadburys" in tags
    # Subcategory domain synonyms (Hindi / Hinglish / English)
    assert "meetha" in tags
    assert "mitha" in tags
    assert "candy" in tags
    assert "toffee" in tags
    assert "confectionery" in tags
    # Ensure list is sorted and unique
    assert tags == sorted(list(set(tags)))


def test_generate_product_tags_milk():
    tags = generate_product_tags(
        name="Amul Taaza Toned Fresh Milk (500 ml)",
        brand="Amul",
        sub_category_name="Milk",
    )
    assert "amul" in tags
    assert "amul dairy" in tags
    assert "milk" in tags
    assert "doodh" in tags
    assert "dudh" in tags
    assert "dairy" in tags
    assert "toned" in tags


def test_generate_product_tags_with_manual_tags():
    tags = generate_product_tags(
        name="Parle-G Gold Glucose Biscuits",
        brand="Parle",
        sub_category_name="Biscuits & Cookies",
        manual_tags=["chai partner", "tea time"],
    )
    assert "parle" in tags
    assert "parle-g" in tags
    assert "biscuits" in tags
    assert "biskut" in tags
    assert "chai partner" in tags
    assert "tea time" in tags
