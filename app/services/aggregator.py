from typing import Any, Dict, List, Mapping, Optional

from app.schemas.recipe import MealDBRecipe
from app.schemas.nutrition import MacroBreakdown
from app.services.usda_client import USDAResponse, fetch_usda_nutrients, prefetch_usda_nutrients
from app.services.nutrition_mapper import map_ingredient, parse_measure_to_grams
from app.utils.logger import logger


async def aggregate_recipe_macros(
    recipe: MealDBRecipe,
    usda_api_key: str,
    nutrient_map: Optional[Mapping[str, Optional[USDAResponse]]] = None,
) -> Dict[str, Any]:
    """
    Calculate recipe macros locally from USDA values.

    When nutrient_map is provided, no extra USDA request is performed for
    ingredients already prefetched for the current page.
    """
    recipe_title = recipe.title
    logger.debug("[AGG] Agrégation pour recette: %s", recipe_title)

    normalized_names = [
        map_ingredient(ingredient.name).strip().lower()
        for ingredient in recipe.ingredients
    ]

    if nutrient_map is None:
        nutrient_map = await prefetch_usda_nutrients(
            usda_api_key,
            normalized_names,
        )

    total_energy = 0.0
    total_protein = 0.0
    total_fat = 0.0
    total_carbs = 0.0

    valid_ingredients: List[Dict[str, Any]] = []

    for ingredient, normalized_name in zip(recipe.ingredients, normalized_names):
        result = nutrient_map.get(normalized_name)

        # Compatibility fallback for callers that pass an incomplete map.
        if normalized_name not in nutrient_map:
            result = await fetch_usda_nutrients(usda_api_key, normalized_name)

        if result is None:
            logger.debug("[AGG] USDA introuvable pour %s", ingredient.name)
            continue

        weight_grams = parse_measure_to_grams(ingredient.measure)
        ratio = weight_grams / 100.0
        macros = result.macros_per_100g

        total_energy += macros.energy_kcal * ratio
        total_protein += macros.protein_g * ratio
        total_fat += macros.fat_g * ratio
        total_carbs += macros.carbs_g * ratio

        valid_ingredients.append({
            "name": ingredient.name,
            "measure": ingredient.measure,
            "calculated_grams": weight_grams,
            "usda_name": result.name,
            "macros": {
                "energy_kcal": round(macros.energy_kcal * ratio, 2),
                "protein_g": round(macros.protein_g * ratio, 2),
                "fat_g": round(macros.fat_g * ratio, 2),
                "carbs_g": round(macros.carbs_g * ratio, 2),
            },
        })

    return {
        "recipe_name": recipe_title,
        "ingredients_used": valid_ingredients,
        "total_macros": MacroBreakdown(
            energy_kcal=round(total_energy, 2),
            protein_g=round(total_protein, 2),
            fat_g=round(total_fat, 2),
            carbs_g=round(total_carbs, 2),
        ).model_dump(),
    }
