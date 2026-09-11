from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Charge .env dans tous les processus (y compris le reloader)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

class Settings(BaseSettings):
    usda_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
