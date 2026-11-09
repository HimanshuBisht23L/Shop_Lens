"""
Query Intent Classifier Module for ShopLens Search V2.

Production-grade Dual-Path Architecture:
1. TYPE_A_SPECIFIC: Target specific product type, brand, or subcategory (e.g., 'chocolate', 'amul milk', 'lays', 'cadbury dairy milk').
   -> Activates Hard Category / Brand / Lexical Gate. Non-matching sub-categories cannot enter candidate pool.
2. TYPE_B_CONCEPTUAL: Target broad concept, theme, or department (e.g., 'household things', 'something to drink', 'sweet things', 'party snacks').
   -> Evaluates Dynamic Taxonomy Prediction (Q2C) via vector embeddings of the catalog taxonomy.
   -> Dynamically scopes or boosts candidate retrieval to predicted subcategories and categories.
"""

from dataclasses import dataclass, field
import difflib
import re

from services.search.query.taxonomy_matcher import predict_taxonomy_scope

TYPE_A_SPECIFIC = "TYPE_A_SPECIFIC"
TYPE_B_CONCEPTUAL = "TYPE_B_CONCEPTUAL"

# Standard known brands in catalog
KNOWN_BRANDS = {
    "cadbury": "Cadbury",
    "amul": "Amul",
    "mother dairy": "Mother Dairy",
    "britannia": "Britannia",
    "lays": "Lays",
    "lay's": "Lays",
    "kurkure": "Kurkure",
    "coca cola": "Coca-Cola",
    "coca-cola": "Coca-Cola",
    "coke": "Coca-Cola",
    "pepsi": "Pepsi",
    "thums up": "Thums Up",
    "sprite": "Sprite",
    "limca": "Limca",
    "oreo": "Oreo",
    "parle": "Parle",
    "parle-g": "Parle",
    "dove": "Dove",
    "colgate": "Colgate",
    "surf excel": "Surf Excel",
    "surf": "Surf Excel",
    "ariel": "Ariel",
    "tide": "Tide",
    "rin": "Rin",
    "vim": "Vim",
    "lizol": "Lizol",
    "harpic": "Harpic",
    "real": "Real",
    "tropicana": "Tropicana",
    "red bull": "Red Bull",
    "nestle": "Nestle",
    "maggi": "Maggi",
    "yippee": "Sunfeast",
    "sunfeast": "Sunfeast",
    "haldiram's": "Haldiram's",
    "haldiram": "Haldiram's",
    "bikaji": "Bikaji",
    "aashirvaad": "Aashirvaad",
    "fortune": "Fortune",
    "tata tea": "Tata Tea",
    "nescafe": "Nescafe",
    "bru": "Bru",
    "horlicks": "Horlicks",
    "bournvita": "Bournvita",
    "dettol": "Dettol",
    "nivea": "Nivea",
    "himalaya": "Himalaya",
    "pampers": "Pampers",
    "pedigree": "Pedigree",
    "whiskas": "Whiskas",
    "harvest gold": "Harvest Gold",
    "english oven": "English Oven",
    "catch": "Catch",
    "everest": "Everest",
    "mdh": "MDH",
    "tata salt": "Tata Salt",
    "happilo": "Happilo",
}

