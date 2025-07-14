"""Configuration settings and constants for the application."""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID: str = os.getenv("CHAT_ID")  # User's Telegram ID

# Bot name for logging
BOT_NAME: str = "LifeWeeksBot"

# Localization
DEFAULT_LANGUAGE: str = "ru"

# Visualization Constants
CELL_SIZE = 10
PADDING = 40
FONT_SIZE = 12
MAX_YEARS = 90
WEEKS_PER_YEAR = 52

# Colors
COLORS = {
    "background": (255, 255, 255),  # White
    "grid": (200, 200, 200),  # Light gray
    "lived": (76, 175, 80),  # Green
    "text": (0, 0, 0),  # Black
    "axis": (100, 100, 100),  # Dark gray
}

# Scheduler Configuration
WEEKLY_NOTIFICATION_DAY = "mon"
WEEKLY_NOTIFICATION_HOUR = 9
WEEKLY_NOTIFICATION_MINUTE = 0


# Donation URL (BuyMeACoffee)
def _get_buymeacoffee_url() -> str:
    """
    Get BuyMeACoffee URL from environment or use default if not set or empty.

    :returns: BuyMeACoffee URL string
    """
    url = os.getenv("BUYMEACOFFEE_URL", "https://www.buymeacoffee.com/yourname")
    if not url or not url.strip():
        return "https://www.buymeacoffee.com/yourname"
    return url


BUYMEACOFFEE_URL: str = _get_buymeacoffee_url()
