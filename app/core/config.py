from pydantic_settings import BaseSettings, SettingsConfigDict

# Modèle de configuration chargé depuis le fichier .env.
# Centralise toutes les variables sensibles nécessaires à l'application.
class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    secret_key: str | None = None
    usda_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file="app/.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()