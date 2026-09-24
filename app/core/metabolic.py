from typing import Dict, Any

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "high": 1.725,
    "athlete": 1.9
}

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    if gender.lower() == "male":
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

def calculate_tdee(bmr: float, activity_level: str) -> float:
    factor = ACTIVITY_FACTORS.get(activity_level, 1.2)
    return bmr * factor

def calculate_target_calories(tdee: float, goal: str) -> float:
    if goal == "loss":
        return tdee - 500
    elif goal == "gain":
        return tdee + 300
    return tdee

def calculate_macros(target_calories: float, weight_kg: float) -> Dict[str, float]:
    protein_g = round(weight_kg * 2.0, 1)
    fat_g = round(weight_kg * 1.0, 1)
    
    protein_calories = protein_g * 4
    fat_calories = fat_g * 9
    remaining_calories = max(0, target_calories - (protein_calories + fat_calories))
    
    carbs_g = round(remaining_calories / 4, 1)
    
    return {
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g
    }

def compute_full_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    bmr = calculate_bmr(data["weight_kg"], data["height_cm"], data["age"], data["gender"])
    tdee = calculate_tdee(bmr, data["activity_level"])
    target_calories = calculate_target_calories(tdee, data["goal"])
    macros = calculate_macros(target_calories, data["weight_kg"])
    return {
        **data,
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "target_calories": round(target_calories, 1),
        "protein_g": macros["protein_g"],
        "carbs_g": macros["carbs_g"],
        "fat_g": macros["fat_g"]
    }