# Sub-category alias mapping (longer phrases prioritized)
SUBCATEGORY_ALIASES: dict[str, str] = {
    "dairy milk": "Chocolates",
    "cadbury silk": "Chocolates",
    "5 star": "Chocolates",
    "chocolate": "Chocolates",
    "chocolates": "Chocolates",
    "dark chocolate": "Chocolates",

    "candy": "Candies & Toffees",
    "candies": "Candies & Toffees",
    "toffee": "Candies & Toffees",
    "toffees": "Candies & Toffees",
    "lollipop": "Candies & Toffees",

    "mithai": "Indian Mithai & Desserts",
    "gulab jamun": "Indian Mithai & Desserts",
    "rasgulla": "Indian Mithai & Desserts",
    "kaju katli": "Indian Mithai & Desserts",
    "soan papdi": "Indian Mithai & Desserts",
    "halwa": "Indian Mithai & Desserts",

    "ice cream": "Ice Creams & Kulfi",
    "icecream": "Ice Creams & Kulfi",
    "kulfi": "Ice Creams & Kulfi",
    "cornetto": "Ice Creams & Kulfi",
    "chocobar": "Ice Creams & Kulfi",

    "milk": "Milk",
    "doodh": "Milk",
    "dudh": "Milk",
    "toned milk": "Milk",
    "cow milk": "Milk",

    "butter": "Butter & Ghee",
    "ghee": "Butter & Ghee",
    "desi ghee": "Butter & Ghee",
    "makhan": "Butter & Ghee",
    "makkhan": "Butter & Ghee",

    "paneer": "Paneer & Curd",
    "curd": "Paneer & Curd",
    "dahi": "Paneer & Curd",
    "yogurt": "Paneer & Curd",
    "chaas": "Paneer & Curd",
    "buttermilk": "Paneer & Curd",

    "brown bread": "Bread & Pav",
    "white bread": "Bread & Pav",
    "bread": "Bread & Pav",
    "pav": "Bread & Pav",
    "paav": "Bread & Pav",
    "bun": "Bread & Pav",

    "egg": "Eggs",
    "eggs": "Eggs",
    "ande": "Eggs",
    "anda": "Eggs",

    "cheese": "Cheese & Dips",
    "mozzarella": "Cheese & Dips",
    "cheddar": "Cheese & Dips",

    "chips": "Chips & Crisps",
    "wafers": "Chips & Crisps",
    "crisps": "Chips & Crisps",
    "potato chips": "Chips & Crisps",

    "namkeen": "Namkeen & Savory",
    "bhujia": "Namkeen & Savory",
    "sev": "Namkeen & Savory",

    "popcorn": "Nachos & Popcorn",
    "nachos": "Nachos & Popcorn",

    "makhana": "Roasted & Healthy Snacks",

    "biscuit": "Cookies & Biscuits",
    "biscuits": "Cookies & Biscuits",
    "cookie": "Cookies & Biscuits",
    "cookies": "Cookies & Biscuits",
    "biskut": "Cookies & Biscuits",

    "rusk": "Rusks & Toasts",
    "toast": "Rusks & Toasts",

    "cake": "Cakes & Muffins",
    "cakes": "Cakes & Muffins",
    "muffin": "Cakes & Muffins",
    "brownie": "Cakes & Muffins",

    "cold drink": "Soft Drinks & Sodas",
    "soft drink": "Soft Drinks & Sodas",
    "soda": "Soft Drinks & Sodas",
    "cola": "Soft Drinks & Sodas",

    "fruit juice": "Fruit Juices & Nectars",
    "juice": "Fruit Juices & Nectars",

    "energy drink": "Energy & Sports Drinks",

    "water": "Water & Tonic Water",
    "mineral water": "Water & Tonic Water",

    "tea": "Tea & Chai Patti",
    "chai": "Tea & Chai Patti",
    "chai patti": "Tea & Chai Patti",
    "green tea": "Tea & Chai Patti",

    "coffee": "Coffee",
    "instant coffee": "Coffee",

    "noodles": "Noodles & Vermicelli",
    "maggi": "Noodles & Vermicelli",
    "vermicelli": "Noodles & Vermicelli",
    "seviyan": "Noodles & Vermicelli",

    "pasta": "Pasta & Macaroni",
    "macaroni": "Pasta & Macaroni",

    "ketchup": "Sauces & Spreads",
    "sauce": "Sauces & Spreads",
    "mayonnaise": "Sauces & Spreads",
    "jam": "Sauces & Spreads",
    "peanut butter": "Sauces & Spreads",

    "atta": "Atta & Flours",
    "flour": "Atta & Flours",
    "maida": "Atta & Flours",
    "besan": "Atta & Flours",
    "sooji": "Atta & Flours",

    "rice": "Rice & Rice Products",
    "basmati": "Rice & Rice Products",
    "poha": "Rice & Rice Products",

    "oil": "Cooking Oils & Ghee",
    "mustard oil": "Cooking Oils & Ghee",
    "sunflower oil": "Cooking Oils & Ghee",
    "olive oil": "Cooking Oils & Ghee",

    "dal": "Dals & Pulses",
    "daal": "Dals & Pulses",
    "pulses": "Dals & Pulses",
    "rajma": "Dals & Pulses",
    "chhole": "Dals & Pulses",

    "spices": "Whole & Ground Spices",
    "masala": "Whole & Ground Spices",
    "haldi": "Whole & Ground Spices",
    "mirch": "Whole & Ground Spices",

    "salt": "Salt, Sugar & Jaggery",
    "namak": "Salt, Sugar & Jaggery",
    "sugar": "Salt, Sugar & Jaggery",
    "cheeni": "Salt, Sugar & Jaggery",
    "jaggery": "Salt, Sugar & Jaggery",
    "gur": "Salt, Sugar & Jaggery",

    "dry fruits": "Dry Fruits & Nuts",
    "almonds": "Dry Fruits & Nuts",
    "badam": "Dry Fruits & Nuts",
    "kaju": "Dry Fruits & Nuts",
    "cashews": "Dry Fruits & Nuts",
    "kismis": "Dry Fruits & Nuts",

    "vegetables": "Fresh Vegetables",
    "vegetable": "Fresh Vegetables",
    "sabzi": "Fresh Vegetables",
    "potato": "Fresh Vegetables",
    "aloo": "Fresh Vegetables",
    "onion": "Fresh Vegetables",
    "pyaz": "Fresh Vegetables",
    "tomato": "Fresh Vegetables",
    "tamatar": "Fresh Vegetables",

    "fruit": "Fresh Fruits",
    "fruits": "Fresh Fruits",
    "apple": "Fresh Fruits",
    "banana": "Fresh Fruits",
    "mango": "Fresh Fruits",

    "soap": "Bathing Soaps & Body Wash",
    "body wash": "Bathing Soaps & Body Wash",
    "shampoo": "Hair Care & Shampoos",
    "hair oil": "Hair Care & Shampoos",
    "toothpaste": "Oral Care",
    "toothbrush": "Oral Care",

    "detergent": "Laundry Detergents & Bars",
    "washing powder": "Laundry Detergents & Bars",
    "dishwash": "Dishwashing",
    "floor cleaner": "Surface Cleaners & Disinfectants",
    "toilet cleaner": "Surface Cleaners & Disinfectants",

    "diapers": "Diapers & Baby Wipes",
    "baby wipes": "Diapers & Baby Wipes",
    "dog food": "Pet Food & Accessories",
    "cat food": "Pet Food & Accessories",
}


