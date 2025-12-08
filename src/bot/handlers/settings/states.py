from enum import Enum


class SettingsState(str, Enum):
    """States for settings dialog."""

    IDLE = "idle"
    WAITING_BIRTH_DATE = "settings_birth_date"
    WAITING_LIFE_EXPECTANCY = "settings_life_expectancy"
    WAITING_LANGUAGE = "settings_language"
