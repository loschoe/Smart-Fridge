import asyncio
import time
from typing import Optional

import httpx
from pydantic import BaseModel

from app.utils.logger import logger


# USDA FDC nutrient IDs retained for tests/integrations that use the official
# nutrient identifiers instead of nutrient names.
ENERGY_ID = 1008
PROTEIN_ID = 1003
FAT_ID = 1004
CARBS_ID = 1005

USDA_TIMEOUT = httpx.Timeout(
    connect=2.0,
    read=4.0,
    write=4.0,
    pool=2.0,
)

USDA_CONCURRENCY = 8
USDA_FAILURE_CACHE_TTL = 60.0


class USDAMacros(BaseModel):
    energy_kcal: float = 0.0
    protein_g: float = 0.0
    fat_g: float = 0.0
    carbs_g: float = 0.0


class USDAResponse(BaseModel):
    name: str
    macros_per_100g: USDAMacros


# Nutrition data is stable enough for the lifetime of the application.
# Failed lookups are cached only briefly so an unavailable upstream API
# cannot be hammered on every page refresh.
_usda_cache: dict[str, tuple[float, Optional[USDAResponse]]] = {}
_usda_inflight: dict[str, asyncio.Task[Optional[USDAResponse]]] = {}
_semaphore = asyncio.Semaphore(USDA_CONCURRENCY)
_async_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _async_client

    if _async_client is None or _async_client.is_closed:
        _async_client = httpx.AsyncClient(
            timeout=USDA_TIMEOUT,
            limits=httpx.Limits(
                max_connections=USDA_CONCURRENCY,
                max_keepalive_connections=USDA_CONCURRENCY,
            ),
        )

    return _async_client


def _get_cached(key: str) -> Optional[USDAResponse] | None:
    entry = _usda_cache.get(key)
    if entry is None:
        return None

    cached_at, value = entry
    if value is not None:
        return value

    if time.monotonic() - cached_at <= USDA_FAILURE_CACHE_TTL:
        return None

    _usda_cache.pop(key, None)
    return None


def _has_cached_value(key: str) -> bool:
    entry = _usda_cache.get(key)
    if entry is None:
        return False

    cached_at, value = entry
    if value is not None:
        return True

    if time.monotonic() - cached_at <= USDA_FAILURE_CACHE_TTL:
        return True

    _usda_cache.pop(key, None)
    return False


def _extract_macros(food: dict, fallback_name: str) -> USDAResponse:
    macros = USDAMacros()

    for nutrient in food.get("foodNutrients", []):
        nutrient_id = nutrient.get("nutrientId")
        name = str(nutrient.get("nutrientName", "")).lower()
        value = float(nutrient.get("value") or 0.0)
        unit = str(nutrient.get("unitName", "")).lower()

        if nutrient_id == ENERGY_ID and unit == "kcal":
            macros.energy_kcal = value
        elif nutrient_id == PROTEIN_ID:
            macros.protein_g = value
        elif nutrient_id == FAT_ID:
            macros.fat_g = value
        elif nutrient_id == CARBS_ID:
            macros.carbs_g = value
        # Keep the name-based fallback because USDA responses are not always
        # identical between food datasets.
        elif "energy" in name and unit == "kcal":
            macros.energy_kcal = value
        elif "protein" in name:
            macros.protein_g = value
        elif "total lipid" in name or name == "fat":
            macros.fat_g = value
        elif "carbohydrate" in name:
            macros.carbs_g = value

    return USDAResponse(
        name=food.get("description") or fallback_name,
        macros_per_100g=macros,
    )


async def _fetch_usda_nutrients_uncached(
    api_key: str,
    ingredient_name: str,
    cache_key: str,
) -> Optional[USDAResponse]:
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": api_key,
        "query": ingredient_name,
        "pageSize": 1,
    }

    async with _semaphore:
        try:
            response = await _get_client().get(url, params=params)
            response.raise_for_status()

            foods = response.json().get("foods") or []
            if not foods:
                logger.info("[USDA] Aucun résultat pour '%s'", ingredient_name)
                _usda_cache[cache_key] = (time.monotonic(), None)
                return None

            result = _extract_macros(foods[0], ingredient_name)
            _usda_cache[cache_key] = (time.monotonic(), result)
            return result

        except (httpx.HTTPError, ValueError) as exc:
            # Do not dump exceptions/URLs for every ingredient: the UI can
            # continue with the data that is available locally.
            logger.info("[USDA] Lookup indisponible pour '%s' (%s)", ingredient_name, type(exc).__name__)
            _usda_cache[cache_key] = (time.monotonic(), None)
            return None


async def fetch_usda_nutrients(
    api_key: str,
    ingredient_name: str,
) -> Optional[USDAResponse]:
    """Fetch USDA nutrition data with caching, deduplication and bounded concurrency."""
    cleaned_name = ingredient_name.strip().lower()
    if not cleaned_name:
        return None

    if _has_cached_value(cleaned_name):
        return _get_cached(cleaned_name)

    inflight = _usda_inflight.get(cleaned_name)
    if inflight is not None:
        return await asyncio.shield(inflight)

    task = asyncio.create_task(
        _fetch_usda_nutrients_uncached(api_key, ingredient_name, cleaned_name)
    )
    _usda_inflight[cleaned_name] = task

    try:
        return await asyncio.shield(task)
    finally:
        if _usda_inflight.get(cleaned_name) is task:
            _usda_inflight.pop(cleaned_name, None)


async def prefetch_usda_nutrients(
    api_key: str,
    ingredient_names: list[str],
) -> dict[str, Optional[USDAResponse]]:
    """Fetch every distinct ingredient once, in parallel."""
    unique_names = list(dict.fromkeys(
        name.strip().lower()
        for name in ingredient_names
        if name and name.strip()
    ))

    if not unique_names:
        return {}

    results = await asyncio.gather(
        *(fetch_usda_nutrients(api_key, name) for name in unique_names),
        return_exceptions=True,
    )

    return {
        name: (result if isinstance(result, USDAResponse) else None)
        for name, result in zip(unique_names, results)
    }


async def close_client() -> None:
    """Close the shared HTTP client when the application shuts down."""
    global _async_client

    if _async_client is not None and not _async_client.is_closed:
        await _async_client.aclose()

    _async_client = None
