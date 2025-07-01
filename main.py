"""Main entry point for the Telegram bot that tracks and reports life weeks.

This script initializes and runs the Telegram bot that helps users track their life weeks.
The bot provides functionality for:
    - Tracking life weeks
    - Visualizing week progress
    - Weekly notifications

Required environment variables:
    - TELEGRAM_BOT_TOKEN: Your Telegram bot token
    - CHAT_ID: Your Telegram chat ID for notifications

Example:
    >>> python main.py
    Life Weeks Bot is running...
"""

from src.bot.application import LifeWeeksBot


def main() -> None:
    """Initialize and run the Telegram bot.

    This function:
        - Creates a new LifeWeeksBot instance
        - Starts the bot in polling mode
        - Handles the bot's lifecycle

    :returns: None
    :raises RuntimeError: If bot initialization or startup fails
    """
    bot = LifeWeeksBot()
    bot.start()


if __name__ == "__main__":
    main()
