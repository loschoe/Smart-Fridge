from pydantic import BaseModel, Field
from typing import Literal

# Données nécessaires pour créer ou mettre à jour un profil utilisateur.
# Ce modèle correspond aux valeurs saisies par l'utilisateur.
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

# Réponse complète envoyée au frontend après calcul du profil.
# Inclut les valeurs dérivées (BMR, TDEE, macros).
class ProfileResponse(ProfileCreate):
    user_id: str

    bmr: float
    tdee: float
    target_calories: float

    protein_g: float
    carbs_g: float
    fat_g: float