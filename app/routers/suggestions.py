from fastapi import APIRouter, Depends
from typing import List
from app.core.deps import get_current_user
from app.json_store import get_fridges
from app.services.mealdb import fetch_recipes_by_ingredient, fetch_recipe_details
from app.services.usda import calculate_recipe_total_nutrients
from app.schemas.recipe import FullRecipeSuggestion, RecipeNutrients

router = APIRouter(prefix="/suggestions", tags=["Suggestions"])

@router.get("/", response_model=List[FullRecipeSuggestion])
async def get_recipe_suggestions(user_id: str = Depends(get_current_user)):
    fridges = get_fridges()
    user_fridge = next((f for f in fridges if f["user_id"] == user_id), None)
    
    if not user_fridge or not user_fridge["ingredients"]:
        return []

    main_ingredient = user_fridge["ingredients"][0]
    raw_recipes = await fetch_recipes_by_ingredient(main_ingredient)
    
    suggestions = []
    for r in raw_recipes[:3]:  # Limiter à 3 recettes pour des raisons de performance
        recipe_detail = await fetch_recipe_details(r["idMeal"])
        if recipe_detail:
            ing_names = [i.name for i in recipe_detail.ingredients]
            nutrients_data = await calculate_recipe_total_nutrients(ing_names)
            suggestions.append(FullRecipeSuggestion(
                recipe=recipe_detail,
                nutrients=RecipeNutrients(**nutrients_data)
            ))

    return suggestions