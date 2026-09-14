import httpx
from functools import lru_cache
from app.services.translations import translate_to_english

USDA_API_KEY = "BG6hpuPoecMjJ8bkUgSx3dl5vHl6NugbrpgFrf9i"

# Client unique réutilisé pour éviter d'ouvrir/fermer une connexion TCP à chaque appel
client = httpx.AsyncClient(timeout=3.0)

# Dictionnaire simple en mémoire pour garder les résultats déjà validés
_VALIDATION_CACHE: dict[str, bool] = {}

async def validate_ingredient_usda(ingredient: str) -> bool:
    clean_item = ingredient.strip().lower()
    
    # Si l'ingrédient original (ex: "bœuf") est déjà en cache
    if clean_item in _VALIDATION_CACHE:
        return _VALIDATION_CACHE[clean_item]

    # Traduction en anglais pour l'API USDA (ex: "bœuf" -> "beef")
    query_term = translate_to_english(clean_item)

    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}&query={query_term}&pageSize=1"
    
    try:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            is_valid = len(data.get("foods", [])) > 0
            
            # Sauvegarde du terme français en cache
            _VALIDATION_CACHE[clean_item] = is_valid
            return is_valid
    except Exception:
        pass

    return False

async def calculate_recipe_total_nutrients(ingredients: list[str]) -> dict:
    return {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}