"""Global default configuration constants for the application.

These constants are used across multiple modules (database, bot, core, etc.)
for default user settings and notification scheduling.
"""

DEFAULT_LIFE_EXPECTANCY = 80  # Default life expectancy in years
DEFAULT_NOTIFICATIONS_ENABLED = True  # Default notification setting
DEFAULT_TIMEZONE = "UTC"  # Default timezone for new users
DEFAULT_NOTIFICATIONS_DAY = (
    "monday"  # Default day for weekly notifications (WeekDay enum value)
)
DEFAULT_NOTIFICATIONS_TIME = "09:00:00"  # Default time for notifications (HH:MM:SS)
DEFAULT_USER_FIRST_NAME = "User"  # Default first name for users
