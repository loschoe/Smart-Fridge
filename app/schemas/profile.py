from pydantic import BaseModel, Field, model_validator
from typing import Literal

class ProfileCreate(BaseModel):
    weight_kg: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    age: int = Field(..., gt=0)
    gender: Literal["male", "female"]
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"]
    goal: Literal["loss", "maintain", "gain"]

class ProfileResponse(ProfileCreate):
    user_id: str
    bmr: float
    tdee: float
    target_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float