import httpx
from app.core.config import settings

_VALIDATION_CACHE: dict[str, bool] = {}

async def validate_ingredient_usda(ingredient: str) -> bool:
    clean_item = ingredient.strip().lower()
    
    if clean_item in _VALIDATION_CACHE:
        return _VALIDATION_CACHE[clean_item]

    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={settings.usda_api_key}&query={clean_item}&pageSize=1"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                is_valid = len(data.get("foods", [])) > 0
                _VALIDATION_CACHE[clean_item] = is_valid
                return is_valid
    except Exception:
        pass

    return False

async def calculate_recipe_total_nutrients(ingredients: list[str]) -> dict:
    return {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}