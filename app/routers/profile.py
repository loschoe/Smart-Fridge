from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import RedirectResponse

from app.core.deps import get_current_user
from app.core.metabolic import compute_full_profile
from app.json_store import get_profiles, save_profiles
from app.schemas.profile import ProfileCreate, ProfileResponse

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


@router.post("/")
def update_profile(
    weight_kg: float = Form(...),
    height_cm: float = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    activity_level: str = Form(...),
    goal: str = Form(...),
    user_id: str = Depends(get_current_user),
):
    # Création du profil
    profile_data = ProfileCreate(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age=age,
        gender=gender,
        activity_level=activity_level,
        goal=goal,
    )

    # Calcul métabolique
    computed = compute_full_profile(profile_data.model_dump())
    computed["user_id"] = user_id

    # Récupération des profils existants
    profiles = get_profiles()

    # Suppression de l'ancien profil de cet utilisateur
    profiles = [p for p in profiles if p.get("user_id") != user_id]

    # Ajout du nouveau profil
    profiles.append(computed)

    # Sauvegarde
    save_profiles(profiles)

    # 🔥 Redirection vers la page principale
    return RedirectResponse(
        url="/",
        status_code=303
    )


@router.get("/", response_model=ProfileResponse)
def get_user_profile(
    user_id: str = Depends(get_current_user),
):
    profiles = get_profiles()

    profile = next((p for p in profiles if p.get("user_id") == user_id), None)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil non trouvé",
        )

    # 🔥 Redirection vers la page principale
    return RedirectResponse(
        url="/",
        status_code=303
    )
