from fastapi import APIRouter, Depends
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.core.deps import get_current_user
from app.core.metabolic import compute_metabolic_plan
from app.json_store import get_profiles, save_profiles

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.post("/", response_model=ProfileResponse)
def save_user_profile(data: ProfileCreate, user_id: str = Depends(get_current_user)):
    # Utilisation de la fonction centralisée compute_metabolic_plan
    metabolic_data = compute_metabolic_plan(data)

    profile_dict = {
        "user_id": user_id,
        **data.model_dump(),
        **metabolic_data
    }

    profiles = get_profiles()
    profiles = [p for p in profiles if p.get("user_id") != user_id]
    profiles.append(profile_dict)
    save_profiles(profiles)

    return profile_dict