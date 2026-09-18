import asyncio

from fastapi import APIRouter, Depends, Query

from app.core.config import settings
from app.core.deps import get_current_user
from app.json_store import get_fridges, get_profiles
from app.services.mealdb import (
    fetch_recipe_details_many,
    fetch_recipes_by_ingredient,
)
from app.services.aggregator import aggregate_recipe_macros
from app.services.nutrition_mapper import map_ingredient
from app.services.translations import translate_to_english
from app.services.usda_client import prefetch_usda_nutrients
from app.schemas.recipe import (
    FullRecipeSuggestion,
    RecipeNutrients,
    SuggestionPage,
)

router = APIRouter(prefix="/suggestions", tags=["Suggestions"])

MAX_INGREDIENTS_FOR_SEARCH = 3
DEFAULT_PAGE_SIZE = 3
MAX_PAGE_SIZE = 6

# Candidate IDs depend only on the complete fridge fingerprint.
# Keeping this cache in memory is intentionally temporary until the DB migration.
_candidate_cache: dict[tuple[str, ...], list[str]] = {}
MAX_CANDIDATE_CACHE_ENTRIES = 32


async def _get_candidate_ids(fridge_ingredients: list[str]) -> list[str]:
    translated = list(dict.fromkeys(
        translate_to_english(item).strip().lower()
        for item in fridge_ingredients
        if item and item.strip()
    ))

    fingerprint = tuple(sorted(translated))
    cached = _candidate_cache.get(fingerprint)
    if cached is not None:
        return cached

    search_ingredients = translated[:MAX_INGREDIENTS_FOR_SEARCH]

    search_results = await asyncio.gather(
        *(fetch_recipes_by_ingredient(item) for item in search_ingredients),
        return_exceptions=True,
    )

    candidate_ids: list[str] = []
    seen: set[str] = set()

    for result in search_results:
        if isinstance(result, Exception):
            continue

        for recipe in result:
            recipe_id = str(recipe.get("idMeal", "")).strip()
            if recipe_id and recipe_id not in seen:
                seen.add(recipe_id)
                candidate_ids.append(recipe_id)

    if len(_candidate_cache) >= MAX_CANDIDATE_CACHE_ENTRIES:
        _candidate_cache.pop(next(iter(_candidate_cache)))

    _candidate_cache[fingerprint] = candidate_ids
    return candidate_ids


@router.get("/", response_model=SuggestionPage)
async def get_recipe_suggestions(
    user_id: str = Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    """Return one small page of recipe suggestions.

    The front-end asks for three recipes at a time. MealDB candidate searches
    are cached, recipe details are cached, and USDA nutrition is prefetched
    only for the recipes actually displayed on the current page.
    """
    fridges = get_fridges()
    user_fridge = next((f for f in fridges if f.get("user_id") == user_id), None)

    if not user_fridge or not user_fridge.get("ingredients"):
        return SuggestionPage(recipes=[], has_more=False, offset=offset, limit=limit)

    fridge_ingredients = user_fridge["ingredients"]
    candidate_ids = await _get_candidate_ids(fridge_ingredients)

    page_ids = candidate_ids[offset:offset + limit]
    if not page_ids:
        return SuggestionPage(recipes=[], has_more=False, offset=offset, limit=limit)

    recipes = await fetch_recipe_details_many(page_ids)
    if not recipes:
        has_more = offset + limit < len(candidate_ids)
        return SuggestionPage(
            recipes=[],
            has_more=has_more,
            offset=offset,
            limit=limit,
        )

    # Fetch every distinct ingredient for this page only.
    ingredient_names = [
        map_ingredient(ingredient.name).strip().lower()
        for recipe in recipes
        for ingredient in recipe.ingredients
    ]
    api_key = settings.usda_api_key
    nutrient_map = await prefetch_usda_nutrients(api_key, ingredient_names)

    profiles = get_profiles()
    user_profile = next((p for p in profiles if p.get("user_id") == user_id), None)
    target_calories = float(user_profile.get("target_calories", 2000.0)) if user_profile else 2000.0
    target_meal_calories = target_calories / 3.0

    fridge_set = {
        translate_to_english(item).strip().lower()
        for item in fridge_ingredients
    }

    suggestions: list[tuple[float, float, FullRecipeSuggestion]] = []

    for recipe in recipes:
        aggregated = await aggregate_recipe_macros(
            recipe,
            api_key,
            nutrient_map=nutrient_map,
        )

        recipe_ingredients = [
            translate_to_english(ingredient.name).strip().lower()
            for ingredient in recipe.ingredients
        ]
        matched_count = sum(
            1
            for ingredient in recipe_ingredients
            if any(fridge_item in ingredient for fridge_item in fridge_set)
        )
        match_score = matched_count / max(len(recipe_ingredients), 1)

        total_macros = aggregated["total_macros"]
        nutrients = RecipeNutrients(
            calories=total_macros.get("energy_kcal", 0.0),
            protein_g=total_macros.get("protein_g", 0.0),
            carbs_g=total_macros.get("carbs_g", 0.0),
            fat_g=total_macros.get("fat_g", 0.0),
        )

        suggestions.append((
            -match_score,
            abs(nutrients.calories - target_meal_calories),
            FullRecipeSuggestion(recipe=recipe, nutrients=nutrients),
        ))

    suggestions.sort(key=lambda item: (item[0], item[1]))

    response_recipes = [item[2] for item in suggestions]

    return SuggestionPage(
        recipes=response_recipes,
        has_more=offset + limit < len(candidate_ids),
        offset=offset,
        limit=limit,
    )
