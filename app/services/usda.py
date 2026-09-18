import asyncio

from app.core.config import settings
from app.services.translations import translate_to_english
from app.services.usda_client import fetch_usda_nutrients


_VALIDATION_CACHE: dict[str, bool] = {}


async def validate_ingredient_usda(ingredient: str) -> bool:
    """Optional USDA validation for callers that explicitly need it."""
    clean_item = ingredient.strip().lower()

    if clean_item in _VALIDATION_CACHE:
        return _VALIDATION_CACHE[clean_item]

    query_term = translate_to_english(clean_item)
    api_key = getattr(settings, "usda_api_key", "DEMO_KEY")

    result = await fetch_usda_nutrients(api_key, query_term)
    is_valid = result is not None
    _VALIDATION_CACHE[clean_item] = is_valid
    return is_valid


async def calculate_recipe_total_nutrients(ingredients: list[str]) -> dict:
    """Calculate total nutrients for a list of ingredients without serial I/O."""
    totals = {
        "calories": 0.0,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
    }

    clean_ingredients = list(dict.fromkeys(
        translate_to_english(item).strip().lower()
        for item in ingredients
        if item and item.strip()
    ))

    if not clean_ingredients:
        return totals

    api_key = getattr(settings, "usda_api_key", "DEMO_KEY")
    results = await asyncio.gather(
        *(fetch_usda_nutrients(api_key, item) for item in clean_ingredients),
        return_exceptions=True,
    )

    for result in results:
        if isinstance(result, Exception) or result is None:
            continue

        macros = result.macros_per_100g
        totals["calories"] += macros.energy_kcal
        totals["protein_g"] += macros.protein_g
        totals["carbs_g"] += macros.carbs_g
        totals["fat_g"] += macros.fat_g

    return {
        "calories": round(totals["calories"], 2),
        "protein_g": round(totals["protein_g"], 2),
        "carbs_g": round(totals["carbs_g"], 2),
        "fat_g": round(totals["fat_g"], 2),
    }
