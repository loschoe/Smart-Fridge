from fastapi import APIRouter
from app.services.mealdb_client import search_recipes_by_ingredient
from app.services.aggregator import aggregate_recipe_macros
from app.core.config import settings

router = APIRouter(prefix="/recipes", tags=["Recipes"])

@router.get("/suggestions")
async def recipe_suggestions(ingredient: str):
    recipes = await search_recipes_by_ingredient(ingredient)

    return [
        {
            "idMeal": recipe.idMeal,
            "recipe_name": recipe.strMeal
        }
        for recipe in recipes[:5]
    ]
