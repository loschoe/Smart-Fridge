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


def parse_measure_to_grams(measure_str: str) -> float:
    """
    Extract grams from g/kg measures.

    The current project has no reliable parser for cups/spoons/pieces, so those
    measures intentionally fall back to 100 g rather than blocking the recipe.
    """
    if not measure_str:
        return 100.0

    text = measure_str.lower().strip()

    match_g = re.search(r"([\d.]+)\s*g\b", text)
    if match_g:
        return float(match_g.group(1))

    match_kg = re.search(r"([\d.]+)\s*kg\b", text)
    if match_kg:
        return float(match_kg.group(1)) * 1000.0

    return 100.0
