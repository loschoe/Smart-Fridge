from app.schemas.profile import Profile


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
