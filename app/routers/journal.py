from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.deps import get_current_user_optional
from app.database import supabase
from datetime import datetime, timezone

router = APIRouter(prefix="/journal", tags=["Journal"])

class JournalEntry(BaseModel):
    meal_type: str
    recipe_id: int
    title: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

@router.get("")
@router.get("/")
async def get_journal(user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        return {"meals": [], "totals": {}, "remaining": {}, "percentages": {}}

    prof_res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
    profile = prof_res.data[0] if prof_res.data else {}

    target_cal = float(profile.get("target_calories", 2000))
    target_prot = float(profile.get("protein_g", 150))
    target_carbs = float(profile.get("carbs_g", 200))
    target_fat = float(profile.get("fat_g", 65))

    journal_res = supabase.table("user_journal").select("*").eq("user_id", user_id).execute()
    meals = journal_res.data or []

    tot_cal = sum(m.get("calories", 0) for m in meals)
    tot_prot = sum(m.get("protein_g", 0) for m in meals)
    tot_carbs = sum(m.get("carbs_g", 0) for m in meals)
    tot_fat = sum(m.get("fat_g", 0) for m in meals)

    percentages = {
        "calories": min(100, round((tot_cal / target_cal) * 100)) if target_cal else 0,
        "protein_g": min(100, round((tot_prot / target_prot) * 100)) if target_prot else 0,
        "carbs_g": min(100, round((tot_carbs / target_carbs) * 100)) if target_carbs else 0,
        "fat_g": min(100, round((tot_fat / target_fat) * 100)) if target_fat else 0,
    }

    return {
        "meals": meals,
        "totals": {"calories": tot_cal, "protein_g": round(tot_prot, 1), "carbs_g": round(tot_carbs, 1), "fat_g": round(tot_fat, 1)},
        "remaining": {
            "calories": max(0, int(target_cal - tot_cal)),
            "protein_g": max(0, round(target_prot - tot_prot, 1)),
            "carbs_g": max(0, round(target_carbs - tot_carbs, 1)),
            "fat_g": max(0, round(target_fat - tot_fat, 1))
        },
        "percentages": percentages
    }

@router.post("/add")
async def add_to_journal(entry: JournalEntry, user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    payload = {
        "user_id": str(user_id),
        "recipe_id": int(entry.recipe_id),
        "meal_type": entry.meal_type,
        "title": entry.title,
        "calories": int(entry.calories),
        "protein_g": float(entry.protein_g),
        "carbs_g": float(entry.carbs_g),
        "fat_g": float(entry.fat_g)
    }

    res = supabase.table("user_journal").insert(payload).execute()
    return {"message": "Plat ajouté au journal", "data": res.data}

@router.delete("/{entry_id}")
async def delete_from_journal(entry_id: int, user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    res = supabase.table("user_journal").delete().eq("id", entry_id).eq("user_id", user_id).execute()
    return {"message": "Plat retiré du journal", "data": res.data}

@router.post("/reset")
async def reset_journal(user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    supabase.table("user_journal").delete().eq("user_id", user_id).execute()
    return {"message": "Journal réinitialisé"}