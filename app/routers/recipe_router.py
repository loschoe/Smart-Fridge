from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.services.mealdb import fetch_recipe_details
from app.services.aggregator import aggregate_recipe_macros


router = APIRouter(prefix="/recipe", tags=["Recipe Details"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/{recipe_id}")
async def view_recipe_detail(recipe_id: str, request: Request):
    recipe_detail = await fetch_recipe_details(recipe_id)

    if not recipe_detail:
        raise HTTPException(status_code=404, detail="Recette introuvable")

    usda_api_key = settings.usda_api_key
    aggregated = await aggregate_recipe_macros(recipe_detail, usda_api_key)

    return templates.TemplateResponse(
        request=request,
        name="recipe.html",
        context={
            "recipe": recipe_detail,
            "nutrients": aggregated.get("total_macros", {}),
            "ingredients_used": aggregated.get("ingredients_used", []),
        },
    )
