"""
ShopLens - Semantic Search Dataset Refinement, Generation & Validation Script

Refines and expands the dataset for sentence-transformers/all-MiniLM-L6-v2 fine-tuning.
Enforces:
1. Ground truth adherence to the 20 catalog products and attributes.
2. Correction of historical mislabelings (Surf Excel != personal hygiene, Bread != spread, etc.).
3. Rich query diversity: natural language, Indian grocery terms, typos, synonyms, broad & specific intents.
4. Support for multiple positives per query.
5. High-quality hard negatives targeting specific semantic confusions.
6. Clean query-grouped splitting (Train ~70%, Val ~15%, Test ~15%) with zero query leakage.
7. Explicit documentation of borderline and out-of-catalog queries in dataset_review.csv.
8. Generation of detailed dataset_statistics.md.
"""

import csv
import json
import os
import random
from pathlib import Path
from collections import defaultdict
import pandas as pd


# ---------------------------------------------------------------------------
# Ground Truth Catalog (Verified directly from PostgreSQL database)
# ---------------------------------------------------------------------------
CATALOG = {
    1: {"name": "Cadbury Dairy Milk Chocholate", "category": "Snacks", "attributes": ["chocolate", "dairy-product", "snack", "sweet"]},
    2: {"name": "Cadbury 5 Star Chocolate", "category": "Snacks", "attributes": ["chocolate", "snack", "sweet"]},
    3: {"name": "Amul Taaza Milk", "category": "Dairy", "attributes": ["breakfast", "dairy-product", "drinkable"]},
    4: {"name": "Amul Butter", "category": "Dairy", "attributes": ["cooking", "dairy-product", "spread"]},
    5: {"name": "Britannia Bread", "category": "Bakery", "attributes": ["bakery-product", "bread", "breakfast"]},
    6: {"name": "Harvest Brown Bread", "category": "Bakery", "attributes": ["bakery-product", "bread", "breakfast", "whole-grain"]},
    7: {"name": "Parle-G Biscuits", "category": "Snacks", "attributes": ["biscuit", "breakfast", "snack", "sweet"]},
    8: {"name": "Oreo Biscuits", "category": "Snacks", "attributes": ["biscuit", "chocolate", "snack", "sweet"]},
    9: {"name": "Lays Classic Salted", "category": "Snacks", "attributes": ["savory-snack", "snack"]},
    10: {"name": "Kurkure Masala Munch", "category": "Snacks", "attributes": ["savory-snack", "snack"]},
    11: {"name": "Coca Cola", "category": "Beverages", "attributes": ["cold-drink", "drinkable"]},
    12: {"name": "Pepsi", "category": "Beverages", "attributes": ["cold-drink", "drinkable"]},
    13: {"name": "Real Mixed Fruit Juice", "category": "Beverages", "attributes": ["drinkable", "fruit", "juice"]},
    14: {"name": "Red Apple", "category": "Fruits", "attributes": ["fresh-produce", "fruit"]},
    15: {"name": "Banana", "category": "Fruits", "attributes": ["breakfast", "fresh-produce", "fruit"]},
    16: {"name": "Tomato", "category": "Vegetables", "attributes": ["cooking", "fresh-produce", "vegetable"]},
    17: {"name": "Potato", "category": "Vegetables", "attributes": ["cooking", "fresh-produce", "vegetable"]},
    18: {"name": "Dove Soap", "category": "Personal Care", "attributes": ["bathing", "personal-care"]},
    19: {"name": "Colgate Toothpaste", "category": "Personal Care", "attributes": ["oral-care", "personal-care"]},
    20: {"name": "Surf Excel Detergent", "category": "Household", "attributes": ["laundry-care"]},
}


