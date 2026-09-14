from pydantic import BaseModel, Field
from typing import Literal


class ProfileCreate(BaseModel):
    weight_kg: float = Field(..., gt=0, description="Poids en kg")
    height_cm: float = Field(..., gt=0, description="Taille en cm")
    age: int = Field(..., gt=0, lt=120, description="Âge en années")

    gender: Literal["male", "female"]

    activity_level: Literal[
        "sedentary",
        "light",
        "moderate",
        "high",
        "athlete",
    ]

    goal: Literal[
        "loss",
        "maintain",
        "gain",
    ]


class ProfileResponse(ProfileCreate):
    user_id: str

    bmr: float
    tdee: float
    target_calories: float

    protein_g: float
    carbs_g: float
    fat_g: float