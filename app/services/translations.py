TRANSLATIONS = {
    # Viandes / Poissons
    "poulet": "chicken",
    "oeuf": "egg",
    "œuf": "egg",
    "boeuf": "beef",
    "bœuf": "beef",
    "porc": "pork",
    "saumon": "salmon",
    "thon": "tuna",
    
    # Produits laitiers
    "beurre": "butter",
    "fromage": "cheese",
    "lait": "milk",
    
    # Féculents / Légumes
    "riz": "rice",
    "pates": "pasta",
    "pâtes": "pasta",
    "tomate": "tomato",
    "pomme de terre": "potato",
    "oignon": "onion",
    "ail": "garlic",
    "carotte": "carrot",
    "huile d'olive": "olive oil",
}

def translate_to_english(ingredient_fr: str) -> str:
    # Convertit un aliment français vers anglais
    clean_item = ingredient_fr.strip().lower()
    return TRANSLATIONS.get(clean_item, clean_item)