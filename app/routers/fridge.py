import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.deps import get_current_user_optional
from app.json_store import get_fridges, save_fridges
from app.services.usda import validate_ingredient_usda

router = APIRouter(prefix="/fridge", tags=["Fridge"])

class FridgeUpdate(BaseModel):
    ingredients: list[str]

@router.post("")
@router.post("/")
async def update_fridge(
    data: FridgeUpdate, 
    user_id: str | None = Depends(get_current_user_optional)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    fridges = get_fridges()
    user_fridge = next((f for f in fridges if f.get("user_id") == user_id), None)
    old_ingredients = set(user_fridge.get("ingredients", []) if user_fridge else [])

    # On ne teste auprès de l'USDA que ce qui n'était PAS encore dans le frigo
    new_items = [item for item in data.ingredients if item not in old_ingredients]

    if new_items:
        results = await asyncio.gather(*[validate_ingredient_usda(item) for item in new_items])
        
        invalid_ingredients = [item for item, is_valid in zip(new_items, results) if not is_valid]

        if invalid_ingredients:
            raise HTTPException(
                status_code=400, 
                detail=f"Ingrédient(s) introuvable(s) dans la base USDA : {', '.join(invalid_ingredients)}"
            )

    # Sauvegarde de la nouvelle liste
    clean_list = list(dict.fromkeys(data.ingredients)) # conserve l'ordre sans doublons
    if user_fridge:
        user_fridge["ingredients"] = clean_list
    else:
        fridges.append({"user_id": user_id, "ingredients": clean_list})
        
    save_fridges(fridges)
    return {"message": "Frigo mis à jour", "ingredients": clean_list}

@router.delete("/{ingredient}")
async def delete_ingredient(
    ingredient: str, 
    user_id: str | None = Depends(get_current_user_optional)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")

    fridges = get_fridges()
    user_fridge = next((f for f in fridges if f.get("user_id") == user_id), None)

    if user_fridge and "ingredients" in user_fridge:
        # On retire l'ingrédient de la liste
        user_fridge["ingredients"] = [
            i for i in user_fridge["ingredients"] if i.lower() != ingredient.lower()
        ]
        save_fridges(fridges)

    return {"message": f"'{ingredient}' supprimé", "ingredients": user_fridge.get("ingredients", []) if user_fridge else []}