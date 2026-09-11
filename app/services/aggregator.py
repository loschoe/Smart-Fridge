import asyncio
from typing import Dict, Any, List

from app.schemas.ingredient import MealDBRecipe
from app.schemas.nutrition import MacroBreakdown
from app.services.usda_client import fetch_usda_nutrients
from app.services.nutrition_mapper import map_ingredient
from app.utils.logger import logger   # ← obligatoire


async def aggregate_recipe_macros(recipe: MealDBRecipe, usda_api_key: str) -> Dict[str, Any]:
    logger.debug(f"[AGG] Agrégation pour recette: {recipe.strMeal}")
    logger.debug(f"[AGG] Ingrédients: {recipe.ingredients}")

    tasks = []

    for ing in recipe.ingredients:
        mapped_name = map_ingredient(ing.name)
        logger.debug(f"[AGG] Mapping {ing.name} -> {mapped_name}")
        tasks.append(fetch_usda_nutrients(usda_api_key, mapped_name))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    logger.debug(f"[AGG] Résultats USDA: {results}")

    total_energy = 0.0
    total_protein = 0.0
    total_fat = 0.0
    total_carbs = 0.0

    valid_ingredients: List[Dict[str, Any]] = []

    for ing, res in zip(recipe.ingredients, results):
        if isinstance(res, Exception) or res is None:
            logger.warning(f"[AGG] USDA introuvable pour {ing.name}")
            continue

        macros = res.macros_per_100g

        total_energy += macros.energy_kcal
        total_protein += macros.protein_g
        total_fat += macros.fat_g
        total_carbs += macros.carbs_g

        valid_ingredients.append({
            "name": ing.name,
            "measure": ing.measure,
            "usda_name": res.name,
            "macros_per_100g": macros.dict()
        })

    return {
        "recipe_name": recipe.strMeal,
        "ingredients_used": valid_ingredients,
        "total_macros": MacroBreakdown(
            energy_kcal=round(total_energy, 2),
            protein_g=round(total_protein, 2),
            fat_g=round(total_fat, 2),
            carbs_g=round(total_carbs, 2),
        ).dict()
    }
