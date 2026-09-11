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
    }from app.schemas.profile import Profile


# Facteurs d'activité standard
ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "high": 1.725,
    "athlete": 1.9,
}


def calculate_bmr(profile: Profile) -> float:
    """
    Formule de Mifflin-St Jeor
    """
    if profile.sex == "male":
        return 10 * profile.weight + 6.25 * profile.height - 5 * profile.age + 5
    else:
        return 10 * profile.weight + 6.25 * profile.height - 5 * profile.age - 161


def calculate_tdee(profile: Profile) -> float:
    bmr = calculate_bmr(profile)
    factor = ACTIVITY_FACTORS[profile.activity_level]
    return bmr * factor


def apply_goal_delta(tdee: float, goal: str) -> float:
    """
    - perte : -500 kcal
    - maintien : 0
    - prise : +300 kcal
    """
    if goal == "loss":
        return tdee - 500
    elif goal == "gain":
        return tdee + 300
    return tdee


def compute_metabolic_plan(profile: Profile) -> dict:
    """
    Fonction finale utilisée par le backend
    """
    bmr = calculate_bmr(profile)
    tdee = calculate_tdee(profile)
    target_calories = apply_goal_delta(tdee, profile.goal)

    return {
        "bmr": round(bmr, 2),
        "tdee": round(tdee, 2),
        "target_calories": round(target_calories, 2),
    }
