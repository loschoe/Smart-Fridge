from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.deps import get_current_user_optional
from app.database import supabase

router = APIRouter(prefix="/profile", tags=["Profile"])

# Données envoyées par le client pour définir le profil métabolique.
class ProfileData(BaseModel):
    weight_kg: float
    height_cm: float
    age: int
    gender: str
    activity_level: str
    goal: str

# Calcul complet du BMR, TDEE, objectif calorique et macros.
# Version locale (tu as déjà une version centralisée ailleurs).
def calculate_calories(weight: float, height: float, age: int, gender: str, activity_level: str, goal: str):
    if gender == "male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    activity_factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "high": 1.725,
        "athlete": 1.9
    }
    factor = activity_factors.get(activity_level, 1.2)
    tdee = bmr * factor

    goal_adjustments = {
        "loss": -500,
        "maintain": 0,
        "gain": 300
    }
    target_calories = tdee + goal_adjustments.get(goal, 0)

    protein_g = weight * 2.0
    fat_g = weight * 1.0
    remaining_calories = target_calories - (protein_g * 4 + fat_g * 9)
    carbs_g = max(0, remaining_calories / 4)

    return {
        "bmr": int(round(bmr)),
        "tdee": int(round(tdee)),
        "target_calories": int(round(target_calories)),
        "protein_g": float(round(protein_g, 1)),
        "carbs_g": float(round(carbs_g, 1)),
        "fat_g": float(round(fat_g, 1))
    }
# Récupère le profil utilisateur + recalcule les valeurs dérivées.
@router.get("")
@router.get("/")
async def get_profile(user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        return {}
    
    try:
        res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        if res.data:
            profile_data = res.data[0]
            weight = float(profile_data.get("weight", 0))
            height = float(profile_data.get("height", 0))
            age = int(profile_data.get("age", 0))
            gender = str(profile_data.get("gender", "male"))
            activity_level = str(profile_data.get("activity_level", "sedentary"))
            goal = str(profile_data.get("goal", "maintain"))

            calc = calculate_calories(weight, height, age, gender, activity_level, goal)
            profile_data.update(calc)

            profile_data["weight_kg"] = weight
            profile_data["height_cm"] = height

            return profile_data
    except Exception as e:
        print(f"[ERROR PROFILE GET] : {e}")
        
    return {}

# Sauvegarde / mise à jour du profil utilisateur.
@router.post("")
@router.post("/")
async def save_profile(
    data: ProfileData, 
    user_id: str | None = Depends(get_current_user_optional)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    try:
        calc = calculate_calories(
            data.weight_kg, data.height_cm, data.age,
            data.gender, data.activity_level, data.goal
        )

        profile_payload = {
            "user_id": str(user_id),
            "weight": float(data.weight_kg),
            "height": float(data.height_cm),
            "age": int(data.age),
            "gender": str(data.gender),
            "activity_level": str(data.activity_level),
            "goal": str(data.goal),
            "target_calories": int(calc["target_calories"]),
            "protein_g": float(calc["protein_g"]),
            "carbs_g": float(calc["carbs_g"]),
            "fat_g": float(calc["fat_g"])
        }

        res = supabase.table("profiles").upsert(profile_payload).execute()
        return {"message": "Profil mis à jour !", "data": res.data}

    except Exception as e:
        print(f"\n[ERROR PROFILE POST] : {e}\n")
        raise HTTPException(status_code=400, detail=f"Erreur Supabase: {str(e)}")