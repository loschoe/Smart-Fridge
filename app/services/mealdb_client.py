import httpx
from typing import List, Optional
from app.schemas.ingredient import MealDBRecipe
from app.utils.logger import logger

BASE_URL = "https://www.themealdb.com/api/json/v1/1"


async def safe_get(client: httpx.AsyncClient, url: str) -> Optional[dict]:
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"[MealDB] safe_get error: {e}")
        return None


async def search_recipes_by_ingredient(ingredient: str) -> List[MealDBRecipe]:
    logger.debug(f"[MealDB] Recherche de recettes pour ingrédient: {ingredient}")

    url = f"{BASE_URL}/filter.php?i={ingredient}"

    async with httpx.AsyncClient(timeout=10) as client:
        # 1) Appel filter.php
        data = await safe_get(client, url)
        logger.debug(f"[MealDB] Réponse filter.php: {data}")

        if not data or not data.get("meals"):
            logger.warning(f"[MealDB] Aucun résultat pour {ingredient}")
            return []

        recipes = []

        # 2) Appels lookup.php
        for meal in data["meals"][:5]:
            details_url = f"{BASE_URL}/lookup.php?i={meal['idMeal']}"
            logger.debug(f"[MealDB] Lookup URL: {details_url}")

            detail_data = await safe_get(client, details_url)
            logger.debug(f"[MealDB] Réponse lookup: {detail_data}")

            if detail_data and detail_data.get("meals"):
                recipes.append(MealDBRecipe(**detail_data["meals"][0]))

    logger.debug(f"[MealDB] Recettes finales: {recipes}")
    return recipes
