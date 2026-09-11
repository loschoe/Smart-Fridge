import httpx
from functools import lru_cache

USDA_API_KEY = "BG6hpuPoecMjJ8bkUgSx3dl5vHl6NugbrpgFrf9i"

# Client unique réutilisé pour éviter d'ouvrir/fermer une connexion TCP à chaque appel
client = httpx.AsyncClient(timeout=3.0)

# Dictionnaire simple en mémoire pour garder les résultats déjà validés
_VALIDATION_CACHE: dict[str, bool] = {}

async def validate_ingredient_usda(ingredient: str) -> bool:
    clean_item = ingredient.strip().lower()
    
    # 1. Si déjà en cache, réponse instantanée !
    if clean_item in _VALIDATION_CACHE:
        return _VALIDATION_CACHE[clean_item]

    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}&query={clean_item}&pageSize=1"
    
    try:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            is_valid = len(data.get("foods", [])) > 0
            _VALIDATION_CACHE[clean_item] = is_valid  # Sauvegarde en cache
            return is_valid
    except Exception:
        pass

    return False

async def calculate_recipe_total_nutrients(ingredients: list[str]) -> dict:
    return {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}