from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.deps import get_current_user
from app.database import supabase

router = APIRouter(prefix="/profile", tags=["Profile"])

class ProfileData(BaseModel):
    weight: float
    height: float
    age: int
    gender: str
    activity_level: str
    goal: str
    target_calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

@router.get("")
@router.get("/")
async def get_profile(user_id: str = Depends(get_current_user)):
    res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0]
    return {}

@router.post("")
@router.post("/")
async def save_profile(data: ProfileData, user_id: str = Depends(get_current_user)):
    payload = data.model_dump()
    payload["user_id"] = user_id
    
    # Insère ou met à jour le profil existant
    supabase.table("profiles").upsert(payload).execute()
    return {"message": "Profil mis à jour"}