# ---------------------------------------------------------------------------
# Curated Queries with Multi-Positives & Informative Hard Negatives
# ---------------------------------------------------------------------------
REFINED_QUERIES = [
    # ---------------- 1. Beverages ----------------
    {
        "query": "something to drink",
        "category": "Beverages",
        "pairs": [(11, 18), (12, 20), (13, 17), (3, 19)],
    },
    {
        "query": "cold soda on a hot day",
        "category": "Beverages",
        "pairs": [(11, 3), (12, 4)],  # Hard Neg: Milk is drinkable but not cold soda
    },
    {
        "query": "fizzy soft drink",
        "category": "Beverages",
        "pairs": [(11, 13), (12, 5)], # Hard Neg: Real Juice is drinkable but not fizzy soft drink
    },
    {
        "query": "packaged fruit beverage",
        "category": "Beverages",
        "pairs": [(13, 11), (13, 9)], # Hard Neg: Coke is a beverage but not fruit-based
    },
    {
        "query": "chilled cold drinks",
        "category": "Beverages",
        "pairs": [(11, 3), (12, 16)],
    },
    {
        "query": "refreshing beverage",
        "category": "Beverages",
        "pairs": [(11, 17), (12, 18), (13, 19)],
    },
    {
        "query": "non alcoholic fizzy cans or bottles",
        "category": "Beverages",
        "pairs": [(11, 7), (12, 20)],
    },
    {
        "query": "real fruit juice tetra pack",
        "category": "Beverages",
        "pairs": [(13, 11), (13, 10)],
    },
    {
        "query": "sweet mixed fruit drink",
        "category": "Beverages",
        "pairs": [(13, 12), (13, 18)],
    },
    {
        "query": "fizzy cola refreshment",
        "category": "Beverages",
        "pairs": [(11, 8), (12, 16)],
    },
    {
        "query": "thanda cold drink for party",
        "category": "Beverages",
        "pairs": [(11, 3), (12, 19)], # Indian term: thanda
    },
    {
        "query": "pepsi cold drink bottle",
        "category": "Beverages",
        "pairs": [(12, 11), (12, 20)],
    },
    {
        "query": "coca cola chilled can",
        "category": "Beverages",
        "pairs": [(11, 12), (11, 18)],
    },
    {
        "query": "healthy fruit drink for children",
        "category": "Beverages",
        "pairs": [(13, 11), (13, 12)], # Hard Neg: Sodas are not healthy fruit drinks
    },

    # ---------------- 2. Dairy Products ----------------
    {
        "query": "dairy essentials for morning",
        "category": "Dairy",
        "pairs": [(3, 20), (4, 18)],
    },
    {
        "query": "fresh milk packet",
        "category": "Dairy",
        "pairs": [(3, 11), (3, 9)],
    },
    {
        "query": "pasteurized table butter",
        "category": "Dairy",
        "pairs": [(4, 3), (4, 11)],  # Hard Neg: Milk is dairy, but not table butter
    },
    {
        "query": "daily dairy products",
        "category": "Dairy",
        "pairs": [(3, 10), (4, 19)],
    },
    {
        "query": "amul dairy items",
        "category": "Dairy",
        "pairs": [(3, 14), (4, 20)],
    },
    {
        "query": "cow or buffalo milk for making tea",
        "category": "Dairy",
        "pairs": [(3, 17), (3, 11)],
    },
    {
        "query": "salted dairy butter for cooking",
        "category": "Dairy",
        "pairs": [(4, 13), (4, 18)],
    },
    {
        "query": "daily milk supply",
        "category": "Dairy",
        "pairs": [(3, 8), (3, 20)],
    },
    {
        "query": "full cream or toned milk",
        "category": "Dairy",
        "pairs": [(3, 4), (3, 18)],  # Hard Neg: Butter is dairy, but not milk
    },
    {
        "query": "yellow cooking butter block",
        "category": "Dairy",
        "pairs": [(4, 3), (4, 12)],
    },
    {
        "query": "doodh packet for chai",
        "category": "Dairy",
        "pairs": [(3, 16), (3, 19)], # Indian term: doodh
    },
    {
        "query": "makhan for morning breakfast",
        "category": "Dairy",
        "pairs": [(4, 18), (4, 9)],  # Indian term: makhan
    },
    {
        "query": "fresh amul doodh",
        "category": "Dairy",
        "pairs": [(3, 11), (3, 20)], # Indian term
    },

    # ---------------- 3. Bakery Products ----------------
    {
        "query": "bread for toast",
        "category": "Bakery",
        "pairs": [(5, 4), (6, 18)],  # Hard Neg: Butter is spread, not bread!
    },
    {
        "query": "fresh bakery items",
        "category": "Bakery",
        "pairs": [(5, 7), (6, 11)],  # Hard Neg: Parle-G is packaged snack, not fresh bakery bread
    },
    {
        "query": "whole wheat brown bread loaf",
        "category": "Bakery",
        "pairs": [(6, 5), (6, 1)],   # Hard Neg: Britannia Bread is white bread, not whole wheat brown!
    },
    {
        "query": "white sandwich bread",
        "category": "Bakery",
        "pairs": [(5, 6), (5, 17)],  # Hard Neg: Harvest Brown is brown bread, not white bread!
    },
    {
        "query": "sliced bread loaf for breakfast",
        "category": "Bakery",
        "pairs": [(5, 12), (6, 18)],
    },
    {
        "query": "healthy high fiber brown bread",
        "category": "Bakery",
        "pairs": [(6, 5), (6, 10)],  # Hard Neg: White bread lacks high fiber
    },
    {
        "query": "soft white bread packet",
        "category": "Bakery",
        "pairs": [(5, 6), (5, 9)],
    },
    {
        "query": "bread loaf for making sandwiches",
        "category": "Bakery",
        "pairs": [(5, 4), (6, 20)],  # Hard Neg: Butter is spread, not bread
    },
    {
        "query": "whole grain brown slices",
        "category": "Bakery",
        "pairs": [(6, 5), (6, 18)],
    },
    {
        "query": "double roti packet",
        "category": "Bakery",
        "pairs": [(5, 16), (6, 19)], # Indian term: double roti
    },
    {
        "query": "sandwich bread loaf",
        "category": "Bakery",
        "pairs": [(5, 4), (6, 18)],
    },

    # ---------------- 4. Breakfast Products ----------------
    {
        "query": "quick morning breakfast items",
        "category": "Breakfast",
        "pairs": [(3, 18), (5, 20), (6, 19), (15, 17)],
    },
    {
        "query": "healthy fruit to eat for breakfast",
        "category": "Breakfast",
        "pairs": [(15, 16), (15, 10)], # Hard Neg: Tomato is culinary vegetable
    },
    {
        "query": "milk and bread for breakfast",
        "category": "Breakfast",
        "pairs": [(3, 17), (5, 18), (6, 20)],
    },
    {
        "query": "light morning meal",
        "category": "Breakfast",
        "pairs": [(5, 9), (15, 20), (6, 18)],
    },
    {
        "query": "breakfast staples",
        "category": "Breakfast",
        "pairs": [(3, 18), (5, 19), (6, 20)],
    },
    {
        "query": "energy fruit for morning",
        "category": "Breakfast",
        "pairs": [(15, 11), (15, 20)],
    },
    {
        "query": "morning tea biscuits",
        "category": "Breakfast",
        "pairs": [(7, 9), (7, 16)],  # Hard Neg: Lays chips are not tea biscuits
    },
    {
        "query": "nutritious breakfast food",
        "category": "Breakfast",
        "pairs": [(3, 10), (6, 20), (15, 18)],
    },
    {
        "query": "subah ka nashta items",
        "category": "Breakfast",
        "pairs": [(3, 18), (5, 19), (15, 20)], # Indian term
    },
    {
        "query": "chai ke sath biscuit",
        "category": "Breakfast",
        "pairs": [(7, 10), (7, 18)], # Indian term
    },
    {
        "query": "nashta essentials",
        "category": "Breakfast",
        "pairs": [(3, 20), (6, 17), (15, 19)], # Indian term
    },

    # ---------------- 5. Spreads ----------------
    {
        "query": "things to spread on bread",
        "category": "Spreads",
        "pairs": [(4, 5), (4, 6), (4, 20)], # Crucial Hard Neg: Britannia/Brown Bread are NOT spreads!
    },
    {
        "query": "butter spread for toast",
        "category": "Spreads",
        "pairs": [(4, 5), (4, 12)],  # Hard Neg: Bread is base, not spread
    },
    {
        "query": "creamy salted spread",
        "category": "Spreads",
        "pairs": [(4, 3), (4, 10)],  # Hard Neg: Milk is dairy, but not spread
    },
    {
        "query": "spread for morning sandwich",
        "category": "Spreads",
        "pairs": [(4, 5), (4, 14)],  # Hard Neg: Bread is base, not spread
    },
    {
        "query": "smooth table spread",
        "category": "Spreads",
        "pairs": [(4, 8), (4, 18)],
    },
    {
        "query": "spread to put on hot paratha or toast",
        "category": "Spreads",
        "pairs": [(4, 19), (4, 17)],
    },
    {
        "query": "dairy butter spread",
        "category": "Spreads",
        "pairs": [(4, 3), (4, 16)],
    },
    {
        "query": "bread par lagane wala makhan",
        "category": "Spreads",
        "pairs": [(4, 5), (4, 20)],  # Indian term: makhan spread
    },
    {
        "query": "paratha makhan spread",
        "category": "Spreads",
        "pairs": [(4, 18), (4, 11)], # Indian term
    },

    # ---------------- 6. Fruits ----------------
    {
        "query": "fresh fruits to eat",
        "category": "Fruits",
        "pairs": [(14, 13), (15, 16)], # Hard Neg: Real Juice is processed; Tomato is vegetable
    },
    {
        "query": "sweet ripe bananas",
        "category": "Fruits",
        "pairs": [(15, 14), (15, 9)],  # Apple is fruit, but not banana
    },
    {
        "query": "crisp red apples",
        "category": "Fruits",
        "pairs": [(14, 15), (14, 11)],
    },
    {
        "query": "healthy raw fruits",
        "category": "Fruits",
        "pairs": [(14, 17), (15, 10)],
    },
    {
        "query": "potassium rich yellow fruit",
        "category": "Fruits",
        "pairs": [(15, 14), (15, 4)],  # Banana is yellow fruit, not butter
    },
    {
        "query": "fresh red crunchy fruit",
        "category": "Fruits",
        "pairs": [(14, 16), (14, 5)],  # Apple is fruit, tomato is cooking vegetable
    },
    {
        "query": "fruit basket essentials",
        "category": "Fruits",
        "pairs": [(14, 17), (15, 18)],
    },
    {
        "query": "fresh produce fruits",
        "category": "Fruits",
        "pairs": [(14, 1), (15, 20)],
    },
    {
        "query": "natural sweet fruit snack",
        "category": "Fruits",
        "pairs": [(14, 8), (15, 12)],  # Hard Neg: Oreo is biscuit snack, not fruit
    },
    {
        "query": "seasonal organic apples",
        "category": "Fruits",
        "pairs": [(14, 15), (14, 2)],
    },
    {
        "query": "taaza fal fruit",
        "category": "Fruits",
        "pairs": [(14, 18), (15, 20)], # Indian term
    },
    {
        "query": "meethe kele banana",
        "category": "Fruits",
        "pairs": [(15, 17), (15, 19)], # Indian term
    },
    {
        "query": "laal seb apple",
        "category": "Fruits",
        "pairs": [(14, 16), (14, 18)], # Indian term
    },

    # ---------------- 7. Vegetables ----------------
    {
        "query": "fresh cooking vegetables",
        "category": "Vegetables",
        "pairs": [(16, 14), (17, 15)], # Hard Neg: Apple/Banana are fruits, not cooking vegetables!
    },
    {
        "query": "potatoes for making fries",
        "category": "Vegetables",
        "pairs": [(17, 16), (17, 11)],
    },
    {
        "query": "red tomatoes for salad and gravy",
        "category": "Vegetables",
        "pairs": [(16, 14), (16, 8)],  # Hard Neg: Apple is red fruit, not salad/gravy tomato!
    },
    {
        "query": "staple kitchen veggies",
        "category": "Vegetables",
        "pairs": [(16, 12), (17, 19)],
    },
    {
        "query": "raw potatoes for aloo subzi",
        "category": "Vegetables",
        "pairs": [(17, 7), (17, 16)],
    },
    {
        "query": "juicy ripe tomatoes",
        "category": "Vegetables",
        "pairs": [(16, 14), (16, 4)],  # Hard Neg: Apple is red fruit
    },
    {
        "query": "vegetables for curry",
        "category": "Vegetables",
        "pairs": [(16, 2), (17, 18)],
    },
    {
        "query": "subzi cooking veggies",
        "category": "Vegetables",
        "pairs": [(16, 13), (17, 19)],
    },
    {
        "query": "fresh vegetable produce",
        "category": "Vegetables",
        "pairs": [(16, 1), (17, 20)],
    },
    {
        "query": "starchy root vegetables",
        "category": "Vegetables",
        "pairs": [(17, 16), (17, 18)], # Hard Neg: Tomato is not root vegetable
    },
    {
        "query": "aloo for cooking",
        "category": "Vegetables",
        "pairs": [(17, 15), (17, 19)], # Indian term
    },
    {
        "query": "tamatar for curry",
        "category": "Vegetables",
        "pairs": [(16, 14), (16, 18)], # Indian term
    },
    {
        "query": "taaza aloo tamatar subzi",
        "category": "Vegetables",
        "pairs": [(16, 5), (17, 20)], # Indian term
    },

    # ---------------- 8. Cooking Ingredients ----------------
    {
        "query": "cooking ingredients for kitchen",
        "category": "Cooking",
        "pairs": [(4, 18), (16, 20), (17, 19)],
    },
    {
        "query": "butter for frying and sauteing",
        "category": "Cooking",
        "pairs": [(4, 3), (4, 14)],  # Hard Neg: Milk is dairy, but not frying fat
    },
    {
        "query": "base vegetables for curry tadka",
        "category": "Cooking",
        "pairs": [(16, 1), (17, 20)],
    },
    {
        "query": "ingredients to cook dinner",
        "category": "Cooking",
        "pairs": [(4, 12), (16, 18), (17, 19)],
    },
    {
        "query": "kitchen staples for cooking meal",
        "category": "Cooking",
        "pairs": [(4, 8), (16, 11)],
    },
    {
        "query": "gravy base tomato",
        "category": "Cooking",
        "pairs": [(16, 14), (16, 9)], # Hard Neg: Apple is red, but not gravy base
    },
    {
        "query": "khana banane ke ingredients",
        "category": "Cooking",
        "pairs": [(4, 19), (16, 18), (17, 20)], # Indian term
    },

    # ---------------- 9. Sweet Snacks & Chocolates ----------------
    {
        "query": "something sweet to eat",
        "category": "Sweet Snacks",
        "pairs": [(1, 9), (2, 10), (7, 17), (8, 19)], # Hard Neg: Lays/Kurkure are salty snacks!
    },
    {
        "query": "chocolate bar",
        "category": "Sweet Snacks",
        "pairs": [(1, 8), (2, 7)],   # Hard Neg: Oreo is biscuit, not chocolate bar!
    },
    {
        "query": "creamy milk chocolate",
        "category": "Sweet Snacks",
        "pairs": [(1, 2), (1, 20)],  # 5 Star is caramel; Dairy Milk is milk chocolate
    },
    {
        "query": "caramel filled chocolate",
        "category": "Sweet Snacks",
        "pairs": [(2, 1), (2, 9)],   # Dairy Milk lacks caramel filling
    },
    {
        "query": "sweet biscuits for children",
        "category": "Sweet Snacks",
        "pairs": [(7, 9), (8, 10)],  # Hard Neg: Lays/Kurkure are salty snacks!
    },
    {
        "query": "black chocolate cream cookies",
        "category": "Sweet Snacks",
        "pairs": [(8, 7), (8, 4)],   # Parle-G is glucose, not chocolate cream
    },
    {
        "query": "glucose biscuits for tea time",
        "category": "Sweet Snacks",
        "pairs": [(7, 8), (7, 12)],  # Oreo is cream biscuit, not glucose
    },
    {
        "query": "sweet treat after dinner",
        "category": "Sweet Snacks",
        "pairs": [(1, 17), (2, 18), (8, 9)],
    },
    {
        "query": "sandwich biscuits with cream",
        "category": "Sweet Snacks",
        "pairs": [(8, 7), (8, 16)],  # Parle-G is flat glucose biscuit
    },
    {
        "query": "chocolates and candy confectionery",
        "category": "Sweet Snacks",
        "pairs": [(1, 19), (2, 20)],
    },
    {
        "query": "cookies for dunking in milk",
        "category": "Sweet Snacks",
        "pairs": [(7, 9), (8, 10)],  # Hard Neg: Chips are not cookies for milk!
    },
    {
        "query": "meetha snack chocolate",
        "category": "Sweet Snacks",
        "pairs": [(1, 9), (2, 19)],  # Indian term: meetha
    },
    {
        "query": "sweet biskit for kids",
        "category": "Sweet Snacks",
        "pairs": [(7, 10), (8, 18)], # Indian spelling variant: biskit
    },
    {
        "query": "chocholate bar sweet",
        "category": "Sweet Snacks",
        "pairs": [(1, 17), (2, 20)], # Spelling typo: chocholate
    },

    # ---------------- 10. Salty & Savory Snacks ----------------
    {
        "query": "salty snacks",
        "category": "Salty Snacks",
        "pairs": [(9, 1), (10, 7)],  # Hard Neg: Dairy Milk and Parle-G are SWEET snacks!
    },
    {
        "query": "crispy potato chips",
        "category": "Salty Snacks",
        "pairs": [(9, 17), (9, 3)],  # Hard Neg: Raw Potato is vegetable, not chips!
    },
    {
        "query": "spicy crunchy snack",
        "category": "Salty Snacks",
        "pairs": [(10, 9), (10, 8)], # Hard Neg: Lays Classic Salted is salted, not spicy!
    },
    {
        "query": "savory munchies for evening",
        "category": "Salty Snacks",
        "pairs": [(9, 7), (10, 1)],  # Hard Neg: Parle-G / Cadbury are sweet, not savory
    },
    {
        "query": "salted potato wafers",
        "category": "Salty Snacks",
        "pairs": [(9, 17), (9, 4)],  # Hard Neg: Raw Potato is vegetable
    },
    {
        "query": "chatpata teatime namkeen",
        "category": "Salty Snacks",
        "pairs": [(10, 7), (10, 15)], # Hard Neg: Parle-G is sweet, not chatpata namkeen
    },
    {
        "query": "crunchy chips packet",
        "category": "Salty Snacks",
        "pairs": [(9, 16), (9, 1)],
    },
    {
        "query": "snack for movie night",
        "category": "Salty Snacks",
        "pairs": [(9, 18), (10, 20)],
    },
    {
        "query": "masala flavored crunchy curls",
        "category": "Salty Snacks",
        "pairs": [(10, 9), (10, 6)], # Lays is plain salted, Kurkure is masala curls
    },
    {
        "query": "salty finger food for party",
        "category": "Salty Snacks",
        "pairs": [(9, 8), (10, 20)], # Oreo is sweet, not salty finger food
    },
    {
        "query": "namkeen chatpata snack",
        "category": "Salty Snacks",
        "pairs": [(10, 1), (10, 18)], # Indian term: namkeen
    },
    {
        "query": "potato chips wafers namkeen",
        "category": "Salty Snacks",
        "pairs": [(9, 17), (9, 7)],  # Indian term
    },

    # ---------------- 11. Personal Care ----------------
    {
        "query": "personal care products",
        "category": "Personal Care",
        "pairs": [(18, 20), (19, 9)], # Crucial Hard Neg: Surf Excel is Laundry/Household, NOT personal care!
    },
    {
        "query": "bath soap for shower",
        "category": "Personal Care",
        "pairs": [(18, 20), (18, 11)], # Crucial Hard Neg: Surf Excel is laundry detergent, NOT bath soap!
    },
    {
        "query": "moisturizing body soap bar",
        "category": "Personal Care",
        "pairs": [(18, 20), (18, 5)],  # Hard Neg: Surf Excel is laundry detergent
    },
    {
        "query": "soap for bathing",
        "category": "Personal Care",
        "pairs": [(18, 20), (18, 10)], # Hard Neg: Surf Excel is for clothes, not bathing!
    },
    {
        "query": "toiletries and body wash bar",
        "category": "Personal Care",
        "pairs": [(18, 2), (18, 20)],
    },
    {
        "query": "daily personal hygiene soap",
        "category": "Personal Care",
        "pairs": [(18, 20), (18, 12)], # Hard Neg: Surf Excel is laundry detergent
    },
    {
        "query": "gentle skin cleanser bar",
        "category": "Personal Care",
        "pairs": [(18, 20), (18, 8)],
    },
    {
        "query": "beauty bathing bar",
        "category": "Personal Care",
        "pairs": [(18, 20), (18, 17)],
    },
    {
        "query": "personal hygiene toiletries",
        "category": "Personal Care",
        "pairs": [(18, 20), (19, 9)],
    },
    {
        "query": "nahane ka sabun bath soap",
        "category": "Personal Care",
        "pairs": [(18, 20), (18, 16)], # Indian term: nahane ka sabun != Surf Excel!
    },
    {
        "query": "body soap bar",
        "category": "Personal Care",
        "pairs": [(18, 20), (18, 19)], # Hard Neg: Surf Excel / Colgate
    },

    # ---------------- 12. Oral Care ----------------
    {
        "query": "oral hygiene",
        "category": "Oral Care",
        "pairs": [(19, 18), (19, 1)], # Crucial Hard Neg: Dove Soap is bathing, not oral hygiene!
    },
    {
        "query": "oral care products",
        "category": "Oral Care",
        "pairs": [(19, 18), (19, 20)], # Hard Neg: Dove Soap & Surf Excel
    },
    {
        "query": "toothpaste for teeth cleaning",
        "category": "Oral Care",
        "pairs": [(19, 18), (19, 4)],  # Hard Neg: Dove Soap is bath soap
    },
    {
        "query": "dental hygiene paste",
        "category": "Oral Care",
        "pairs": [(19, 18), (19, 9)],  # Hard Neg: Dove Soap
    },
    {
        "query": "fluoride toothpaste for fresh breath",
        "category": "Oral Care",
        "pairs": [(19, 15), (19, 18)],
    },
    {
        "query": "morning teeth brushing paste",
        "category": "Oral Care",
        "pairs": [(19, 11), (19, 18)],
    },
    {
        "query": "cavity protection toothpaste",
        "category": "Oral Care",
        "pairs": [(19, 7), (19, 18)],
    },
    {
        "query": "minty fresh oral dentifrice",
        "category": "Oral Care",
        "pairs": [(19, 18), (19, 12)],
    },
    {
        "query": "paste to brush teeth",
        "category": "Oral Care",
        "pairs": [(19, 20), (19, 18)],
    },
    {
        "query": "dant saaf karne ka paste toothpaste",
        "category": "Oral Care",
        "pairs": [(19, 18), (19, 17)], # Indian term
    },
    {
        "query": "colgat toothpaste for teeth",
        "category": "Oral Care",
        "pairs": [(19, 18), (19, 9)],  # Indian typo/colloquial
    },

    # ---------------- 13. Laundry Care ----------------
    {
        "query": "laundry detergent powder",
        "category": "Laundry",
        "pairs": [(20, 18), (20, 3)],  # Crucial Hard Neg: Dove Soap is bath soap, NOT laundry detergent!
    },
    {
        "query": "washing powder for clothes",
        "category": "Laundry",
        "pairs": [(20, 18), (20, 19)], # Hard Neg: Dove Soap is for skin, not clothes
    },
    {
        "query": "clothes washing detergent",
        "category": "Laundry",
        "pairs": [(20, 18), (20, 11)],
    },
    {
        "query": "stain removal powder for laundry",
        "category": "Laundry",
        "pairs": [(20, 18), (20, 12)],
    },
    {
        "query": "household laundry cleaning products",
        "category": "Laundry",
        "pairs": [(20, 18), (20, 8)],
    },
    {
        "query": "detergent for bucket or washing machine",
        "category": "Laundry",
        "pairs": [(20, 18), (20, 14)],
    },
    {
        "query": "fabric washing powder",
        "category": "Laundry",
        "pairs": [(20, 18), (20, 15)],
    },
    {
        "query": "cloth cleaning soap powder",
        "category": "Laundry",
        "pairs": [(20, 18), (20, 19)],
    },
    {
        "query": "kapde dhone ka powder detergent",
        "category": "Laundry",
        "pairs": [(20, 18), (20, 16)], # Indian term: kapde dhone ka powder
    },
    {
        "query": "surf excel washing powder packet",
        "category": "Laundry",
        "pairs": [(20, 18), (20, 9)],
    },

    # ---------------- 14. General Grocery Combos ----------------
    {
        "query": "daily kitchen essentials",
        "category": "General Grocery",
        "pairs": [(3, 18), (4, 20), (5, 19), (16, 11), (17, 18)],
    },
    {
        "query": "snack items for party",
        "category": "General Grocery",
        "pairs": [(1, 19), (8, 20), (9, 18), (10, 19)],
    },
    {
        "query": "items for making cheese butter toast",
        "category": "General Grocery",
        "pairs": [(4, 18), (5, 20), (6, 19)],
    },
    {
        "query": "healthy snacks for diet",
        "category": "General Grocery",
        "pairs": [(14, 1), (15, 2), (6, 18)], # Hard Neg: Cadbury Chocolates are NOT healthy diet snacks!
    },
    {
        "query": "drinks and chips combo",
        "category": "General Grocery",
        "pairs": [(11, 18), (12, 19), (9, 20)],
    },
    {
        "query": "kids school tiffin snacks",
        "category": "General Grocery",
        "pairs": [(5, 19), (7, 20), (8, 18), (15, 17)],
    },
    {
        "query": "weekend movie binge snacks",
        "category": "General Grocery",
        "pairs": [(9, 18), (10, 19), (11, 20)],
    },
    {
        "query": "sweet and savory snack combo",
        "category": "General Grocery",
        "pairs": [(1, 18), (9, 20)],
    },
    {
        "query": "groceries for home kitchen",
        "category": "General Grocery",
        "pairs": [(3, 18), (4, 19), (5, 20), (16, 11), (17, 12)],
    },
    {
        "query": "teatime snack and biscuit",
        "category": "General Grocery",
        "pairs": [(7, 20), (8, 18), (10, 19)],
    },
]


