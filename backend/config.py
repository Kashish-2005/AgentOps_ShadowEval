"""
Module: config.py
Project: AgentOps-ShadowEval

This module centralizes application configuration using Pydantic Settings.
"""

from typing import Literal
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings and environment configuration.
    """
    
    # Execution Environment
    APP_ENV: Literal["development", "staging", "production"] = "development"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Persistence
    DB_PATH: str = "./shadoweval.db"
    
    # Agent Logic & Thresholds
    LOOP_THRESHOLD: int = 4
    CONCURRENCY_LIMIT: int = 3
    
    # Monitoring & Security
    PROMETHEUS_ENABLED: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    APP_VERSION: str = "1.0.0"
    ESTIMATED_COST_PER_TOKEN_USD: float = 0.000002

    # LLM Configuration
    USE_REAL_LLM: bool = False
    HUGGINGFACE_API_KEY: str = ""
    HUGGINGFACE_MODEL: str = "facebook/bart-large-cnn"
    
    @property
    def is_production(self) -> bool:
        """Returns True if the application is running in production mode."""
        return self.APP_ENV == "production"
    
    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached singleton instance of the Settings class.
    """
    return Settings()


# Module-level singleton for non-FastAPI imports
settings = get_settings()