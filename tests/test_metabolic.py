from app.schemas.profile import Profile
from app.core.metabolic import (
    calculate_bmr,
    calculate_tdee,
    apply_goal_delta,
    compute_metabolic_plan,
)


def test_bmr_male():
    profile = Profile(
        weight=70,
        height=175,
        age=30,
        sex="male",
        activity_level="moderate",
        goal="maintain",
    )
    bmr = calculate_bmr(profile)
    assert round(bmr, 2) == round(10*70 + 6.25*175 - 5*30 + 5, 2)


def test_tdee():
    profile = Profile(
        weight=70,
        height=175,
        age=30,
        sex="male",
        activity_level="moderate",
        goal="maintain",
    )
    tdee = calculate_tdee(profile)
    assert round(tdee, 2) == round(calculate_bmr(profile) * 1.55, 2)


def test_goal_loss():
    assert apply_goal_delta(2500, "loss") == 2000


def test_goal_gain():
    assert apply_goal_delta(2500, "gain") == 2800


def test_compute_plan():
    profile = Profile(
        weight=70,
        height=175,
        age=30,
        sex="male",
        activity_level="moderate",
        goal="loss",
    )
    plan = compute_metabolic_plan(profile)
    assert "bmr" in plan
    assert "tdee" in plan
    assert "target_calories" in plan