# ---------------------------------------------------------------------------
# Borderline / Ambiguous / Out-of-Catalog Review Dataset
# (Documented explicitly for human review rather than silently mislabeling)
# ---------------------------------------------------------------------------
DATASET_REVIEW_EXAMPLES = [
    {
        "query": "personal hygiene products",
        "positive_product_id": 20,
        "positive_product_name": CATALOG[20]["name"],
        "negative_product_id": 9,
        "negative_product_name": CATALOG[9]["name"],
        "review_reason": "Historical confusion: Surf Excel was previously mistagged with personal-care. Corrected to laundry-care (Household). Must NOT be labeled positive for personal hygiene.",
        "recommended_action": "REJECT as positive; use Surf Excel as HARD NEGATIVE for personal hygiene queries."
    },
    {
        "query": "things to spread on bread",
        "positive_product_id": 5,
        "positive_product_name": CATALOG[5]["name"],
        "negative_product_id": 18,
        "negative_product_name": CATALOG[18]["name"],
        "review_reason": "Lexical co-occurrence: Bread is the base for spreading, but is not itself a spread. Only butter is a spread.",
        "recommended_action": "REJECT as positive; use Britannia Bread as HARD NEGATIVE against positive Amul Butter."
    },
    {
        "query": "cooking oil",
        "positive_product_id": 4,
        "positive_product_name": CATALOG[4]["name"],
        "negative_product_id": 19,
        "negative_product_name": CATALOG[19]["name"],
        "review_reason": "Missing Catalog Product: Butter is a cooking fat/spread, but not cooking oil. ShopLens catalog contains no cooking oil (mustard, sunflower, olive).",
        "recommended_action": "EXCLUDE from training set; mark query as having NO relevant catalog product."
    },
    {
        "query": "oral hygiene",
        "positive_product_id": 18,
        "positive_product_name": CATALOG[18]["name"],
        "negative_product_id": 1,
        "negative_product_name": CATALOG[1]["name"],
        "review_reason": "Category parent overlap: Both Dove Soap and Colgate Toothpaste share 'Personal Care', but Dove is bathing only, not oral care.",
        "recommended_action": "REJECT as positive; use Dove Soap as HARD NEGATIVE against positive Colgate Toothpaste."
    },
    {
        "query": "healthy diet snack",
        "positive_product_id": 1,
        "positive_product_name": CATALOG[1]["name"],
        "negative_product_id": 20,
        "negative_product_name": CATALOG[20]["name"],
        "review_reason": "Semantic conflict: Cadbury Dairy Milk has 'snack' attribute, but contradicts 'healthy diet' intent (high sugar confectionery).",
        "recommended_action": "REJECT as positive; use Cadbury as HARD NEGATIVE against positive Red Apple and Banana."
    },
    {
        "query": "breakfast items",
        "positive_product_id": 13,
        "positive_product_name": CATALOG[13]["name"],
        "negative_product_id": 18,
        "negative_product_name": CATALOG[18]["name"],
        "review_reason": "Taxonomy gap: Packaged juice is consumed at breakfast by many users, but lacks the 'breakfast' attribute in catalog taxonomy.",
        "recommended_action": "EXCLUDE from primary breakfast training pairs until attribute taxonomy is expanded."
    },
    {
        "query": "dairy items",
        "positive_product_id": 1,
        "positive_product_name": CATALOG[1]["name"],
        "negative_product_id": 18,
        "negative_product_name": CATALOG[18]["name"],
        "review_reason": "Ingredient attribute vs primary intent: Cadbury contains 'dairy-product' attribute, but users searching 'dairy items' seek milk/butter/paneer, not chocolate candy.",
        "recommended_action": "EXCLUDE Cadbury from primary 'dairy items' queries; keep positive strictly on Amul Milk and Amul Butter."
    },
    {
        "query": "fresh bakery products",
        "positive_product_id": 7,
        "positive_product_name": CATALOG[7]["name"],
        "negative_product_id": 18,
        "negative_product_name": CATALOG[18]["name"],
        "review_reason": "Baking method vs store shelf: Biscuits are baked, but classified under packaged snacks rather than bakery bread.",
        "recommended_action": "EXCLUDE biscuits from bakery category; keep bakery queries focused on bread loaves."
    },
    {
        "query": "fruit snack",
        "positive_product_id": 13,
        "positive_product_name": CATALOG[13]["name"],
        "negative_product_id": 18,
        "negative_product_name": CATALOG[18]["name"],
        "review_reason": "Form factor ambiguity: Juice is derived from fruit, but is a liquid beverage rather than a solid fruit snack.",
        "recommended_action": "Label whole fresh fruits (Apple, Banana) as positive; flag juice as ambiguous."
    },
    {
        "query": "energy food for workout",
        "positive_product_id": 7,
        "positive_product_name": CATALOG[7]["name"],
        "negative_product_id": 20,
        "negative_product_name": CATALOG[20]["name"],
        "review_reason": "Processed glucose vs fitness nutrition: Parle-G provides quick glucose energy, but fitness consumers may reject it as high-sugar processed food.",
        "recommended_action": "Use Banana as the unambiguous positive for workout energy food."
    },
    {
        "query": "savory breakfast",
        "positive_product_id": 9,
        "positive_product_name": CATALOG[9]["name"],
        "negative_product_id": 18,
        "negative_product_name": CATALOG[18]["name"],
        "review_reason": "Cultural/meal fit: Has 'savory-snack' attribute, but potato chips are rarely acceptable as breakfast food.",
        "recommended_action": "EXCLUDE chips from breakfast queries."
    },
    {
        "query": "fabric conditioner",
        "positive_product_id": 20,
        "positive_product_name": CATALOG[20]["name"],
        "negative_product_id": 19,
        "negative_product_name": CATALOG[19]["name"],
        "review_reason": "Sub-category distinction: Detergent cleans fabrics, but is distinct from fabric softener/conditioner (e.g. Comfort).",
        "recommended_action": "Mark as unsupported intent (no fabric softener in catalog)."
    },
    {
        "query": "hair shampoo for hair wash",
        "positive_product_id": 18,
        "positive_product_name": CATALOG[18]["name"],
        "negative_product_id": 9,
        "negative_product_name": CATALOG[9]["name"],
        "review_reason": "Missing Catalog Product: Dove Soap is a body bar, not hair shampoo. Catalog contains no shampoo.",
        "recommended_action": "EXCLUDE from training set; mark query as having NO relevant catalog product."
    },
    {
        "query": "dishwashing liquid for utensils",
        "positive_product_id": 20,
        "positive_product_name": CATALOG[20]["name"],
        "negative_product_id": 3,
        "negative_product_name": CATALOG[3]["name"],
        "review_reason": "Missing Catalog Product: Surf Excel is for laundry clothes, not dishwashing utensils. Catalog contains no dishwashing bar/liquid.",
        "recommended_action": "EXCLUDE from training set; mark query as having NO relevant catalog product."
    },
]


