from typing import Any, Dict, List, Optional
from pydantic import BaseModel, model_validator

# Ingrédient MealDB sous forme normalisée.
# "measure" reste brut : MealDB n'est pas cohérent sur les formats.
class IngredientItem(BaseModel):
    name: str
    measure: str

# Modèle MealDB unifié : les 20 paires strIngredientX / strMeasureX
# sont aplaties dans une liste "ingredients".
class MealDBRecipe(BaseModel):
    id: str
    title: str
    thumbnail: str
    instructions: str
    category: Optional[str] = None
    area: Optional[str] = None
    ingredients: List[IngredientItem]

    @model_validator(mode="before")
    @classmethod
    def parse_mealdb_raw(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten TheMealDB's 20 ingredient/measure pairs into one list."""
        if "ingredients" in data:
            return data

        ingredients = []
        for i in range(1, 21):
            ingredient = data.get(f"strIngredient{i}")
            measure = data.get(f"strMeasure{i}")

            if ingredient and str(ingredient).strip():
                ingredients.append({
                    "name": str(ingredient).strip(),
                    "measure": str(measure).strip() if measure else "",
                })

        return {
            "id": data.get("idMeal"),
            "title": data.get("strMeal"),
            "thumbnail": data.get("strMealThumb"),
            "instructions": data.get("strInstructions", ""),
            "category": data.get("strCategory"),
            "area": data.get("strArea"),
            "ingredients": ingredients,
        }

# Macros calculées pour une recette (kcal + macros).
class RecipeNutrients(BaseModel):
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0

# Suggestion complète : recette + macros + type de repas.
class FullRecipeSuggestion(BaseModel):
    recipe: MealDBRecipe
    nutrients: RecipeNutrients
    meal_type: Optional[str] = None   
    meal_label: Optional[str] = None  

# Page paginée de suggestions.
class SuggestionPage(BaseModel):
    recipes: List[FullRecipeSuggestion]
    has_more: bool = False
    offset: int = 0
    limit: int = 3