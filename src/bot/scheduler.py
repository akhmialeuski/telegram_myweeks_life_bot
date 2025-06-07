"""Scheduler for weekly notifications."""

from telegram.ext import Application
from ..utils.config import CHAT_ID
from ..core.life_tracker import get_weeks_lived

async def send_weekly_message(application: Application) -> None:
    """Send a weekly notification message about the current week of life.

    :param application: The running Application instance.
    :type application: Application
    :returns: None
    :raises telegram.error.TelegramError: If the message cannot be sent.
    """
    weeks_lived = get_weeks_lived()
    await application.bot.send_message(
        chat_id=CHAT_ID,
        text=f"The {weeks_lived}th week of your life has begun."
    )
