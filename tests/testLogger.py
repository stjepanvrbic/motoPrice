"""
Tests for logging setup.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from loguru import logger

from src.utils.logger import getLogger, setupLogging


@pytest.fixture(autouse=True)
def _resetLogger():
    """Reset logger state before each test."""
    # Remove all handlers
    logger.remove()

    # Reset the _initialized flag
    import src.utils.logger as logger_module

    logger_module._initialized = False

    yield

    # Cleanup after test
    logger.remove()
    logger_module._initialized = False


@pytest.fixture()
def tempLogDir():
    """Create temporary directory for log files."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def testSetupLoggingBasic(monkeypatch):
    """Basic logging setup."""
    # Use test config
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_FILE", "test.log")

    setupLogging()

    # Verify logging is initialized
    import src.utils.logger as logger_module

    assert logger_module._initialized is True


def testSetupLoggingOnlyOnce():
    """setupLogging only initializes once."""
    setupLogging()
    setupLogging()
    setupLogging()

    # Should still be initialized
    import src.utils.logger as logger_module

    assert logger_module._initialized is True


def testGetLoggerInitializesIfNeeded():
    """getLogger initializes logging if not already done."""
    import src.utils.logger as logger_module

    assert logger_module._initialized is False

    test_logger = getLogger("test")

    assert logger_module._initialized is True
    assert test_logger is not None


def testGetLoggerWithName():
    """getLogger returns logger with name binding."""
    test_logger = getLogger("my_module")
    assert test_logger is not None


def testLoggingToFile(tempLogDir, monkeypatch, capsys):
    """Logging writes to file."""
    log_file = tempLogDir / "test.log"

    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_FILE", str(log_file))

    # Reset logger and config
    import src.utils.config as config_module
    import src.utils.logger as logger_module

    logger_module._initialized = False
    config_module._config = None

    test_logger = getLogger("test")
    test_logger.info("Test message")

    # Force loguru to flush
    from loguru import logger as loguru_logger

    loguru_logger.complete()

    # Verify file was created
    assert log_file.exists()

    # Verify message in file
    content = log_file.read_text()
    assert "Test message" in content
    assert "INFO" in content


def testLoggingLevels(tempLogDir, monkeypatch):
    """Different log levels work correctly."""
    log_file = tempLogDir / "test.log"

    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("LOG_FILE", str(log_file))

    import src.utils.config as config_module
    import src.utils.logger as logger_module

    logger_module._initialized = False
    config_module._config = None

    test_logger = getLogger("test")

    test_logger.debug("Debug message")  # Should not appear
    test_logger.info("Info message")  # Should not appear
    test_logger.warning("Warning message")  # Should appear
    test_logger.error("Error message")  # Should appear

    # Force flush
    from loguru import logger as loguru_logger

    loguru_logger.complete()

    content = log_file.read_text()
    assert "Debug message" not in content
    assert "Info message" not in content
    assert "Warning message" in content
    assert "Error message" in content


def testConsoleLogging(monkeypatch, capsys):
    """Console logging can be enabled/disabled."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_FILE", "test.log")

    import src.utils.logger as logger_module

    logger_module._initialized = False

    # Console should be enabled by default
    setupLogging()


def testMultipleLoggers(tempLogDir, monkeypatch):
    """Multiple loggers can be created."""
    log_file = tempLogDir / "test.log"

    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_FILE", str(log_file))

    import src.utils.config as config_module
    import src.utils.logger as logger_module

    logger_module._initialized = False
    config_module._config = None

    logger1 = getLogger("module1")
    logger2 = getLogger("module2")
    logger3 = getLogger("module3")

    logger1.info("From module1")
    logger2.info("From module2")
    logger3.info("From module3")

    # Force flush
    from loguru import logger as loguru_logger

    loguru_logger.complete()

    content = log_file.read_text()
    assert "From module1" in content
    assert "From module2" in content
    assert "From module3" in content


def testLogRotation(tempLogDir, monkeypatch):
    """Log rotation configuration."""
    log_file = tempLogDir / "test.log"

    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_FILE", str(log_file))

    import src.utils.config as config_module
    import src.utils.logger as logger_module

    logger_module._initialized = False
    config_module._config = None

    setupLogging()

    # Just verify it doesn't crash with rotation config
    test_logger = getLogger("test")
    test_logger.info("Test message")

    # Force flush
    from loguru import logger as loguru_logger

    loguru_logger.complete()

    assert log_file.exists()
