from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    """
    Application settings.
    """
    APP_NAME: str = "FineHero AI"
    DATABASE_URL: str = "sqlite:///./finehero.db"
    
    # External API Keys
    GOOGLE_AI_API_KEY: str = ""
    
    # JWT Configuration
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Other settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Validate SECRET_KEY is set and not empty
if not settings.SECRET_KEY:
    if not settings.DEBUG:
        raise RuntimeError(
            "SECRET_KEY environment variable must be set in production. "
            "Set SECRET_KEY in your .env file or environment."
        )
    else:
        # For development, generate a random secret if not set
        import secrets
        settings.SECRET_KEY = secrets.token_urlsafe(32)
