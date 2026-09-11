def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """Formule de Mifflin-St Jeor"""
    if gender == "male":
        return (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        return (10 * weight) + (6.25 * height) - (5 * age) - 161

def calculate_tdee(bmr: float, activity_level: str) -> float:
    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    return bmr * multipliers.get(activity_level, 1.2)

def calculate_target_macros(tdee: float, goal: str) -> dict:
    if goal == "loss":
        target_cal = tdee - 500
    elif goal == "gain":
        target_cal = tdee + 300
    else:
        target_cal = tdee

    # Macros (30% Protéines, 40% Glucides, 30% Lipides)
    protein_g = (target_cal * 0.30) / 4
    carbs_g = (target_cal * 0.40) / 4
    fat_g = (target_cal * 0.30) / 9

    return {
        "target_calories": round(target_cal, 1),
        "protein_g": round(protein_g, 1),
        "carbs_g": round(carbs_g, 1),
        "fat_g": round(fat_g, 1)
    }