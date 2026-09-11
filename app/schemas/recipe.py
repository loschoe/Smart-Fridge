from pydantic import BaseModel, model_validator
from typing import List, Dict, Any

class IngredientItem(BaseModel):
    name: str
    measure: str

class MealDBRecipe(BaseModel):
    id: str
    title: str
    thumbnail: str
    instructions: str
    ingredients: List[IngredientItem]

    @model_validator(mode="before")
    @classmethod
    def parse_mealdb_raw(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aplatit les 20 paires strIngredient/strMeasure de TheMealDB"""
        if "ingredients" in data:
            return data

        ingredients = []
        for i in range(1, 21):
            ing = data.get(f"strIngredient{i}")
            measure = data.get(f"strMeasure{i}")
            if ing and ing.strip():
                ingredients.append({
                    "name": ing.strip(),
                    "measure": measure.strip() if measure else ""
                })
        
        return {
            "id": data.get("idMeal"),
            "title": data.get("strMeal"),
            "thumbnail": data.get("strMealThumb"),
            "instructions": data.get("strInstructions", ""),
            "ingredients": ingredients
        }

class RecipeNutrients(BaseModel):
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0

class FullRecipeSuggestion(BaseModel):
    recipe: MealDBRecipe
    nutrients: RecipeNutrients