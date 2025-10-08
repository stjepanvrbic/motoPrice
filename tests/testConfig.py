"""
Tests for configuration management.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from src.utils.config import AppConfig, getConfig, reloadConfig


@pytest.fixture(autouse=True)
def _resetConfigSingleton():
    """Reset config singleton before each test."""
    import src.utils.config as config_module

    config_module._config = None
    yield
    config_module._config = None


@pytest.fixture()
def tempConfigDir():
    """Create temporary directory for config files."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture()
def sampleYamlConfig(tempConfigDir):
    """Create sample YAML config file."""
    config_data = {
        "database": {"pool_size": 10, "max_overflow": 20, "echo": True},
        "scraping": {
            "sources": ["test1", "test2"],
            "delay_between_requests": 2.5,
            "timeout": 60,
            "max_retries": 5,
        },
        "scoring": {
            "weights": {
                "price": 0.35,
                "mileage": 0.25,
                "quality": 0.15,
                "condition": 0.10,
                "red_flags": 0.10,
                "location": 0.05,
            }
        },
        "ai": {"provider": "local", "model": "llava", "cache_results": False},
        "logging": {"level": "DEBUG", "file": "test.log"},
    }

    config_file = tempConfigDir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    return config_file


def testLoadYamlConfig(sampleYamlConfig, monkeypatch):
    """Loading config from YAML file."""
    # Clear environment variables that might override
    monkeypatch.delenv("DATABASE_POOL_SIZE", raising=False)
    monkeypatch.delenv("DATABASE_MAX_OVERFLOW", raising=False)
    monkeypatch.delenv("SCRAPING_TIMEOUT", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("LOG_FILE", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")  # Required for local provider validation

    config = AppConfig(sampleYamlConfig)

    assert config.database.pool_size == 10
    assert config.database.max_overflow == 20
    assert config.database.echo is True

    assert config.scraping.sources == ["test1", "test2"]
    assert config.scraping.delay_between_requests == 2.5
    assert config.scraping.timeout == 60
    assert config.scraping.max_retries == 5

    assert config.scoring.weight_price == 0.35
    assert config.scoring.weight_mileage == 0.25

    assert config.ai.provider == "local"
    assert config.ai.model == "llava"
    assert config.ai.cache_results is False

    assert config.logging.level == "DEBUG"
    assert config.logging.file == "test.log"


def testEnvironmentVariableOverride(sampleYamlConfig, monkeypatch):
    """Environment variables override YAML config."""
    monkeypatch.setenv("DATABASE_POOL_SIZE", "15")
    monkeypatch.setenv("DATABASE_MAX_OVERFLOW", "25")
    monkeypatch.setenv("SCRAPING_TIMEOUT", "90")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    config = AppConfig(sampleYamlConfig)

    assert config.database.pool_size == 15
    assert config.database.max_overflow == 25
    assert config.scraping.timeout == 90
    assert config.logging.level == "WARNING"


def testMissingConfigFile(tempConfigDir):
    """Loading config when YAML file doesn't exist."""
    nonexistent = tempConfigDir / "nonexistent.yaml"
    config = AppConfig(nonexistent)

    # Should use defaults
    assert config.database.pool_size == 5
    assert config.scraping.delay_between_requests == 1.0


def testDatabaseUrlRequired(sampleYamlConfig, monkeypatch):
    """Database URL validation."""
    # Remove DATABASE_URL if set
    monkeypatch.delenv("DATABASE_URL", raising=False)

    config = AppConfig(sampleYamlConfig)
    # Should have default URL
    assert config.database.url == "postgresql://localhost:5432/motoprice"


def testScoringWeightsValidation(tempConfigDir):
    """Scoring weights must sum to 1.0."""
    invalid_config = {
        "scoring": {
            "weights": {
                "price": 0.5,
                "mileage": 0.3,
                "quality": 0.1,
                "condition": 0.1,
                "red_flags": 0.1,
                "location": 0.1,
            }
        }
    }

    config_file = tempConfigDir / "invalid.yaml"
    with open(config_file, "w") as f:
        yaml.dump(invalid_config, f)

    with pytest.raises(ValueError, match="Scoring weights must sum to 1.0"):
        AppConfig(config_file)


def testOpenAIKeyRequired(tempConfigDir, monkeypatch):
    """OpenAI API key required when using OpenAI provider."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config_data = {"ai": {"provider": "openai"}}
    config_file = tempConfigDir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        AppConfig(config_file)


def testOpenAIKeyNotRequiredForLocal(tempConfigDir, monkeypatch):
    """OpenAI API key not required for local provider."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config_data = {"ai": {"provider": "local"}}
    config_file = tempConfigDir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = AppConfig(config_file)
    assert config.ai.provider == "local"


def testGetConfigSingleton():
    """getConfig returns singleton instance."""
    config1 = getConfig()
    config2 = getConfig()
    assert config1 is config2


def testReloadConfig(sampleYamlConfig, monkeypatch):
    """Reloading config creates new instance."""
    # Clear env vars that might interfere
    monkeypatch.delenv("DATABASE_POOL_SIZE", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    config1 = getConfig()
    reloadConfig(sampleYamlConfig)
    config2 = getConfig()

    assert config1 is not config2
    assert config2.database.pool_size == 10  # From sample YAML


def testDatabaseConfigDefaults(monkeypatch):
    """Database config has proper defaults."""
    from src.utils.config import DatabaseConfig

    # Clear DATABASE_URL if set
    monkeypatch.delenv("DATABASE_URL", raising=False)

    config = DatabaseConfig()
    assert config.url == "postgresql://localhost:5432/motoprice"
    assert config.pool_size == 5
    assert config.max_overflow == 10
    assert config.echo is False


def testScrapingConfigDefaults():
    """Scraping config has proper defaults."""
    from src.utils.config import ScrapingConfig

    config = ScrapingConfig()
    assert config.sources == ["cycletrader", "facebook"]
    assert config.delay_between_requests == 1.0
    assert config.timeout == 30
    assert config.max_retries == 3
    assert config.user_agent_rotation is True


def testScoringConfigDefaults():
    """Scoring config has proper defaults."""
    from src.utils.config import ScoringConfig

    config = ScoringConfig()
    assert config.weight_price == 0.40
    assert config.weight_mileage == 0.20
    assert config.weight_quality == 0.15
    assert config.weight_condition == 0.10
    assert config.weight_red_flags == 0.10
    assert config.weight_location == 0.05


def testAIConfigDefaults():
    """AI config has proper defaults."""
    from src.utils.config import AIConfig

    config = AIConfig()
    assert config.provider == "openai"
    assert config.model == "gpt-4-vision-preview"
    assert config.cache_results is True
    assert config.max_tokens == 1000
    assert config.temperature == 0.1
    assert config.api_key == ""


def testLoggingConfigDefaults():
    """Logging config has proper defaults."""
    from src.utils.config import LoggingConfig

    config = LoggingConfig()
    assert config.level == "INFO"
    assert config.file == "logs/motoprice.log"
    assert config.rotation == "10 MB"
    assert config.retention == "1 month"
    assert config.console is True


def testConfigWithEnvironmentVariables(tempConfigDir, monkeypatch):
    """Full config loading with environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("DATABASE_POOL_SIZE", "20")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_MODEL", "gpt-4")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")

    config_file = tempConfigDir / "config.yaml"
    config_file.write_text("# Empty config\n")

    config = AppConfig(config_file)

    assert config.database.url == "postgresql://test:test@localhost/test"
    assert config.database.pool_size == 20
    assert config.ai.api_key == "sk-test123"
    assert config.ai.provider == "openai"
    assert config.ai.model == "gpt-4"
    assert config.logging.level == "ERROR"
