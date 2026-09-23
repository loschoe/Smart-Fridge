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
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)

    return normalized


@router.get("")
@router.get("/")
def get_user_fridge(user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

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

    supabase.table("fridge_items").delete().eq("user_id", user_id).execute()

    if clean_list:
        records = [{"user_id": user_id, "ingredient": item} for item in clean_list]
        supabase.table("fridge_items").insert(records).execute()

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

    clean_ingredient = ingredient.strip().lower()

    (
        supabase.table("fridge_items")
        .delete()
        .eq("user_id", user_id)
        .ilike("ingredient", clean_ingredient)
        .execute()
    )

    res = (
        supabase.table("fridge_items")
        .select("ingredient")
        .eq("user_id", user_id)
        .execute()
    )
    remaining = [row["ingredient"] for row in res.data] if res.data else []

    return {
        "message": f"'{clean_ingredient}' supprimé",
        "ingredients": remaining,
    }