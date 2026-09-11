from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

class IngredientQuantity(BaseModel):
    name: str = Field(..., description="Nom de l'ingrédient")
    measure: str = Field(..., description="Quantité brute (ex: '200 g', '1 cup')")

class MealDBRecipe(BaseModel):
    idMeal: str
    strMeal: str
    strInstructions: Optional[str] = None
    ingredients: List[IngredientQuantity] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def flatten_ingredients(cls, data: dict) -> dict:
        if isinstance(data, dict) and "ingredients" not in data:
            items = []
            for i in range(1, 21):
                ing = data.get(f"strIngredient{i}")
                meas = data.get(f"strMeasure{i}")
                if ing and str(ing).strip():
                    items.append({
                        "name": str(ing).strip(),
                        "measure": str(meas).strip() if meas else ""
                    })
            data["ingredients"] = items
        return data