@dataclass
class QueryIntent:
    intent_type: str  # TYPE_A_SPECIFIC or TYPE_B_CONCEPTUAL
    matched_brand: str | None = None
    matched_sub_category: str | None = None
    matched_category_ids: list[int] = field(default_factory=list)
    matched_sub_category_ids: list[int] = field(default_factory=list)
    matched_sub_category_names: list[str] = field(default_factory=list)
    inferred_attributes: dict = field(default_factory=dict)
    taxonomy_affinity: float = 0.0
    is_taxonomy_scoped: bool = False
    confidence: float = 1.0


def classify_query_intent(cleaned_query: str) -> QueryIntent:
    q = cleaned_query.strip().lower()
    if not q:
        return QueryIntent(intent_type=TYPE_B_CONCEPTUAL)

    tokens = q.split()
    matched_brand = None
    matched_sub_cat = None

    # 1. Check for specific sub-category entity matches (Longer phrases prioritized)
    sorted_aliases = sorted(SUBCATEGORY_ALIASES.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if alias == q or f" {alias} " in f" {q} ":
            matched_sub_cat = SUBCATEGORY_ALIASES[alias]
            break

    if not matched_sub_cat:
        # Check token typos for subcategories (e.g. "choclate" -> "chocolate")
        for token in tokens:
            close_cats = difflib.get_close_matches(token, sorted_aliases, n=1, cutoff=0.85)
            if close_cats:
                matched_sub_cat = SUBCATEGORY_ALIASES[close_cats[0]]
                break

    # 2. Check for brand matches (exact or token match or strict typo >= 0.88)
    for b_alias, official_name in KNOWN_BRANDS.items():
        if b_alias == q or f" {b_alias} " in f" {q} ":
            matched_brand = official_name
            break

    if not matched_brand:
        for token in tokens:
            close_brands = difflib.get_close_matches(token, KNOWN_BRANDS.keys(), n=1, cutoff=0.88)
            if close_brands:
                matched_brand = KNOWN_BRANDS[close_brands[0]]
                break

    # 3. If specific brand or sub-category matched -> Type A Specific
    if matched_brand or matched_sub_cat:
        return QueryIntent(
            intent_type=TYPE_A_SPECIFIC,
            matched_brand=matched_brand,
            matched_sub_category=matched_sub_cat,
            confidence=0.95,
        )

    # 4. If Type B (Broad / Conceptual Query) -> Run Dynamic Taxonomy Prediction (Q2C)
    taxonomy_scope = predict_taxonomy_scope(cleaned_query, threshold=0.55)

    return QueryIntent(
        intent_type=TYPE_B_CONCEPTUAL,
        matched_brand=None,
        matched_sub_category=None,
        matched_category_ids=taxonomy_scope.matched_category_ids,
        matched_sub_category_ids=taxonomy_scope.matched_sub_category_ids,
        matched_sub_category_names=taxonomy_scope.matched_sub_category_names,
        inferred_attributes=taxonomy_scope.inferred_attributes,
        taxonomy_affinity=taxonomy_scope.top_affinity,
        is_taxonomy_scoped=taxonomy_scope.is_scoped,
        confidence=0.85,
    )
