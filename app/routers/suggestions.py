import asyncio
import re

from fastapi import APIRouter, Depends, Query

from app.core.config import settings
from app.core.deps import get_current_user
from app.database import supabase
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

DEFAULT_PAGE_SIZE = 3
MAX_PAGE_SIZE = 6

# Cache interne pour éviter de recalculer les candidats MealDB
_candidate_cache: dict[tuple[str, ...], list[str]] = {}
MAX_CANDIDATE_CACHE_ENTRIES = 32

# Normalisation légère pour les recherches MealDB
def normalize_for_mealdb(name: str) -> str:
    """
    Normalise un ingrédient pour les recherches et comparaisons MealDB.
    """
    name = name.lower().strip()

    replacements = {
        "bay leaves": "bay leaf",
        "dry white wine": "white wine",
        "ginger cordial": "ginger",
        "spring onions": "green onion",
        "black olives": "olives",
    }

    return replacements.get(name, name)

# Normalisation avancée pour comparer frigo ↔ recette
def normalize_ingredient(name: str) -> str:
    """
    Normalisation plus poussée pour comparer les ingrédients
    du frigo avec ceux des recettes.
    """
    name = translate_to_english(name)
    name = normalize_for_mealdb(name)

    name = re.sub(r"[^a-z0-9\s-]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()

    replacements = {
        "minced beef": "beef",
        "ground beef": "beef",
        "beef mince": "beef",
        "minced pork": "pork",
        "ground pork": "pork",
        "chicken breast": "chicken",
        "chicken breasts": "chicken",
        "chicken thigh": "chicken",
        "chicken thighs": "chicken",
        "cheddar cheese": "cheese",
        "mozzarella cheese": "cheese",
        "parmesan cheese": "cheese",
        "grated cheese": "cheese",
        "cheese grated": "cheese",
    }

    return replacements.get(name, name)

# Logique de matching frigo ↔ recette
def ingredient_matches(fridge_ingredient: str, recipe_ingredient: str) -> bool:
    fridge = normalize_ingredient(fridge_ingredient)
    recipe = normalize_ingredient(recipe_ingredient)

    if not fridge or not recipe:
        return False

    if fridge == recipe:
        return True

    if fridge.endswith("s") and fridge[:-1] == recipe:
        return True

    if recipe.endswith("s") and recipe[:-1] == fridge:
        return True

    fridge_words = set(fridge.split())
    recipe_words = set(recipe.split())

    if len(fridge_words) == 1 and fridge in recipe_words:
        return True

    return False

# Score de compatibilité frigo ↔ recette
def calculate_recipe_score(
    fridge_ingredients: list[str],
    recipe_ingredients: list[str],
) -> tuple[float, dict]:
    fridge = list(dict.fromkeys(
        normalize_ingredient(item)
        for item in fridge_ingredients
        if item and item.strip()
    ))

    recipe = list(dict.fromkeys(
        normalize_ingredient(item)
        for item in recipe_ingredients
        if item and item.strip()
    ))

    if not fridge or not recipe:
        return 0.0, {
            "matched": 0,
            "missing": len(recipe),
            "fridge_used": 0,
            "recipe_size": len(recipe),
        }

    matched_fridge: set[str] = set()
    matched_recipe: set[str] = set()

    for fridge_item in fridge:
        for recipe_item in recipe:
            if recipe_item in matched_recipe:
                continue

            if ingredient_matches(fridge_item, recipe_item):
                matched_fridge.add(fridge_item)
                matched_recipe.add(recipe_item)
                break

    matched_count = len(matched_fridge)
    missing_count = len(recipe) - len(matched_recipe)
    fridge_count = len(fridge)
    recipe_size = len(recipe)

    fridge_usage_ratio = matched_count / max(fridge_count, 1)

    score = 0.0
    score += matched_count * 100.0
    score += fridge_usage_ratio * 80.0
    score -= missing_count * 35.0

    if len(fridge) <= 1:
        if recipe_size <= 3:
            score += 45.0
        elif recipe_size <= 5:
            score += 20.0
        elif recipe_size <= 7:
            score += -25.0
        else:
            score -= (recipe_size - 6) * 15.0

    elif len(fridge) <= 3:
        if recipe_size <= 4:
            score += 30.0
        elif recipe_size <= 6:
            score += 10.0
        elif recipe_size > 8:
            score -= (recipe_size - 8) * 10.0

    else:
        if recipe_size <= 5:
            score += 15.0
        elif recipe_size > 10:
            score -= (recipe_size - 10) * 5.0

    if matched_count == fridge_count:
        score += 100.0

    if fridge_count > 1 and matched_count == 1:
        score -= 30.0

    if missing_count >= 5:
        score -= 40.0

    if missing_count >= 8:
        score -= 60.0

    return score, {
        "matched": matched_count,
        "missing": missing_count,
        "fridge_used": matched_count,
        "recipe_size": recipe_size,
        "fridge_count": fridge_count,
        "usage_ratio": fridge_usage_ratio,
    }

# Recherche des recettes candidates via MealDB (avec cache)
async def _get_candidate_ids(fridge_ingredients: list[str]) -> list[str]:
    translated = [
        normalize_for_mealdb(
            translate_to_english(item).strip().lower()
        )
        for item in fridge_ingredients
        if item and item.strip()
    ]

    fingerprint = tuple(sorted(set(translated)))

    cached = _candidate_cache.get(fingerprint)
    if cached is not None:
        return cached

    search_results = await asyncio.gather(
        *(fetch_recipes_by_ingredient(item) for item in fingerprint),
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

# Associe un type de repas selon la position dans la journée
def _categorize_meal_type(index: int) -> tuple[str, str]:
    """
    Associe un type et un libellé selon le rang de la carte dans la journée.
    0 = Petit-déjeuner (Sucré)
    1 = Déjeuner (Copieux)
    2 = Dîner (Simple)
    """
    meal_map = {
        0: ("breakfast", "Petit-Déjeuner (Sucré)"),
        1: ("lunch", "Déjeuner (Copieux)"),
        2: ("dinner", "Dîner (Simple)")
    }
    return meal_map.get(index % 3, ("meal", "Repas"))

# Endpoint principal : suggestions de recettes
@router.get("/", response_model=SuggestionPage)
async def get_recipe_suggestions(
    user_id: str = Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    res = (
        supabase
        .table("fridge_items")
        .select("ingredient")
        .eq("user_id", user_id)
        .execute()
    )

    fridge_ingredients = [
        row["ingredient"]
        for row in res.data
        if row.get("ingredient")
    ]

    if not fridge_ingredients:
        return SuggestionPage(
            recipes=[],
            has_more=False,
            offset=offset,
            limit=limit,
        )

    candidate_ids = await _get_candidate_ids(fridge_ingredients)

    if not candidate_ids:
        return SuggestionPage(
            recipes=[],
            has_more=False,
            offset=offset,
            limit=limit,
        )

    recipes = await fetch_recipe_details_many(candidate_ids)

    if not recipes:
        return SuggestionPage(
            recipes=[],
            has_more=False,
            offset=offset,
            limit=limit,
        )

    ingredient_names = [
        map_ingredient(ingredient.name).strip().lower()
        for recipe in recipes
        for ingredient in recipe.ingredients
    ]

    ingredient_names = list(dict.fromkeys(ingredient_names))

    api_key = settings.usda_api_key

    nutrient_map = await prefetch_usda_nutrients(
        api_key,
        ingredient_names,
    )

    profiles = (
        supabase
        .table("profiles")
        .select("*")
        .eq("user_id", user_id)
        .execute()
        .data
    )

    user_profile = profiles[0] if profiles else None

    target_calories = (
        float(user_profile.get("target_calories", 2000.0))
        if user_profile
        else 2000.0
    )

    target_meal_calories = target_calories / 3.0

    suggestions: list[
        tuple[
            float,
            int,
            int,
            float,
            FullRecipeSuggestion,
        ]
    ] = []

    for recipe in recipes:
        recipe_ingredient_names = [
            ingredient.name
            for ingredient in recipe.ingredients
        ]

        compatibility_score, compatibility = calculate_recipe_score(
            fridge_ingredients,
            recipe_ingredient_names,
        )

        matched_count = compatibility["matched"]
        missing_count = compatibility["missing"]
        recipe_size = compatibility["recipe_size"]

        aggregated = await aggregate_recipe_macros(
            recipe,
            api_key,
            nutrient_map=nutrient_map,
        )

        if not aggregated or "total_macros" not in aggregated:
            continue

        total_macros = aggregated["total_macros"] or {}

        nutrients = RecipeNutrients(
            calories=total_macros.get("energy_kcal", 0.0),
            protein_g=total_macros.get("protein_g", 0.0),
            carbs_g=total_macros.get("carbs_g", 0.0),
            fat_g=total_macros.get("fat_g", 0.0),
        )

        calorie_difference = abs(
            nutrients.calories - target_meal_calories
        )

        suggestions.append(
            (
                -compatibility_score,
                missing_count,
                recipe_size,
                calorie_difference,
                FullRecipeSuggestion(
                    recipe=recipe,
                    nutrients=nutrients,
                ),
            )
        )

    suggestions.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2],
            item[3],
        )
    )

    total_suggestions = len(suggestions)

    page = suggestions[
        offset:offset + limit
    ]

    response_recipes = []
    for idx, item in enumerate(page):
        suggestion = item[4]
        meal_type, meal_label = _categorize_meal_type(offset + idx)
        suggestion.meal_type = meal_type
        suggestion.meal_label = meal_label

        response_recipes.append(suggestion)

    return SuggestionPage(
        recipes=response_recipes,
        has_more=offset + limit < total_suggestions,
        offset=offset,
        limit=limit,
    )
