import os
from dotenv import load_dotenv

# Charge les variables définies dans le fichier .env
load_dotenv()

# Clé de chiffrement pour les tokens JWT
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 jour (1440 minutes)

# Clé API USDA pour la recherche nutritionnelle
USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")