def split_queries_stratified(seed: int = 42):
    """
    Stratifies unique queries by category into:
    - Train (~70%)
    - Validation (~15%)
    - Test (~15%)
    Guarantees zero query leakage across splits.
    """
    rng = random.Random(seed)

    by_category = defaultdict(list)
    for q_def in REFINED_QUERIES:
        by_category[q_def["category"]].append(q_def)

    train_defs = []
    val_defs = []
    test_defs = []

    for cat, defs in by_category.items():
        shuffled = list(defs)
        rng.shuffle(shuffled)

        n = len(shuffled)
        n_val = max(1, round(n * 0.15))
        n_test = max(1, round(n * 0.15))
        n_train = n - n_val - n_test

        train_defs.extend(shuffled[:n_train])
        val_defs.extend(shuffled[n_train:n_train + n_val])
        test_defs.extend(shuffled[n_train + n_val:])

    return train_defs, val_defs, test_defs


def flatten_to_rows(query_defs):
    """Flattens query definitions into schema-compliant rows."""
    rows = []
    for q_def in query_defs:
        query = q_def["query"]
        for pos_id, neg_id in q_def["pairs"]:
            rows.append({
                "query": query,
                "positive_product_id": pos_id,
                "positive_product_name": CATALOG[pos_id]["name"],
                "negative_product_id": neg_id,
                "negative_product_name": CATALOG[neg_id]["name"],
            })
    return rows


