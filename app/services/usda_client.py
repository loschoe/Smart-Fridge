import httpx
from typing import Optional
from app.schemas.nutrition import MacroBreakdown, USDANutrientOut
from app.utils.logger import logger   # ← obligatoire

BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

ENERGY_ID = 1008
PROTEIN_ID = 1003
FAT_ID = 1004
CARBS_ID = 1005


async def fetch_usda_nutrients(api_key: str, ingredient_name: str) -> Optional[USDANutrientOut]:
    logger.debug(f"[USDA] Query: {ingredient_name}")

    params = {
        "api_key": api_key,
        "query": ingredient_name,
        "dataType": ["SR Legacy", "Foundation"],
        "pageSize": 1
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(BASE_URL, params=params)
            logger.debug(f"[USDA] Status: {resp.status_code}")
            logger.debug(f"[USDA] Raw response: {resp.text}")
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[USDA] Erreur: {e}")
            return None

    foods = data.get("foods")
    logger.debug(f"[USDA] Foods: {foods}")

    if not foods:
        logger.warning(f"[USDA] Aucun aliment trouvé pour {ingredient_name}")
        return None

    food = foods[0]
    nutrients = food.get("foodNutrients", [])

    def get_value(nutrient_id):
        for n in nutrients:
            if n.get("nutrientId") == nutrient_id:
                return n.get("value")
        return None

    energy = get_value(ENERGY_ID)
    protein = get_value(PROTEIN_ID)
    fat = get_value(FAT_ID)
    carbs = get_value(CARBS_ID)

    if None in (energy, protein, fat, carbs):
        logger.warning(f"[USDA] Nutriments incomplets pour {ingredient_name}")
        return None

    macros = MacroBreakdown(
        energy_kcal=energy,
        protein_g=protein,
        fat_g=fat,
        carbs_g=carbs
    )

    return USDANutrientOut(
        fdc_id=food["fdcId"],
        name=food["description"],
        macros_per_100g=macros
    )
