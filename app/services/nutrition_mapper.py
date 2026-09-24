import re

MAPPING = {
    "aubergine": "eggplant",
    "courgette": "zucchini",
    "prawns": "shrimp",
    "biscuits": "cookies",
    "mince": "ground beef",
    "caster sugar": "granulated sugar",
}

def map_ingredient(name: str) -> str:
    """Convert common UK ingredient names to USDA-friendly wording."""
    key = name.lower().strip()
    return MAPPING.get(key, key)


# --- Conversion tables ---
UNIT_TO_GRAMS = {
    "cup": 120.0,
    "tbsp": 15.0,
    "tbs": 15.0,
    "tbls": 15.0,
    "tablespoon": 15.0,
    "tsp": 5.0,
    "teaspoon": 5.0,
    "slice": 30.0,
    "piece": 50.0,
    "clove": 5.0,
    "stick": 113.0,  # butter stick
    "packet": 50.0,
    "bunch": 25.0,
    "handful": 30.0,
    "fillet": 120.0,
    "breast": 150.0,
    "thigh": 100.0,
}

# --- Ingredient-specific overrides ---
INGREDIENT_OVERRIDES = {
    "egg": 50.0,
    "onion": 100.0,
    "lemon": 65.0,
    "garlic": 5.0,
}


def parse_fraction(text: str) -> float:
    """Convert '1/2', '¼', '⅓' etc. to float."""
    unicode_fracs = {
        "¼": 0.25,
        "½": 0.5,
        "¾": 0.75,
        "⅓": 1/3,
        "⅔": 2/3,
    }
    if text in unicode_fracs:
        return unicode_fracs[text]

    if "/" in text:
        try:
            num, den = text.split("/")
            return float(num) / float(den)
        except Exception:
            return None

    try:
        return float(text)
    except Exception:
        return None


def parse_measure_to_grams(measure_str: str) -> float:
    """
    Convert MealDB measure strings to grams.
    Supports cups, tbsp, tsp, slices, pieces, eggs, onions, lemons, etc.
    Falls back to 20 g instead of 100 g.
    """
    if not measure_str:
        return 20.0

    text = measure_str.lower().strip()

    # --- Direct g/kg parsing ---
    match_g = re.search(r"([\d.]+)\s*g\b", text)
    if match_g:
        return float(match_g.group(1))

    match_kg = re.search(r"([\d.]+)\s*kg\b", text)
    if match_kg:
        return float(match_kg.group(1)) * 1000.0

    # --- Extract quantity ---
    qty_match = re.match(r"([\d¼½¾⅓⅔/\.]+)", text)
    qty = 1.0
    if qty_match:
        parsed = parse_fraction(qty_match.group(1))
        if parsed is not None:
            qty = parsed

    # --- Ingredient-specific overrides ---
    for ing, grams in INGREDIENT_OVERRIDES.items():
        if ing in text:
            return qty * grams

    # --- Unit-based conversion ---
    for unit, grams in UNIT_TO_GRAMS.items():
        if unit in text:
            return qty * grams

    # --- Fallback ---
    return qty * 20.0
