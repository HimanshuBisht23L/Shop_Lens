"""
Query Normalization Module for ShopLens Search V2.

Performs:
1. Basic text cleaning (lowercase, whitespace collapse, punctuation handling).
2. Natural language price filter extraction (e.g., 'under 50', '50 se kam', 'between 100 and 500').
3. Search radius extraction (e.g., 'within 5km', 'under 3 miles').
4. Conversational filler and location phrase removal ('please show me', 'near me', 'pass me').
5. Hinglish-to-English grocery domain mapping (e.g., 'doodh' -> 'milk', 'pyaz' -> 'onion').
"""

import re
from dataclasses import dataclass


@dataclass
class NormalizedQueryOutput:
    original_query: str
    cleaned_query: str
    min_price: float | None = None
    max_price: float | None = None
    radius_km: float | None = None
    hinglish_terms_mapped: dict[str, str] = None


CURRENCY_PATTERN = r"(?:₹|rs\.?|inr|rupee|rupees|ruppee|ruppees)"

FILLER_PHRASES = [
    "please show me",
    "please give me",
    "please find me",
    "please find",
    "show me",
    "find me",
    "find",
    "i want",
    "i need",
    "give me",
    "search for",
    "looking for",
    "look for",
    "near me",
    "nearby",
    "around me",
    "pass me",
    "kripya",
]

# Static domain dictionary for Hinglish grocery terminology
HINGLISH_MAP = {
    "doodh": "milk",
    "dudh": "milk",
    "pyaz": "onion",
    "pyaaz": "onion",
    "kanda": "onion",
    "meetha": "sweet",
    "mitha": "sweet",
    "aloo": "potato",
    "alu": "potato",
    "tamatar": "tomato",
    "makhan": "butter",
    "makkhan": "butter",
    "namkeen": "savory snack",
    "namkin": "savory snack",
    "roti": "bread",
    "paav": "bread",
    "pav": "bread",
    "seb": "apple",
    "kela": "banana",
    "biskut": "biscuit",
    "biskoot": "biscuit",
    "sabzi": "vegetables",
    "sabji": "vegetables",
    "phal": "fruits",
    "sabun": "soap",
    "dahi": "curd",
    "chai": "tea",
    "chini": "sugar",
}


DISTANCE_UNITS_LOOKAHEAD = r"(?!\s*(?:km|kms|kilometer|kilometers|mile|miles|meter|meters|m\b))"

def clean_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def extract_price_range(text: str) -> tuple[str, float | None, float | None]:
    pattern = (
        r"(?:between|from)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        r"\s*(\d+(?:\.\d+)?)"
        r"\s*(?:and|to|-)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        r"\s*(\d+(?:\.\d+)?)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        rf"{DISTANCE_UNITS_LOOKAHEAD}"
    )
    match = re.search(pattern, text)
    if not match:
        return text, None, None

    min_p = float(match.group(1))
    max_p = float(match.group(2))
    cleaned = re.sub(pattern, "", text, count=1)
    return cleaned, min_p, max_p


def extract_max_price(text: str) -> tuple[str, float | None]:
    # English: under 50, below 50, less than 50
    pattern_en = (
        r"(?:under|below|less than|upto|up to)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        r"\s*(\d+(?:\.\d+)?)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        rf"{DISTANCE_UNITS_LOOKAHEAD}"
    )
    match = re.search(pattern_en, text)
    if match:
        max_p = float(match.group(1))
        cleaned = re.sub(pattern_en, "", text, count=1)
        return cleaned, max_p

    # Hindi / Hinglish: 50 se kam, 50 rupaye se kam
    pattern_hi = (
        rf"{CURRENCY_PATTERN}?"
        r"\s*(\d+(?:\.\d+)?)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        rf"{DISTANCE_UNITS_LOOKAHEAD}"
        r"\s*(?:se kam|se kum|ke andar|tak)"
    )
    match_hi = re.search(pattern_hi, text)
    if match_hi:
        max_p = float(match_hi.group(1))
        cleaned = re.sub(pattern_hi, "", text, count=1)
        return cleaned, max_p

    return text, None


def extract_min_price(text: str) -> tuple[str, float | None]:
    # English: above 20, over 20, more than 20
    pattern_en = (
        r"(?:above|over|more than|minimum|min)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        r"\s*(\d+(?:\.\d+)?)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        rf"{DISTANCE_UNITS_LOOKAHEAD}"
    )
    match = re.search(pattern_en, text)
    if match:
        min_p = float(match.group(1))
        cleaned = re.sub(pattern_en, "", text, count=1)
        return cleaned, min_p

    # Hindi / Hinglish: 20 se jyada, 20 se upar
    pattern_hi = (
        rf"{CURRENCY_PATTERN}?"
        r"\s*(\d+(?:\.\d+)?)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        rf"{DISTANCE_UNITS_LOOKAHEAD}"
        r"\s*(?:se jyada|se zyaada|se upar)"
    )
    match_hi = re.search(pattern_hi, text)
    if match_hi:
        min_p = float(match_hi.group(1))
        cleaned = re.sub(pattern_hi, "", text, count=1)
        return cleaned, min_p

    return text, None


def extract_radius(text: str) -> tuple[str, float | None]:
    pattern = (
        r"(?:within|in|under|around|radius)"
        r"\s*(\d+(?:\.\d+)?)\s*"
        r"(km|kms|kilometer|kilometers|mile|miles)\b"
    )
    match = re.search(pattern, text)
    if not match:
        return text, None

    val = float(match.group(1))
    unit = match.group(2).lower()
    radius_km = val * 1.60934 if "mile" in unit else val
    cleaned = re.sub(pattern, "", text, count=1)
    return cleaned, radius_km


def remove_fillers(text: str) -> str:
    cleaned = text
    for phrase in FILLER_PHRASES:
        cleaned = re.sub(rf"\b{re.escape(phrase)}\b", "", cleaned)
    return cleaned


def map_hinglish_terms(text: str) -> tuple[str, dict[str, str]]:
    mapped_terms = {}
    tokens = text.split()
    translated_tokens = []
    
    for token in tokens:
        stripped_token = re.sub(r"[^\w]", "", token)
        if stripped_token in HINGLISH_MAP:
            eng_equiv = HINGLISH_MAP[stripped_token]
            mapped_terms[stripped_token] = eng_equiv
            translated_tokens.append(eng_equiv)
        else:
            translated_tokens.append(token)
            
    return " ".join(translated_tokens), mapped_terms


def normalize_query(raw_query: str) -> NormalizedQueryOutput:
    if not raw_query:
        return NormalizedQueryOutput(
            original_query="",
            cleaned_query="",
            hinglish_terms_mapped={},
        )

    text = clean_text(raw_query)

    # 1. Radius
    text, radius_km = extract_radius(text)

    # 2. Price ranges
    text, min_p, max_p = extract_price_range(text)

    # 3. Max price
    if max_p is None:
        text, max_p = extract_max_price(text)

    # 4. Min price
    if min_p is None:
        text, min_p = extract_min_price(text)

    # 5. Remove conversational fillers
    text = remove_fillers(text)

    # 6. Clean punctuation while preserving alphanumeric characters and spaces
    text = re.sub(r"[^\w\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # 7. Apply Hinglish normalization
    translated_text, mapped_terms = map_hinglish_terms(text)
    translated_text = re.sub(r"\s+", " ", translated_text).strip()

    return NormalizedQueryOutput(
        original_query=raw_query,
        cleaned_query=translated_text,
        min_price=min_p,
        max_price=max_p,
        radius_km=radius_km,
        hinglish_terms_mapped=mapped_terms,
    )
