from pydantic_settings import BaseSettings, SettingsConfigDict
from supabase import create_client, Client

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    secret_key: str | None = None
    usda_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Création du client Supabase
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
