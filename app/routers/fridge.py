import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.deps import get_current_user_optional
from app.services.usda import validate_ingredient_usda
from app.database import supabase

router = APIRouter(prefix="/fridge", tags=["Fridge"])

class FridgeUpdate(BaseModel):
    ingredients: list[str]

@router.get("")
@router.get("/")
def get_user_fridge(user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    # Récupération des ingrédients de l'utilisateur dans Supabase
    res = supabase.table("fridge_items").select("ingredient").eq("user_id", user_id).execute()
    ingredients = [row["ingredient"] for row in res.data]
    
    return {"ingredients": ingredients}

@router.post("")
@router.post("/")
async def update_fridge(
    data: FridgeUpdate, 
    user_id: str | None = Depends(get_current_user_optional)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    # 1. Récupération des ingrédients existants en BDD
    res_existing = supabase.table("fridge_items").select("ingredient").eq("user_id", user_id).execute()
    existing_items = set(row["ingredient"] for row in res_existing.data)

    # 2. Nettoyage de la nouvelle liste
    clean_ingredients = list(dict.fromkeys(item.strip().lower() for item in data.ingredients if item.strip()))

    # 3. Validation USDA uniquement pour les NOUVEAUX ingrédients
    new_items = [item for item in clean_ingredients if item not in existing_items]
    if new_items:
        results = await asyncio.gather(*[validate_ingredient_usda(item) for item in new_items])
        invalid_ingredients = [item for item, is_valid in zip(new_items, results) if not is_valid]

        if invalid_ingredients:
            raise HTTPException(
                status_code=400, 
                detail=f"Ingrédient(s) introuvable(s) dans la base USDA : {', '.join(invalid_ingredients)}"
            )

    # 4. Remplacement des ingrédients dans Supabase (supprime les anciens puis insère les nouveaux)
    supabase.table("fridge_items").delete().eq("user_id", user_id).execute()

    if clean_ingredients:
        rows_to_insert = [{"user_id": user_id, "ingredient": item} for item in clean_ingredients]
        supabase.table("fridge_items").insert(rows_to_insert).execute()

    return {"message": "Frigo mis à jour dans Supabase", "ingredients": clean_ingredients}