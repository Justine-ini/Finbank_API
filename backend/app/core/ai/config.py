from pydantic_settings import BaseSettings, SettingsConfigDict

class AISettings(BaseSettings):
    RISK_SCORE_THRESHOLD: float = 0.7
    MODEL_VERSION: str = "1.0.0"
    ANALYSIS_WINDOW_DAYS: str = "90"

    RISK_WEIGHTS: dict[str, float] = {
        "amount": 0.3,
        "time": 0.1,
        "frequency": 0.2,
        "patterns": 0.2,
        "velocity_amount": 0.2,
    }

    PATTERN_WEIGHTS: dict[str, float] = {
        "round_amounts": 0.2,
        "repeated_amounts": 0.2,
        "velocity": 0.6
    }

    TIME_RISK_WEIGHTS: dict[str, float] = {
        "time_of_day": 0.7,
        "day_of_week": 0.3
    }

    HIGH_AMOUNT_THRESHOLD: float = 10000.0

    VELOCITY_THRESHOLD: float = 50000.0

    FREQUENCY_THRESHOLD: int = 5

    HIGH_RISK_SCORE_THRESHOLD: float = 0.7

    BANKING_HOURS_START: int = 9

    BANKING_HOURS_END: int = 17

    BANKING_HOURS_RISK: float = 0.1

    OFF_HOURS_RISK: float = 0.5

    LATE_HOURS_RISK: float = 0.9

    model_config = SettingsConfigDict(
        env_file="../../.envs/.env.local",
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="AI_"
        )
    
ai_settings = AISettings()