def validate_all(train_rows, val_rows, test_rows, review_rows):
    """Strictly validates all 10 dataset requirements."""
    all_rows = train_rows + val_rows + test_rows
    errors = []

    # 1. Product IDs exist in catalog
    for r in all_rows:
        if r["positive_product_id"] not in CATALOG:
            errors.append(f"Invalid positive ID: {r['positive_product_id']}")
        if r["negative_product_id"] not in CATALOG:
            errors.append(f"Invalid negative ID: {r['negative_product_id']}")

    # 2. Product names match exactly
    for r in all_rows:
        exp_pos = CATALOG[r["positive_product_id"]]["name"]
        exp_neg = CATALOG[r["negative_product_id"]]["name"]
        if r["positive_product_name"] != exp_pos:
            errors.append(f"Name mismatch for ID {r['positive_product_id']}: '{r['positive_product_name']}' != '{exp_pos}'")
        if r["negative_product_name"] != exp_neg:
            errors.append(f"Name mismatch for ID {r['negative_product_id']}: '{r['negative_product_name']}' != '{exp_neg}'")

    # 3. Positive != Negative
    for r in all_rows:
        if r["positive_product_id"] == r["negative_product_id"]:
            errors.append(f"Identical positive and negative ID for query '{r['query']}': {r['positive_product_id']}")

    # 4. No contradictory labels
    query_pos_map = defaultdict(set)
    query_neg_map = defaultdict(set)
    for r in all_rows:
        q = r["query"]
        query_pos_map[q].add(r["positive_product_id"])
        query_neg_map[q].add(r["negative_product_id"])

    for q in query_pos_map:
        overlap = query_pos_map[q].intersection(query_neg_map[q])
        if overlap:
            errors.append(f"Contradictory label for query '{q}': product {overlap} is both positive and negative")

    # 5. No duplicates within splits
    for s_name, s_rows in [("train", train_rows), ("validation", val_rows), ("test", test_rows)]:
        seen = set()
        for r in s_rows:
            key = (r["query"], r["positive_product_id"], r["negative_product_id"])
            if key in seen:
                errors.append(f"Duplicate pair in {s_name}: {key}")
            seen.add(key)

    # 6. Zero query leakage
    t_q = {r["query"] for r in train_rows}
    v_q = {r["query"] for r in val_rows}
    te_q = {r["query"] for r in test_rows}

    if t_q.intersection(v_q):
        errors.append(f"Query leakage train <-> val: {t_q.intersection(v_q)}")
    if t_q.intersection(te_q):
        errors.append(f"Query leakage train <-> test: {t_q.intersection(te_q)}")
    if v_q.intersection(te_q):
        errors.append(f"Query leakage val <-> test: {v_q.intersection(te_q)}")

    # 7. Specific sanity check: Surf Excel is NEVER positive for personal care/bathing/hygiene
    for r in all_rows:
        q_l = r["query"].lower()
        if any(term in q_l for term in ["personal hygiene", "personal care", "shower", "bath soap", "body wash", "nahane"]):
            if r["positive_product_id"] == 20:
                errors.append(f"Surf Excel Detergent incorrectly positive for hygiene query: '{r['query']}'")

    # 8. Specific sanity check: Britannia/Brown Bread is NEVER positive for 'things to spread on bread'
    for r in all_rows:
        if r["query"].lower() == "things to spread on bread" and r["positive_product_id"] in (5, 6):
            errors.append(f"Bread incorrectly labeled as spread for 'things to spread on bread'")

    return errors


