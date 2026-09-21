from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user_optional
from app.database import supabase

router = APIRouter(prefix="/fridge", tags=["Fridge"])


class FridgeUpdate(BaseModel):
    ingredients: list[str]


def _normalize_ingredients(ingredients: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for raw_item in ingredients:
        item = raw_item.strip().lower()
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        normalized.append(item)

    return normalized



@router.get("")
@router.get("/")
def get_user_fridge(user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    # Récupération des ingrédients dans Supabase
    res = (
        supabase.table("fridge_items")
        .select("ingredient")
        .eq("user_id", user_id)
        .execute()
    )
    ingredients = [row["ingredient"] for row in res.data] if res.data else []

    return {"ingredients": ingredients}



@router.post("")
@router.post("/")
async def update_fridge(
    data: FridgeUpdate,
    user_id: str | None = Depends(get_current_user_optional),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    clean_list = _normalize_ingredients(data.ingredients)

    fridges = get_fridges()
    user_fridge = next((f for f in fridges if f.get("user_id") == user_id), None)

    if user_fridge:
        user_fridge["ingredients"] = clean_list
    else:
        fridges.append({
            "user_id": user_id,
            "ingredients": clean_list,
        })

    # Persistence no longer depends on USDA/TheMealDB availability.
    save_fridges(fridges)

    return {
        "message": "Frigo mis à jour",
        "ingredients": clean_list,
    }


@router.delete("/{ingredient}")
async def delete_ingredient(
    ingredient: str,
    user_id: str | None = Depends(get_current_user_optional),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    fridges = get_fridges()
    user_fridge = next((f for f in fridges if f.get("user_id") == user_id), None)

    if user_fridge and "ingredients" in user_fridge:
        user_fridge["ingredients"] = [
            item
            for item in user_fridge["ingredients"]
            if item.lower() != ingredient.lower()
        ]
        save_fridges(fridges)

    return {
        "message": f"'{ingredient}' supprimé",
        "ingredients": remaining,
    }