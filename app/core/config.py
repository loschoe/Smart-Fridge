import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

class Settings(BaseSettings):
    usda_api_key: str = os.getenv("USDA_API_KEY", "DEMO_KEY")
    secret_key: str = os.getenv("SECRET_KEY", "super-secret-key-change-me")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24h

    class Config:
        env_file = ".env"

settings = Settings()