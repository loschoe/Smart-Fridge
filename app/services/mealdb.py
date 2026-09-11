import httpx
from typing import List
from app.schemas.recipe import MealDBRecipe

BASE_URL = "https://www.themealdb.com/api/json/v1/1"

async def fetch_recipes_by_ingredient(ingredient: str) -> List[dict]:
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/filter.php", params={"i": ingredient})
        if res.status_code != 200:
            return []
        data = res.json()
        return data.get("meals") or []

async def fetch_recipe_details(meal_id: str) -> MealDBRecipe | None:
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/lookup.php", params={"i": meal_id})
        if res.status_code != 200:
            return None
        data = res.json()
        meals = data.get("meals")
        if not meals:
            return None
        return MealDBRecipe.model_validate(meals[0])