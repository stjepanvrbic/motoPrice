"""
Configuration management for motoPrice.

Loads configuration from:
1. config/config.yaml (defaults)
2. Environment variables (override defaults)
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    url: str = "postgresql://localhost:5432/motoprice"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

    model_config = ConfigDict(env_prefix="DATABASE_")


class ScrapingConfig(BaseSettings):
    """Web scraping configuration."""

    sources: list[str] = ["cycletrader", "facebook"]
    delay_between_requests: float = 1.0
    timeout: int = 30
    max_retries: int = 3
    user_agent_rotation: bool = True

    model_config = ConfigDict(env_prefix="SCRAPING_")


class ScoringConfig(BaseSettings):
    """Scoring algorithm configuration."""

    weight_price: float = 0.40
    weight_mileage: float = 0.20
    weight_quality: float = 0.15
    weight_condition: float = 0.10
    weight_red_flags: float = 0.10
    weight_location: float = 0.05

    model_config = ConfigDict(env_prefix="SCORING_WEIGHT_")


class AIConfig(BaseSettings):
    """AI provider configuration."""

    provider: str = "openai"
    model: str = "gpt-4-vision-preview"
    cache_results: bool = True
    max_tokens: int = 1000
    temperature: float = 0.1
    api_key: str = ""

    model_config = ConfigDict(env_prefix="AI_")


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    file: str = "logs/motoprice.log"
    rotation: str = "10 MB"
    retention: str = "1 month"
    console: bool = True

    model_config = ConfigDict(env_prefix="LOG_")


class AppConfig:
    """Main application configuration."""

    def __init__(self, config_path: Path | None = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to YAML config file (defaults to config/config.yaml)
        """
        if config_path is None:
            config_path = PROJECT_ROOT / "config" / "config.yaml"

        self.config_path = config_path
        self._yaml_config = self._loadYamlConfig()

        # Initialize sub-configs with YAML defaults + env overrides
        self.database = self._initDatabaseConfig()
        self.scraping = self._initScrapingConfig()
        self.scoring = self._initScoringConfig()
        self.ai = self._initAIConfig()
        self.logging = self._initLoggingConfig()

        # Validate required configuration
        self._validate()

    def _loadYamlConfig(self) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            return {}

        with open(self.config_path) as f:
            return yaml.safe_load(f) or {}

    def _initDatabaseConfig(self) -> DatabaseConfig:
        """Initialize database configuration."""
        yaml_db = self._yaml_config.get("database", {})
        return DatabaseConfig(
            url=os.getenv("DATABASE_URL", "postgresql://localhost:5432/motoprice"),
            pool_size=int(os.getenv("DATABASE_POOL_SIZE", yaml_db.get("pool_size", 5))),
            max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", yaml_db.get("max_overflow", 10))),
            echo=yaml_db.get("echo", False),
        )

    def _initScrapingConfig(self) -> ScrapingConfig:
        """Initialize scraping configuration."""
        yaml_scraping = self._yaml_config.get("scraping", {})
        return ScrapingConfig(
            sources=yaml_scraping.get("sources", ["cycletrader", "facebook"]),
            delay_between_requests=float(
                os.getenv(
                    "SCRAPING_DELAY_BETWEEN_REQUESTS",
                    yaml_scraping.get("delay_between_requests", 1.0),
                )
            ),
            timeout=int(os.getenv("SCRAPING_TIMEOUT", yaml_scraping.get("timeout", 30))),
            max_retries=int(os.getenv("SCRAPING_MAX_RETRIES", yaml_scraping.get("max_retries", 3))),
            user_agent_rotation=yaml_scraping.get("user_agent_rotation", True),
        )

    def _initScoringConfig(self) -> ScoringConfig:
        """Initialize scoring configuration."""
        yaml_weights = self._yaml_config.get("scoring", {}).get("weights", {})
        return ScoringConfig(
            weight_price=yaml_weights.get("price", 0.40),
            weight_mileage=yaml_weights.get("mileage", 0.20),
            weight_quality=yaml_weights.get("quality", 0.15),
            weight_condition=yaml_weights.get("condition", 0.10),
            weight_red_flags=yaml_weights.get("red_flags", 0.10),
            weight_location=yaml_weights.get("location", 0.05),
        )

    def _initAIConfig(self) -> AIConfig:
        """Initialize AI configuration."""
        yaml_ai = self._yaml_config.get("ai", {})
        api_key = os.getenv("OPENAI_API_KEY", "")

        return AIConfig(
            provider=os.getenv("AI_PROVIDER", yaml_ai.get("provider", "openai")),
            model=os.getenv("AI_MODEL", yaml_ai.get("model", "gpt-4-vision-preview")),
            cache_results=yaml_ai.get("cache_results", True),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", yaml_ai.get("max_tokens", 1000))),
            temperature=float(os.getenv("AI_TEMPERATURE", yaml_ai.get("temperature", 0.1))),
            api_key=api_key,
        )

    def _initLoggingConfig(self) -> LoggingConfig:
        """Initialize logging configuration."""
        yaml_logging = self._yaml_config.get("logging", {})
        return LoggingConfig(
            level=os.getenv("LOG_LEVEL", yaml_logging.get("level", "INFO")),
            format=yaml_logging.get(
                "format",
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            ),
            file=os.getenv("LOG_FILE", yaml_logging.get("file", "logs/motoprice.log")),
            rotation=yaml_logging.get("rotation", "10 MB"),
            retention=yaml_logging.get("retention", "1 month"),
            console=yaml_logging.get("console", True),
        )

    def _validate(self):
        """Validate required configuration values."""
        errors = []

        # Check database URL
        if not self.database.url:
            errors.append("DATABASE_URL is required")

        # Check OpenAI API key if using OpenAI
        if self.ai.provider == "openai" and not self.ai.api_key:
            errors.append("OPENAI_API_KEY is required when using OpenAI provider")

        # Validate scoring weights sum to 1.0
        total_weight = (
            self.scoring.weight_price
            + self.scoring.weight_mileage
            + self.scoring.weight_quality
            + self.scoring.weight_condition
            + self.scoring.weight_red_flags
            + self.scoring.weight_location
        )
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"Scoring weights must sum to 1.0 (currently {total_weight})")

        if errors:
            raise ValueError(
                "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )


# Global config instance
_config: AppConfig | None = None


def getConfig() -> AppConfig:
    """
    Get global configuration instance.

    Returns:
        AppConfig instance
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reloadConfig(config_path: Path | None = None):
    """
    Reload configuration from file.

    Args:
        config_path: Path to config file (optional)
    """
    global _config
    _config = AppConfig(config_path)
