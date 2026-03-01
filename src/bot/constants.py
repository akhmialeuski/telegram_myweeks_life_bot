"""Bot constants module.

This module contains all constants used throughout the bot application,
including command names, configuration values, and other constants.
"""

# Command constants
from src.enums import SupportedLanguage

COMMAND_START = "start"
COMMAND_WEEKS = "weeks"
COMMAND_SETTINGS = "settings"
COMMAND_VISUALIZE = "visualize"
COMMAND_HELP = "help"
COMMAND_SUBSCRIPTION = "subscription"
COMMAND_CANCEL = "cancel"
COMMAND_UNKNOWN = "unknown"

# Timezone constants
DEFAULT_TIMEZONE_MAPPING = {
    SupportedLanguage.RU: "Europe/Moscow",
    SupportedLanguage.BY: "Europe/Minsk",
    SupportedLanguage.BE: "Europe/Minsk",
    SupportedLanguage.UA: "Europe/Kyiv",
    SupportedLanguage.UK: "Europe/Kyiv",
    SupportedLanguage.EN: "UTC",
}
FALLBACK_TIMEZONE = "UTC"
