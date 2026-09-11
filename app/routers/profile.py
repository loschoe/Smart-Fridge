from fastapi import APIRouter, Depends
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.core.deps import get_current_user
from app.core.metabolic import calculate_bmr, calculate_tdee, calculate_target_macros
from app.json_store import get_profiles, save_profiles

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.post("/", response_model=ProfileResponse)
def save_user_profile(data: ProfileCreate, user_id: str = Depends(get_current_user)):
    bmr = calculate_bmr(data.weight_kg, data.height_cm, data.age, data.gender)
    tdee = calculate_tdee(bmr, data.activity_level)
    targets = calculate_target_macros(tdee, data.goal)

    profile_dict = {
        "user_id": user_id,
        **data.model_dump(),
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        **targets
    }

    profiles = get_profiles()
    profiles = [p for p in profiles if p["user_id"] != user_id]
    profiles.append(profile_dict)
    save_profiles(profiles)

    return profile_dict