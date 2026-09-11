from fastapi import APIRouter, Depends
from app.schemas.profile import Profile
from app.core.metabolic import compute_metabolic_plan

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("/metabolic")
def calculate_metabolic(profile: Profile):
    """
    Retourne BMR, TDEE et calories cibles selon l'objectif.
    """
    return compute_metabolic_plan(profile)
