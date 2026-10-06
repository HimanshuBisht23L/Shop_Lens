import re

from apis.v1.schemas.search import NormalizedQuery


CURRENCY_PATTERN = r"(?:₹|rs\.?|inr|rupee|rupees|ruppee|ruppees)"

FILLER_PHRASES = [
    "show me",
    "find me",
    "find",
    "i want",
    "i need",
    "give me",
    "please find",
    "please show me",
    "please give me",
]


def clean_text(text: str) -> str:

    text = text.strip().lower()

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text


# Extract price range like --> between 100 and 500
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
    )

    match = re.search(pattern, text)

    if not match:
        return text, None, None

    min_price = float(match.group(1))
    max_price = float(match.group(2))

    text = re.sub(pattern, "", text, count=1)

    return text, min_price, max_price


# Extract Max Price
def extract_max_price(text: str) -> tuple[str, float | None]:

    pattern = (
        r"(?:under|below|less than|upto|up to)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        r"\s*(\d+(?:\.\d+)?)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
    )

    match = re.search(pattern, text)

    if not match:
        return text, None

    max_price = float(match.group(1))

    text = re.sub(pattern, "", text, count=1)

    return text, max_price



# Extract Min Price
def extract_min_price(text: str) -> tuple[str, float | None]:

    pattern = (
        r"(?:above|over|more than|minimum|min)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
        r"\s*(\d+(?:\.\d+)?)"
        r"\s*"
        rf"{CURRENCY_PATTERN}?"
    )

    match = re.search(pattern, text)

    if not match:
        return text, None

    min_price = float(match.group(1))

    text = re.sub(pattern, "", text, count=1)

    return text, min_price


# Currently we convert miles to kilometers -->  within 5 km, within 5 kilometers, under 3 km, within 2 miles
def extract_radius(text: str) -> tuple[str, float | None]:
    
    pattern = (
        r"(?:within|under|inside)"
        r"\s*"
        r"(\d+(?:\.\d+)?)"
        r"\s*"
        r"(km|kilometer|kilometers|mi|mile|miles)"
    )

    match = re.search(pattern, text)

    if not match:
        return text, None

    distance = float(match.group(1))
    unit = match.group(2)

    if unit in {"mi", "mile", "miles"}:
        distance *= 1.60934

    text = re.sub(pattern, "", text, count=1)

    return text, distance


def remove_location_phrases(text: str) -> str:
    
    patterns = [
        r"\bnear me\b",
        r"\bnearby\b",
        r"\bclose to me\b",
        r"\baround me\b",
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text)

    return text


def remove_filler_words(text: str) -> str:
    
    phrases = sorted(
        FILLER_PHRASES,
        key=len,
        reverse=True,
    )

    for phrase in phrases:
        text = re.sub(
            rf"\b{re.escape(phrase)}\b",
            "",
            text,
        )

    return text


def clean_query(text: str) -> str:

    text = re.sub(r"\s+", " ", text)

    text = text.strip(" ,.-")

    return text


def normalize_query(text: str) -> NormalizedQuery:
    
    text = clean_text(text)

    # Price range
    text, min_price, max_price = extract_price_range(text)

    # Maximum price
    if max_price is None:
        text, max_price = extract_max_price(text)

    # Minimum price
    if min_price is None:
        text, min_price = extract_min_price(text)

    # Distance
    text, radius_km = extract_radius(text)

    # Location phrase
    text = remove_location_phrases(text)

    # Filler words
    text = remove_filler_words(text)
    
    # Final query cleanup
    text = clean_query(text)

    return NormalizedQuery(
        query=text,
        min_price=min_price,
        max_price=max_price,
        radius_km=radius_km,
    )


result = normalize_query("chocolate within 5 km")
print(result)