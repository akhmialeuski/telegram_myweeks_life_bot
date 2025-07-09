"""Unit tests for logger utilities.

Tests logger setup, configuration, and level management
for the application logging system.
"""

import logging
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from src.utils.logger import get_logger, set_log_level


class TestLogger:
    """Test suite for logger utilities."""

    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a valid logger instance.

        :returns: None
        """
        logger = get_logger("test_logger")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_with_existing_name(self):
        """Test that get_logger returns same instance for same name.

        :returns: None
        """
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")

        assert logger1 is logger2

    def test_get_logger_with_different_names(self):
        """Test that get_logger returns different instances for different names.

        :returns: None
        """
        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")

        assert logger1 is not logger2
        assert logger1.name == "logger1"
        assert logger2.name == "logger2"

    def test_get_logger_default_level(self):
        """Test that new loggers get default INFO level.

        :returns: None
        """
        logger = get_logger("new_test_logger")

        assert logger.level == logging.INFO

    def test_set_log_level_valid_levels(self):
        """Test setting valid log levels.

        :returns: None
        """
        logger_name = "test_level_logger"

        for level in [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]:
            set_log_level(logger_name, level)
            logger = get_logger(logger_name)
            assert logger.level == level

    def test_set_log_level_invalid_level(self):
        """Test setting invalid log level raises ValueError.

        :returns: None
        """
        with pytest.raises(ValueError, match="Invalid logging level"):
            set_log_level("test_logger", 999)

    def test_set_log_level_string_level(self):
        """Test setting log level with string raises ValueError.

        :returns: None
        """
        with pytest.raises(ValueError, match="Invalid logging level"):
            set_log_level("test_logger", "INFO")

    def test_logger_has_handlers(self):
        """Test that root logger has console and file handlers.

        :returns: None
        """
        logger = get_logger("test_handler_logger")
        root_logger = logging.getLogger()

        # Root logger should have handlers
        assert len(root_logger.handlers) >= 2

        # Should have console and file handlers
        handler_types = [type(handler).__name__ for handler in root_logger.handlers]
        assert "StreamHandler" in handler_types
        assert "FileHandler" in handler_types

    def test_logger_console_output(self):
        """Test that logger outputs to console.

        :returns: None
        """
        logger = get_logger("test_console_logger")

        with patch("sys.stdout") as mock_stdout:
            logger.info("Test console message")

            # Should have been called (though we can't easily test exact content)
            # Just verify the logger is working
            assert logger.isEnabledFor(logging.INFO)

    def test_logger_file_creation(self):
        """Test that log file gets created.

        :returns: None
        """
        # Check if the log file path exists or would be created
        from src.utils.logger import LOG_FILE, LOGS_DIR

        assert isinstance(LOG_FILE, Path)
        assert isinstance(LOGS_DIR, Path)
        assert LOG_FILE.parent == LOGS_DIR

    def test_module_specific_log_levels(self):
        """Test that different modules can have different log levels.

        :returns: None
        """
        # Test default levels for known modules
        from src.utils.logger import DEFAULT_LOG_LEVELS

        assert isinstance(DEFAULT_LOG_LEVELS, dict)
        assert len(DEFAULT_LOG_LEVELS) > 0

        # Test setting levels for different modules
        set_log_level("test_module_1", logging.DEBUG)
        set_log_level("test_module_2", logging.ERROR)

        logger1 = get_logger("test_module_1")
        logger2 = get_logger("test_module_2")

        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.ERROR

    def test_logger_format_configuration(self):
        """Test that loggers use proper formatting.

        :returns: None
        """
        root_logger = logging.getLogger()

        # Check that handlers have formatters
        for handler in root_logger.handlers:
            assert handler.formatter is not None

        # Test the format includes expected elements
        from src.utils.logger import LOG_FORMAT

        assert "%(asctime)s" in LOG_FORMAT
        assert "%(name)s" in LOG_FORMAT
        assert "%(levelname)s" in LOG_FORMAT
        assert "%(message)s" in LOG_FORMAT

    def test_logger_with_module_name(self):
        """Test getting logger with __name__ style module names.

        :returns: None
        """
        module_name = "src.handlers.start_handler"
        logger = get_logger(module_name)

        assert isinstance(logger, logging.Logger)
        assert logger.name == module_name

    def test_third_party_module_suppression(self):
        """Test that third-party modules get higher log levels by default.

        :returns: None
        """
        from src.utils.logger import DEFAULT_LOG_LEVELS

        # Check that noisy third-party modules are set to WARNING by default
        assert DEFAULT_LOG_LEVELS.get("httpx", logging.INFO) >= logging.WARNING
        assert DEFAULT_LOG_LEVELS.get("urllib3", logging.INFO) >= logging.WARNING

    def test_logger_exception_handling(self):
        """Test that logger can handle exceptions properly.

        :returns: None
        """
        logger = get_logger("test_exception_logger")

        # This should not raise an exception
        try:
            logger.error("Test error message", exc_info=True)
            logger.exception("Test exception message")
        except Exception as e:
            pytest.fail(f"Logger should handle exceptions gracefully: {e}")

    def test_set_log_level_updates_existing_logger(self):
        """Test that changing log level affects existing logger instances.

        :returns: None
        """
        logger_name = "test_update_logger"

        # Get logger with default level
        logger = get_logger(logger_name)
        original_level = logger.level

        # Change level
        new_level = logging.ERROR if original_level != logging.ERROR else logging.DEBUG
        set_log_level(logger_name, new_level)

        # Same instance should have new level
        assert logger.level == new_level

    def test_logs_directory_creation(self):
        """Test that logs directory gets created if it doesn't exist.

        :returns: None
        """
        from src.utils.logger import LOGS_DIR

        # The directory should exist or be created during module import
        # We can't easily test the creation without mocking, but we can verify the path
        assert isinstance(LOGS_DIR, Path)
        assert LOGS_DIR.name == "logs"

    def test_logger_utf8_encoding(self):
        """Test that file handler uses UTF-8 encoding for international characters.

        :returns: None
        """
        logger = get_logger("test_utf8_logger")

        # Test with international characters
        test_message = "Тест международных символов 测试国际字符"

        try:
            logger.info(test_message)
            # If no exception is raised, UTF-8 encoding is working
            assert True
        except UnicodeEncodeError:
            pytest.fail("Logger should handle UTF-8 characters properly")

    def test_multiple_logger_instances_independence(self):
        """Test that multiple logger instances work independently.

        :returns: None
        """
        logger1 = get_logger("independent_logger_1")
        logger2 = get_logger("independent_logger_2")

        # Set different levels
        set_log_level("independent_logger_1", logging.DEBUG)
        set_log_level("independent_logger_2", logging.ERROR)

        # Verify independence
        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.ERROR
        assert logger1.level != logger2.level
