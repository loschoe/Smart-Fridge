from pydantic import BaseModel, Field
from typing import Optional


class MacroBreakdown(BaseModel):
    energy_kcal: float = Field(..., description="Énergie en kcal")
    protein_g: float = Field(..., description="Protéines en grammes")
    fat_g: float = Field(..., description="Lipides en grammes")
    carbs_g: float = Field(..., description="Glucides en grammes")


class USDANutrientOut(BaseModel):
    fdc_id: int
    name: str
    macros_per_100g: MacroBreakdown
