from pydantic import BaseModel, Field
from typing import Optional

# Représente un ensemble de macros pour 100 g d’un aliment.
# Structure standardisée utilisée dans tout le pipeline USDA.
class MacroBreakdown(BaseModel):
    energy_kcal: float = Field(..., description="Énergie en kcal")
    protein_g: float = Field(..., description="Protéines en grammes")
    fat_g: float = Field(..., description="Lipides en grammes")
    carbs_g: float = Field(..., description="Glucides en grammes")

# Sortie normalisée pour un aliment USDA.
# Permet de stocker l’ID, le nom, et les macros par 100 g.
class USDANutrientOut(BaseModel):
    fdc_id: int
    name: str
    macros_per_100g: MacroBreakdown
