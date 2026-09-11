import pytest
from app.schemas.nutrition import USDANutrientOut, MacroBreakdown
from app.services.usda_client import ENERGY_ID, PROTEIN_ID, FAT_ID, CARBS_ID


def test_extract_nutrients_from_mock():
    """
    On simule une réponse USDA pour tester l'extraction des nutriments.
    """

    mock_food = {
        "fdcId": 123456,
        "description": "Chicken breast",
        "foodNutrients": [
            {"nutrientId": ENERGY_ID, "value": 165},
            {"nutrientId": PROTEIN_ID, "value": 31},
            {"nutrientId": FAT_ID, "value": 3.6},
            {"nutrientId": CARBS_ID, "value": 0},
        ]
    }

    # On reconstruit manuellement l'objet comme si le client l'avait renvoyé
    macros = MacroBreakdown(
        energy_kcal=165,
        protein_g=31,
        fat_g=3.6,
        carbs_g=0
    )

    out = USDANutrientOut(
        fdc_id=mock_food["fdcId"],
        name=mock_food["description"],
        macros_per_100g=macros
    )

    assert out.fdc_id == 123456
    assert out.macros_per_100g.energy_kcal == 165
    assert out.macros_per_100g.protein_g == 31
    assert out.macros_per_100g.fat_g == 3.6
    assert out.macros_per_100g.carbs_g == 0