def write_csv(filepath, rows, fieldnames):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_statistics_report(filepath, train_rows, val_rows, test_rows, review_rows, train_defs, val_defs, test_defs):
    all_rows = train_rows + val_rows + test_rows
    total_examples = len(all_rows)
    all_queries = {r["query"] for r in all_rows}
    unique_queries = len(all_queries)

    all_pos_ids = {r["positive_product_id"] for r in all_rows}
    all_neg_ids = {r["negative_product_id"] for r in all_rows}
    all_products = all_pos_ids.union(all_neg_ids)

    # Multi-positive queries
    query_pos_count = defaultdict(set)
    for r in all_rows:
        query_pos_count[r["query"]].add(r["positive_product_id"])
    multi_pos_queries = {q: ids for q, ids in query_pos_count.items() if len(ids) > 1}

    # Category breakdown
    by_cat = defaultdict(lambda: {"train_q": 0, "val_q": 0, "test_q": 0, "train_p": 0, "val_p": 0, "test_p": 0})
    for q in train_defs:
        by_cat[q["category"]]["train_q"] += 1
        by_cat[q["category"]]["train_p"] += len(q["pairs"])
    for q in val_defs:
        by_cat[q["category"]]["val_q"] += 1
        by_cat[q["category"]]["val_p"] += len(q["pairs"])
    for q in test_defs:
        by_cat[q["category"]]["test_q"] += 1
        by_cat[q["category"]]["test_p"] += len(q["pairs"])

    # Product coverage breakdown
    prod_pos_counts = defaultdict(int)
    prod_neg_counts = defaultdict(int)
    for r in all_rows:
        prod_pos_counts[r["positive_product_id"]] += 1
        prod_neg_counts[r["negative_product_id"]] += 1

    content = f"""# ShopLens — Semantic Search Dataset Statistics & Validation Report

## 1. Executive Summary

This document reports the comprehensive statistics, coverage metrics, and validation results for the refined ShopLens semantic search dataset, prepared for fine-tuning `sentence-transformers/all-MiniLM-L6-v2`.

- **Total Validated Training Triples**: {total_examples}
- **Total Unique Search Queries**: {unique_queries}
- **Catalog Product Coverage**: {len(all_products)} / 20 products ({len(all_products)/20*100:.0f}%)
- **Split Proportions**: Train {len(train_rows)/total_examples*100:.1f}% ({len(train_rows)} triples across {len(train_defs)} queries) | Validation {len(val_rows)/total_examples*100:.1f}% ({len(val_rows)} triples across {len(val_defs)} queries) | Test {len(test_rows)/total_examples*100:.1f}% ({len(test_rows)} triples across {len(test_defs)} queries)
- **Multi-Positive Queries**: {len(multi_pos_queries)} queries ({len(multi_pos_queries)/unique_queries*100:.1f}% of all queries)
- **Borderline / Ambiguous Examples Flagged for Review**: {len(review_rows)} examples
- **Cross-Split Query Leakage**: **0%** (Strict query-grouped partition verified)
- **Data Integrity & Consistency Errors**: **0**

---

## 2. Dataset Split Breakdown

| Split | Total Pairs | Percentage | Unique Queries | Query Percentage | Multi-Positive Queries |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Train (`train.csv`)** | {len(train_rows)} | {len(train_rows)/total_examples*100:.1f}% | {len(train_defs)} | {len(train_defs)/unique_queries*100:.1f}% | {sum(1 for q in train_defs if len(q['pairs']) > 1)} |
| **Validation (`validation.csv`)** | {len(val_rows)} | {len(val_rows)/total_examples*100:.1f}% | {len(val_defs)} | {len(val_defs)/unique_queries*100:.1f}% | {sum(1 for q in val_defs if len(q['pairs']) > 1)} |
| **Test (`test.csv`)** | {len(test_rows)} | {len(test_rows)/total_examples*100:.1f}% | {len(test_defs)} | {len(test_defs)/unique_queries*100:.1f}% | {sum(1 for q in test_defs if len(q['pairs']) > 1)} |
| **Total** | **{total_examples}** | **100.0%** | **{unique_queries}** | **100.0%** | **{len(multi_pos_queries)}** |

---

## 3. Category & Domain Distribution

Queries were stratified by category across splits to ensure balanced domain representation:

| Domain Category | Total Queries | Train Queries | Val Queries | Test Queries | Total Triples | Train Triples | Val Triples | Test Triples |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for cat in sorted(by_cat.keys()):
        d = by_cat[cat]
        tot_q = d["train_q"] + d["val_q"] + d["test_q"]
        tot_p = d["train_p"] + d["val_p"] + d["test_p"]
        content += f"| **{cat}** | {tot_q} | {d['train_q']} | {d['val_q']} | {d['test_q']} | {tot_p} | {d['train_p']} | {d['val_p']} | {d['test_p']} |\n"

    content += f"""| **Total** | **{unique_queries}** | **{len(train_defs)}** | **{len(val_defs)}** | **{len(test_defs)}** | **{total_examples}** | **{len(train_rows)}** | **{len(val_rows)}** | **{len(test_rows)}** |

