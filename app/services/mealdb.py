import asyncio
from typing import Any, Optional

import httpx

from app.schemas.recipe import MealDBRecipe
from app.utils.logger import logger


BASE_URL = "https://www.themealdb.com/api/json/v1/1"

MEALDB_TIMEOUT = httpx.Timeout(
    connect=2.0,
    read=4.0,
    write=4.0,
    pool=2.0,
)

MEALDB_CONCURRENCY = 6
MAX_RECIPES_PER_INGREDIENT = 30

_filter_cache: dict[str, list[dict[str, Any]]] = {}
_detail_cache: dict[str, MealDBRecipe] = {}
_detail_inflight: dict[str, asyncio.Task[Optional[MealDBRecipe]]] = {}

_mealdb_semaphore = asyncio.Semaphore(MEALDB_CONCURRENCY)
_async_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _async_client

    if _async_client is None or _async_client.is_closed:
        _async_client = httpx.AsyncClient(
            timeout=MEALDB_TIMEOUT,
            limits=httpx.Limits(
                max_connections=MEALDB_CONCURRENCY,
                max_keepalive_connections=MEALDB_CONCURRENCY,
            ),
        )

    return _async_client


async def _get_json(url: str, params: dict[str, str]) -> Optional[dict[str, Any]]:
    async with _mealdb_semaphore:
        try:
            response = await _get_client().get(url, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("[MealDB] Requête indisponible (%s)", type(exc).__name__)
            return None


async def fetch_recipes_by_ingredient(ingredient: str) -> list[dict[str, Any]]:
    """Return cached MealDB search results for an ingredient."""
    key = ingredient.strip().lower()
    if not key:
        return []

    if key in _filter_cache:
        return _filter_cache[key]

    data = await _get_json(
        f"{BASE_URL}/filter.php",
        {"i": key},
    )
    meals = (data or {}).get("meals") or []
    meals = meals[:MAX_RECIPES_PER_INGREDIENT]

    _filter_cache[key] = meals
    return meals


async def _fetch_recipe_details_uncached(recipe_id: str) -> Optional[MealDBRecipe]:
    data = await _get_json(
        f"{BASE_URL}/lookup.php",
        {"i": recipe_id},
    )
    meals = (data or {}).get("meals") or []

    if not meals:
        return None

    try:
        recipe = MealDBRecipe.model_validate(meals[0])
    except (TypeError, ValueError):
        return None

    _detail_cache[recipe_id] = recipe
    return recipe


async def fetch_recipe_details(recipe_id: str) -> Optional[MealDBRecipe]:
    """Fetch recipe details once and reuse them for suggestions/detail pages."""
    key = str(recipe_id).strip()
    if not key:
        return None

    cached = _detail_cache.get(key)
    if cached is not None:
        return cached

    inflight = _detail_inflight.get(key)
    if inflight is not None:
        return await asyncio.shield(inflight)

    task = asyncio.create_task(_fetch_recipe_details_uncached(key))
    _detail_inflight[key] = task

    try:
        return await asyncio.shield(task)
    finally:
        if _detail_inflight.get(key) is task:
            _detail_inflight.pop(key, None)


async def fetch_recipe_details_many(recipe_ids: list[str]) -> list[MealDBRecipe]:
    """Fetch a small page of recipes concurrently, reusing the detail cache."""
    unique_ids = list(dict.fromkeys(str(recipe_id).strip() for recipe_id in recipe_ids))
    results = await asyncio.gather(
        *(fetch_recipe_details(recipe_id) for recipe_id in unique_ids if recipe_id),
        return_exceptions=True,
    )

    return [
        result
        for result in results
        if isinstance(result, MealDBRecipe)
    ]


async def close_client() -> None:
    """Close the shared HTTP client when the application shuts down."""
    global _async_client

    if _async_client is not None and not _async_client.is_closed:
        await _async_client.aclose()

    _async_client = None
