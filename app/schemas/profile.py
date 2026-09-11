from pydantic import BaseModel, Field, field_validator
from typing import Literal

# Alignement strict des niveaux d'activité avec metabolic.py
ActivityType = Literal["sedentary", "light", "moderate", "high", "athlete"]
GoalType = Literal["loss", "maintain", "gain"]

class Profile(BaseModel):
    weight: float = Field(..., gt=0, description="Poids (kg)")
    height: float = Field(..., gt=0, description="Taille (cm)")
    age: int = Field(..., gt=0, description="Âge (années)")
    sex: Literal["male", "female"]
    activity_level: ActivityType
    goal: GoalType

    @field_validator("weight")
    @classmethod
    def check_weight(cls, v: float) -> float:
        if v < 30 or v > 300:
            raise ValueError("Poids irréaliste")
        return v

    @field_validator("height")
    @classmethod
    def check_height(cls, v: float) -> float:
        if v < 120 or v > 250:
            raise ValueError("Taille irréaliste")
        return v

    @field_validator("age")
    @classmethod
    def check_age(cls, v: int) -> int:
        if v < 10 or v > 120:
            raise ValueError("Âge irréaliste")
        return v

class ProfileCreate(BaseModel):
    weight_kg: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    age: int = Field(..., gt=0)
    gender: Literal["male", "female"]
    activity_level: ActivityType
    goal: GoalType

class ProfileResponse(ProfileCreate):
    user_id: str
    bmr: float
    tdee: float
    target_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float