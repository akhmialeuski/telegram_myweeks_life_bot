"""Common logger configuration for the project.

This module provides a centralized logging configuration that can be used across all modules.
Each module should get its own logger instance using get_logger(module_name).

The module configures:
    - File logging to logs/life_weeks_bot.log
    - Console logging with module-specific levels
    - Default log levels for different modules
    - Ability to dynamically change log levels

Example:
    >>> from src.utils.logger import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Module started")
"""

import logging
import sys
from pathlib import Path
from typing import Dict

from .config import BOT_NAME

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file path
LOG_FILE = LOGS_DIR / "life_weeks_bot.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log levels for different modules
DEFAULT_LOG_LEVELS: Dict[str, int] = {
    # Our application modules
    BOT_NAME: logging.INFO,
    "handlers": logging.INFO,
    "utils": logging.INFO,
    # Third-party modules to suppress
    "httpx": logging.WARNING,
    "apscheduler": logging.WARNING,
    "telegram": logging.WARNING,
    "urllib3": logging.WARNING,
}


def _setup_root_logger() -> None:
    """Set up the root logger with file and console handlers.

    This function configures:
        - Root logger with INFO level
        - File handler logging everything (DEBUG+) to life_weeks_bot.log
        - Console handler with module-specific levels
        - Default log levels for all known modules

    :returns: None
    :raises IOError: If log file cannot be created or accessed
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # File handler - log everything to file
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Log all levels to file
    file_handler.setFormatter(formatter)

    # Console handler - use module-specific levels
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Set default levels for all modules
    for module_name, level in DEFAULT_LOG_LEVELS.items():
        logging.getLogger(module_name).setLevel(level)


# Initialize root logger
_setup_root_logger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.

    This function returns a configured logger instance for the specified module.
    If the module doesn't have a default log level set, it will be set to INFO.

    :param name: The name of the module requesting the logger
    :type name: str
    :returns: A configured logger instance for the specified module
    :rtype: logging.Logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module started")
        >>> logger.error("Error occurred", exc_info=True)
    """
    logger = logging.getLogger(name)
    # Set default level if not already set
    if name not in DEFAULT_LOG_LEVELS:
        DEFAULT_LOG_LEVELS[name] = logging.INFO
        logger.setLevel(logging.INFO)
    return logger
