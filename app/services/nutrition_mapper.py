MAPPING = {
    "aubergine": "eggplant",
    "courgette": "zucchini",
    "prawns": "shrimp",
    "biscuits": "cookies",
    "mince": "ground beef",
    "caster sugar": "granulated sugar",
    # tu pourras en ajouter au fur et à mesure
}


def map_ingredient(name: str) -> str:
    """
    Convertit un nom UK → US si possible.
    Sinon renvoie le nom original.
    """
    key = name.lower().strip()
    return MAPPING.get(key, name)