---

## 4. Product Catalog Coverage

Every product in the ShopLens catalog is represented as both positive and negative candidates across the dataset:

| Product ID | Product Name | Category | Positive Triples | Negative Triples | Total Appearances |
| :---: | :--- | :--- | :---: | :---: | :---: |
"""
    for pid in sorted(CATALOG.keys()):
        name = CATALOG[pid]["name"]
        cat = CATALOG[pid]["category"]
        pos_c = prod_pos_counts[pid]
        neg_c = prod_neg_counts[pid]
        tot_c = pos_c + neg_c
        content += f"| {pid:2d} | {name} | {cat} | {pos_c} | {neg_c} | {tot_c} |\n"

    content += f"""

---

## 5. Query Leakage & Integrity Verification

1. **Query Leakage Verification**:
   - Train ∩ Validation: **0 queries**
   - Train ∩ Test: **0 queries**
   - Validation ∩ Test: **0 queries**
   - *Result*: **100% strict query isolation.**

2. **Label Contradiction Check**:
   - For every query, the set of positive product IDs and negative product IDs was verified to have zero intersection.
   - *Result*: **0 contradictory labels.**

3. **Duplicate Pair Check**:
   - Within each split, every `(query, positive_product_id, negative_product_id)` triple was checked for uniqueness.
   - *Result*: **0 duplicate triples.**

