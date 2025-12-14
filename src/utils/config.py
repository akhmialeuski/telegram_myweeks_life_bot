"""Configuration settings and constants for the application."""

import os

from dotenv import load_dotenv

from src.enums import SupportedLanguage

# Bot name for logging
BOT_NAME: str = "LifeWeeksBot"

# Load environment variables
load_dotenv()

# Bot Configuration
TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID: str = os.getenv("CHAT_ID")  # User's Telegram ID

# Localization
DEFAULT_LANGUAGE: str = SupportedLanguage.RU.value

# Visualization Constants
CELL_SIZE = 10
PADDING = 40
FONT_SIZE = 12
MAX_YEARS = 90
WEEKS_PER_YEAR = 52

# Validation Constants
MIN_BIRTH_YEAR = 1900
MIN_LIFE_EXPECTANCY = 50
MAX_LIFE_EXPECTANCY = 120

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

# Subscription message probability (percentage)
DEFAULT_SUBSCRIPTION_MESSAGE_PROBABILITY = 20  # 20% default probability


def _get_subscription_message_probability() -> int:
    """
    Get subscription message probability from environment or use default.

    :returns: Probability percentage as integer (0-100)
    """
    try:
        probability = os.getenv("SUBSCRIPTION_MESSAGE_PROBABILITY")
        if probability is not None:
            return int(probability)
    except (ValueError, TypeError):
        pass
    return DEFAULT_SUBSCRIPTION_MESSAGE_PROBABILITY


SUBSCRIPTION_MESSAGE_PROBABILITY: int = _get_subscription_message_probability()


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
