import pytest
import asyncio

from app.schemas.ingredient import MealDBRecipe, IngredientQuantity
from app.services.aggregator import aggregate_recipe_macros


@pytest.mark.asyncio
async def test_aggregator_basic():
    recipe = MealDBRecipe(
        idMeal="1",
        strMeal="Test Meal",
        strIngredient1="Chicken",
        strMeasure1="200 g",
        strIngredient2="Salt",
        strMeasure2="1 tsp",
    )

    # On simule une clé USDA bidon
    result = await aggregate_recipe_macros(recipe, "FAKE_KEY")

    assert "recipe_name" in result
    assert "total_macros" in result