4. **Negative Quality Check**:
   - Every negative product was checked to ensure it is not in the set of valid positive products for that query.
   - Hard negatives were explicitly structured to teach the model subtle boundaries (e.g. White Bread vs Brown Bread, Raw Potato vs Potato Chips, Bath Soap vs Laundry Detergent, Bread vs Butter Spread).

---

## 6. Review Dataset Summary (`dataset_review.csv`)

{len(review_rows)} borderline or ambiguous cases were isolated for review. Highlights:

1. **`personal hygiene products` → Surf Excel Detergent**: Rejected as positive. Corrected to Laundry/Household.
2. **`things to spread on bread` → Britannia Bread**: Rejected as positive. Bread is the substrate; butter is the spread.
3. **`cooking oil`**: Marked as unsupported intent (no cooking oil exists in the 20-product catalog).
4. **`oral hygiene` → Dove Soap**: Rejected as positive. Dove is bathing soap; Colgate is oral care.
5. **`healthy diet snack` → Cadbury Chocolate**: Rejected as positive. Fresh fruits (Apple, Banana) are the true healthy snacks.
6. **`dishwashing liquid` & `hair shampoo`**: Documented as unsupported query intents.

---

## 7. Known Scope Limitations & Guidance

1. **Catalog Scale**: The dataset reflects the active 20-product catalog. When the store catalog expands, query generation should be rerun using `generate_datasets.py`.
2. **Recommended Training Objective**: Use `MultipleNegativesRankingLoss` (MNRL) or `TripletLoss` with small batch size (16) and a conservative learning rate ($2 \\times 10^{{-5}}$).
3. **Test Set Protection**: The `test.csv` split is preserved as an independent test set and must NOT be used for gradient updates or early stopping.
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print("=" * 70)
    print("SHOPLENS - SEMANTIC SEARCH DATASET REFINEMENT & GENERATION")
    print("=" * 70)

    base_dir = Path(__file__).resolve().parent.parent / "datasets"
    base_dir.mkdir(parents=True, exist_ok=True)

    # 1. Stratified split
    train_defs, val_defs, test_defs = split_queries_stratified(seed=42)

    train_rows = flatten_to_rows(train_defs)
    val_rows = flatten_to_rows(val_defs)
    test_rows = flatten_to_rows(test_defs)
    review_rows = DATASET_REVIEW_EXAMPLES

    # 2. Strict validation
    errors = validate_all(train_rows, val_rows, test_rows, review_rows)
    if errors:
        print("\n[VALIDATION FAILED]")
        for err in errors:
            print(" -", err)
        raise ValueError(f"Validation failed with {len(errors)} errors")
    else:
        print("\n[VALIDATION PASSED] All integrity, logic, and catalog checks passed successfully!")

    # 3. Write CSVs
    fieldnames = [
        "query",
        "positive_product_id",
        "positive_product_name",
        "negative_product_id",
        "negative_product_name",
    ]

    train_path = base_dir / "train.csv"
    val_path = base_dir / "validation.csv"
    test_path = base_dir / "test.csv"
    review_path = base_dir / "dataset_review.csv"
    stats_path = base_dir / "dataset_statistics.md"

    write_csv(train_path, train_rows, fieldnames)
    write_csv(val_path, val_rows, fieldnames)
    write_csv(test_path, test_rows, fieldnames)

    review_fieldnames = fieldnames + ["review_reason", "recommended_action"]
    write_csv(review_path, review_rows, review_fieldnames)

    # 4. Write Statistics Report
    generate_statistics_report(
        stats_path,
        train_rows, val_rows, test_rows, review_rows,
        train_defs, val_defs, test_defs,
    )

    # 5. Verification with Pandas
    df_train = pd.read_csv(train_path)
    df_val = pd.read_csv(val_path)
    df_test = pd.read_csv(test_path)
    df_review = pd.read_csv(review_path)

    assert list(df_train.columns) == fieldnames, "train.csv columns mismatch"
    assert list(df_val.columns) == fieldnames, "validation.csv columns mismatch"
    assert list(df_test.columns) == fieldnames, "test.csv columns mismatch"
    assert list(df_review.columns) == review_fieldnames, "dataset_review.csv columns mismatch"

    print("\n[FILE LOAD VERIFIED] All CSVs and Markdown reports generated and loaded cleanly!")

    # Summary
    total_examples = len(train_rows) + len(val_rows) + len(test_rows)
    unique_queries = len(REFINED_QUERIES)

    print("\n" + "=" * 70)
    print("DATASET REFINEMENT SUMMARY")
    print("=" * 70)
    print(f"Total Validated Triples:       {total_examples}")
    print(f"Total Unique Queries:          {unique_queries}")
    print(f"Train Triples:                 {len(train_rows)} ({len(train_rows)/total_examples*100:.1f}%) across {len(train_defs)} queries")
    print(f"Validation Triples:            {len(val_rows)} ({len(val_rows)/total_examples*100:.1f}%) across {len(val_defs)} queries")
    print(f"Test Triples:                  {len(test_rows)} ({len(test_rows)/total_examples*100:.1f}%) across {len(test_defs)} queries")
    print(f"Review Triples Flagged:        {len(review_rows)}")
    print(f"Dataset Statistics Report:     {stats_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
