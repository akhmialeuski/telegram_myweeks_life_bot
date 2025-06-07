"""Configuration settings and constants for the application."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
DATE_OF_BIRTH: str = os.getenv("DATE_OF_BIRTH")  # Format: YYYY-MM-DD
CHAT_ID: str = os.getenv("CHAT_ID")  # User's Telegram ID

# Visualization Constants
CELL_SIZE = 10
PADDING = 40
FONT_SIZE = 12
MAX_YEARS = 90
WEEKS_PER_YEAR = 52

# Colors
COLORS = {
    'background': (255, 255, 255),  # White
    'grid': (200, 200, 200),        # Light gray
    'lived': (76, 175, 80),         # Green
    'text': (0, 0, 0),              # Black
    'axis': (100, 100, 100),        # Dark gray
}

# Scheduler Configuration
WEEKLY_NOTIFICATION_DAY = "mon"
WEEKLY_NOTIFICATION_HOUR = 9
WEEKLY_NOTIFICATION_MINUTE = 0
