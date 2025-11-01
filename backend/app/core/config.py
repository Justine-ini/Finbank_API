from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    
    model_config = SettingsConfigDict(
        env_file="../../.envs/.env.local",  # Fixed: env_file as key
        env_ignore_empty=True,
        extra='ignore'
    )
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Finbank_API"
    PROJECT_DESCRIPTION: str = "Welcome to Financial Tech with FastAPI"
    SITE_NAME: str = "Finbank"

settings = Settings()