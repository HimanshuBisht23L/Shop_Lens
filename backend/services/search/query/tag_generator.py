"""
Automated Tag Generation Module for ShopLens Search V2.

Generates rich, consistent product search tags automatically:
1. Tokenizes brand and product title, removing noise/stopwords.
2. Expands domain-specific taxonomy synonyms for the selected sub-category (Hinglish, colloquial terms).
3. Adds brand aliases.
4. Merges with optional manual tags and deduplicates.

Zero human admin effort required.
"""

import re

STOPWORDS = {
    "and", "the", "for", "in", "with", "of", "to", "at", "by", "from",
    "pack", "packet", "bottle", "box", "can", "pouch", "bag",
    "g", "gm", "gms", "gram", "grams", "kg", "kgs", "ml", "l", "ltr", "liter", "litre",
    "piece", "pieces", "pcs", "pc"
}

SUBCATEGORY_SYNONYMS: dict[str, list[str]] = {
    "Chocolates & Candies": [
        "chocolate", "chocolates", "candy", "candies", "sweets", "meetha", "mitha",
        "toffee", "confectionery", "dark chocolate", "milk chocolate"
    ],
    "Milk": [
        "milk", "doodh", "dudh", "dairy", "cow milk", "toned milk", "fresh milk", "pouch milk"
    ],
    "Butter & Ghee": [
        "butter", "ghee", "makhan", "makkhan", "dairy", "cooking fat"
    ],
    "Bread & Bakery": [
        "bread", "bakery", "pav", "paav", "roti", "loaf", "brown bread", "white bread", "breakfast"
    ],
    "Biscuits & Cookies": [
        "biscuit", "biscuits", "cookies", "biskut", "biskoot", "chai time", "bakery", "snack"
    ],
    "Chips & Crisps": [
        "chips", "crisps", "wafers", "namkeen", "snack", "crunchy", "potato chips", "munchies"
    ],
    "Soft Drinks & Juices": [
        "cold drink", "soft drink", "juice", "soda", "beverage", "fizzy", "refreshment"
    ],
    "Tea & Coffee": [
        "tea", "coffee", "chai", "chai patti", "beverage", "hot drink", "caffeine"
    ],
    "Fresh Fruits": [
        "fruit", "fruits", "phal", "fresh", "organic", "healthy"
    ],
    "Fresh Vegetables": [
        "vegetable", "vegetables", "sabzi", "sabji", "tarkari", "fresh", "organic"
    ],
    "Personal Care & Soaps": [
        "soap", "sabun", "bath", "body wash", "skincare", "hygiene"
    ],
    "Oral Care": [
        "toothpaste", "toothbrush", "dant", "oral care", "fresh breath"
    ],
    "Cleaning & Household": [
        "detergent", "washing powder", "cleaner", "surf", "soap", "household", "laundry"
    ],
}

BRAND_ALIASES: dict[str, list[str]] = {
    "cadbury": ["cadburys", "cadbury chocolate"],
    "amul": ["amul dairy", "anand milk"],
    "coca cola": ["coke", "coca-cola"],
    "pepsi": ["pepsico"],
    "lays": ["lay's", "lays chips"],
    "parle": ["parle-g", "parleg"],
    "britannia": ["britania"],
    "kurkure": ["kurkure namkeen"],
    "colgate": ["colgate palmolive"],
    "dove": ["dove soap"],
    "surf excel": ["surf", "surf detergent"],
}


def tokenize_text(text: str) -> list[str]:
    # Extract lowercase alphanumeric tokens
    tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    return [
        t for t in tokens
        if len(t) >= 2 and t not in STOPWORDS and not t.isdigit()
    ]


def generate_product_tags(
    name: str,
    brand: str,
    sub_category_name: str | None = None,
    manual_tags: list[str] | None = None,
) -> list[str]:
    """
    Automated tag generator for product catalog indexing.
    """
    tags_set: set[str] = set()

    # 1. Title tokens
    if name:
        for t in tokenize_text(name):
            tags_set.add(t)

    # 2. Brand tokens & aliases
    if brand:
        b_clean = brand.strip().lower()
        tags_set.add(b_clean)
        for t in tokenize_text(brand):
            tags_set.add(t)
        if b_clean in BRAND_ALIASES:
            for alias in BRAND_ALIASES[b_clean]:
                tags_set.add(alias.lower())

    # 3. Sub-Category Domain Synonyms
    if sub_category_name:
        sub_cat_clean = sub_category_name.strip()
        tags_set.add(sub_cat_clean.lower())
        for key, synonyms in SUBCATEGORY_SYNONYMS.items():
            if (
                key.lower() == sub_cat_clean.lower()
                or sub_cat_clean.lower() in key.lower()
                or key.lower() in sub_cat_clean.lower()
            ):
                for syn in synonyms:
                    tags_set.add(syn.lower())

    # 4. Manual tags from admin (if any)
    if manual_tags:
        for m_tag in manual_tags:
            cleaned_m = m_tag.strip().lower()
            if cleaned_m:
                tags_set.add(cleaned_m)

    return sorted(list(tags_set))
