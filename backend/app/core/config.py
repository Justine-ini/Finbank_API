from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    
    model_config = SettingsConfigDict(
        env_file="../../.envs/.env.local",
        env_ignore_empty=True,
        extra='ignore'
    )
    
    API_V1_STR: str = ""
    PROJECT_NAME: str = ""
    PROJECT_DESCRIPTION: str = ""
    SITE_NAME: str = ""
    DATABASE_URL: str = ""

    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int
    MAILPIT_UI_PORT: int

    REDIS_HOST: str = ""
    REDIS_PORT: int
    REDIS_DB: int

    RABBITMQ_HOST: str = ""
    RABBITMQ_POST: int
    RABBITMQ_USER: str = ""
    RABBITMQ_PASSWORD: str = ""

    OTP_EXPIRATION_MINUTES: int = 2 if ENVIRONMENT == "local" else 5
    LOGIN_ATTEMPTS: int = 3
    LOCKOUT_DURATION_MINUTES: int = 2 if ENVIRONMENT == "local" else 5

settings = Settings()