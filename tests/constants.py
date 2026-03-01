"""Shared test constants for timezone-related tests.

This module provides constants used across unit and integration tests
to avoid magic values and ensure consistency with production code.
"""

# Callback data (must match src.bot.handlers.settings.keyboards)
CALLBACK_TIMEZONE_UTC: str = "timezone_UTC"
CALLBACK_TIMEZONE_MOSCOW: str = "timezone_Europe/Moscow"
CALLBACK_TIMEZONE_WARSAW: str = "timezone_Europe/Warsaw"
CALLBACK_TIMEZONE_MINSK: str = "timezone_Europe/Minsk"
CALLBACK_TIMEZONE_NEW_YORK: str = "timezone_America/New_York"
CALLBACK_TIMEZONE_EUROPE_LONDON: str = "timezone_Europe/London"
CALLBACK_TIMEZONE_OTHER: str = "timezone_other"
CALLBACK_SETTINGS_TIMEZONE: str = "settings_timezone"

# Fixed state values for deterministic tests (avoid time.time()/uuid.uuid4())
TEST_STATE_TIMESTAMP: float = 1700000000.0
TEST_STATE_ID: str = "test-state-id-12345"

# IANA timezone identifiers for tests
TIMEZONE_EUROPE_LONDON: str = "Europe/London"
TIMEZONE_EUROPE_MINSK: str = "Europe/Minsk"
TIMEZONE_EUROPE_MOSCOW: str = "Europe/Moscow"
TIMEZONE_EUROPE_WARSAW: str = "Europe/Warsaw"
TIMEZONE_AMERICA_NEW_YORK: str = "America/New_York"
TIMEZONE_INVALID: str = "Invalid/Timezone"
