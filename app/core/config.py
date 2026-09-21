from pydantic_settings import BaseSettings, SettingsConfigDict

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
