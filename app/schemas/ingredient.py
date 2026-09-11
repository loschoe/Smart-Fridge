from typing import List, Optional
from pydantic import BaseModel, Field, validator

class IngredientQuantity(BaseModel):
    name: str = Field(..., description="Nom de l'ingrédient")
    measure: str = Field(..., description="Quantité brute (ex: '200 g', '1 cup')")


class MealDBRecipe(BaseModel):
    idMeal: str
    strMeal: str
    strInstructions: Optional[str] = None

    # Les 20 paires d'ingrédients / mesures
    strIngredient1: Optional[str] = None
    strIngredient2: Optional[str] = None
    strIngredient3: Optional[str] = None
    strIngredient4: Optional[str] = None
    strIngredient5: Optional[str] = None
    strIngredient6: Optional[str] = None
    strIngredient7: Optional[str] = None
    strIngredient8: Optional[str] = None
    strIngredient9: Optional[str] = None
    strIngredient10: Optional[str] = None
    strIngredient11: Optional[str] = None
    strIngredient12: Optional[str] = None
    strIngredient13: Optional[str] = None
    strIngredient14: Optional[str] = None
    strIngredient15: Optional[str] = None
    strIngredient16: Optional[str] = None
    strIngredient17: Optional[str] = None
    strIngredient18: Optional[str] = None
    strIngredient19: Optional[str] = None
    strIngredient20: Optional[str] = None

    strMeasure1: Optional[str] = None
    strMeasure2: Optional[str] = None
    strMeasure3: Optional[str] = None
    strMeasure4: Optional[str] = None
    strMeasure5: Optional[str] = None
    strMeasure6: Optional[str] = None
    strMeasure7: Optional[str] = None
    strMeasure8: Optional[str] = None
    strMeasure9: Optional[str] = None
    strMeasure10: Optional[str] = None
    strMeasure11: Optional[str] = None
    strMeasure12: Optional[str] = None
    strMeasure13: Optional[str] = None
    strMeasure14: Optional[str] = None
    strMeasure15: Optional[str] = None
    strMeasure16: Optional[str] = None
    strMeasure17: Optional[str] = None
    strMeasure18: Optional[str] = None
    strMeasure19: Optional[str] = None
    strMeasure20: Optional[str] = None

    ingredients: List[IngredientQuantity] = Field(default_factory=list)
    
    @validator("ingredients", always=True)
    def flatten_ingredients(cls, v, values):
        items = []
        for i in range(1, 21):
            ing = values.get(f"strIngredient{i}")
            meas = values.get(f"strMeasure{i}")
            if ing and ing.strip():
                items.append(
                    IngredientQuantity(
                        name=ing.strip(),
                        measure=meas.strip() if meas else ""
                    )
                )
        return items
