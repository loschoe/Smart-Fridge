import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Chargement explicite du .env situé à la racine du backend.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Configuration centrale de l’application.
# Toutes les clés sensibles sont chargées depuis le .env
class Settings(BaseSettings):
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    usda_api_key: str = os.getenv("USDA_API_KEY", "DEMO_KEY")
    secret_key: str = os.getenv("SECRET_KEY", "super-secret-key-change-me")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  
    )

# Instance globale utilisée dans tout le backend.
settings = Settings()