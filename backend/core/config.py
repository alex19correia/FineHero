import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Application settings.
    """
    APP_NAME: str = "FineHero AI"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./finehero.db")
    # Add other settings here, e.g., API keys

    class Config:
        env_file = ".env"

settings = Settings()
