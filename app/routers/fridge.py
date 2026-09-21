from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user_optional
from app.database import supabase

router = APIRouter(prefix="/fridge", tags=["Fridge"])


class FridgeUpdate(BaseModel):
    ingredients: list[str]


def _normalize_ingredients(ingredients: list[str]) -> list[str]:
    """Normalize and deduplicate ingredient names without any network call."""
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

    try:
        # 1. Supprimer l'ancien frigo de cet utilisateur dans Supabase
        supabase.table("fridge_items").delete().eq("user_id", user_id).execute()

        # 2. Réinsérer les nouveaux ingrédients
        if clean_list:
            records = [
                {"user_id": user_id, "ingredient": item} for item in clean_list
            ]
            supabase.table("fridge_items").insert(records).execute()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur Supabase : {str(e)}"
        )

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

    clean_item = ingredient.strip().lower()

    try:
        # Supprimer la ligne de cet ingrédient spécifique pour cet utilisateur
        supabase.table("fridge_items").delete().eq(
            "user_id", user_id
        ).eq("ingredient", clean_item).execute()

        # Récupérer la liste à jour
        res = (
            supabase.table("fridge_items")
            .select("ingredient")
            .eq("user_id", user_id)
            .execute()
        )
        remaining = [row["ingredient"] for row in res.data] if res.data else []

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur Supabase : {str(e)}"
        )

    return {
        "message": f"'{ingredient}' supprimé",
        "ingredients": remaining,
    }