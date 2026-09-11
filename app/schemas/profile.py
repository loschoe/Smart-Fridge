from pydantic import BaseModel, Field, validator
from typing import Literal

class Profile(BaseModel):
    weight: float = Field(..., gt=0, description="Poids (kg)")
    height: float = Field(..., gt=0, description="Taille (cm)")
    age: int = Field(..., gt=0, description="Âge (années)")
    sex: Literal["male", "female"]
    activity_level: Literal["sedentary", "light", "moderate", "high", "athlete"]
    goal: Literal["loss", "maintain", "gain"]

    @validator("weight")
    def check_weight(cls, v):
        if v < 30 or v > 300:
            raise ValueError("Poids irréaliste")
        return v

    @validator("height")
    def check_height(cls, v):
        if v < 120 or v > 250:
            raise ValueError("Taille irréaliste")
        return v

    @validator("age")
    def check_age(cls, v):
        if v < 10 or v > 120:
            raise ValueError("Âge irréaliste")
        return v
