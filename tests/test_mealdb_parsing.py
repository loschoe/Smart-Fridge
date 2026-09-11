from app.schemas.ingredient import MealDBRecipe


def test_flatten_ingredients():
    data = {
        "idMeal": "12345",
        "strMeal": "Test Meal",
        "strIngredient1": "Chicken",
        "strMeasure1": "200 g",
        "strIngredient2": "Salt",
        "strMeasure2": "1 tsp",
        "strIngredient3": "",
        "strMeasure3": "",
    }

    recipe = MealDBRecipe(**data)

    assert len(recipe.ingredients) == 2
    assert recipe.ingredients[0].name == "Chicken"
    assert recipe.ingredients[0].measure == "200 g"
    assert recipe.ingredients[1].name == "Salt"
    assert recipe.ingredients[1].measure == "1 tsp"
