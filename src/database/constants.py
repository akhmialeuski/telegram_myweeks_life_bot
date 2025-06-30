"""Database configuration constants.

Contains all database-related configuration constants
used throughout the database layer.
"""

# Database file paths
DEFAULT_DATABASE_PATH = "lifeweeks.db"  # Default SQLite database filename
DATABASE_DIRECTORY = "data"  # Directory to store database files

# Table names
USERS_TABLE = "users"  # Main users table name
USER_SETTINGS_TABLE = "user_settings"  # User settings table name

# Column constraints
MAX_USERNAME_LENGTH = 255  # Maximum length for Telegram username
MAX_FIRST_NAME_LENGTH = 255  # Maximum length for user's first name
MAX_LAST_NAME_LENGTH = 255  # Maximum length for user's last name
MAX_NOTIFICATIONS_DAY_LENGTH = 20  # Maximum length for day of week string
MAX_TIMEZONE_LENGTH = 100  # Maximum length for timezone identifier

# Default values
DEFAULT_LIFE_EXPECTANCY = 80  # Default life expectancy in years
DEFAULT_NOTIFICATIONS_ENABLED = True  # Default notification setting
DEFAULT_TIMEZONE = "UTC"  # Default timezone for new users
DEFAULT_NOTIFICATIONS_DAY = "Monday"  # Default day for weekly notifications
DEFAULT_NOTIFICATIONS_TIME = "09:00:00"  # Default time for notifications (HH:MM:SS)

# Database connection settings
SQLITE_ECHO = False  # Set to True for SQL query logging
SQLITE_POOL_PRE_PING = True  # Enable connection pool pre-ping for reliability
