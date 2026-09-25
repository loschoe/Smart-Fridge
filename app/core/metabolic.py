from typing import Dict, Any

# Coefficients utilisés pour convertir le BMR en dépense énergétique totale.
# Permet d'ajuster selon le niveau d'activité déclaré par l'utilisateur.
ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "high": 1.725,
    "athlete": 1.9
}

# Calcul du métabolisme de base (BMR) via la formule de Mifflin-St Jeor.
# La différence homme/femme se joue uniquement sur la constante finale.
def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    if gender.lower() == "male":
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

# Convertit le BMR en TDEE en appliquant le facteur d'activité.
# Si le niveau est inconnu, on retombe sur "sedentary".
def calculate_tdee(bmr: float, activity_level: str) -> float:
    factor = ACTIVITY_FACTORS.get(activity_level, 1.2)
    return bmr * factor

# Ajuste les calories selon l'objectif : perte, maintien ou prise de masse.
def calculate_target_calories(tdee: float, goal: str) -> float:
    if goal == "loss":
        return tdee - 500
    elif goal == "gain":
        return tdee + 300
    return tdee

# Répartition des macros à partir de l'objectif calorique.
# Protéines et lipides sont fixés en fonction du poids, les glucides complètent le total.
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

# Pipeline complet : calcule BMR, TDEE, objectif calorique et macros.
# Retourne un profil enrichi prêt à être stocké ou affiché.
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