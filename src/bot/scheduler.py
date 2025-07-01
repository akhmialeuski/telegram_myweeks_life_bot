"""Scheduler for weekly notifications."""

from telegram.ext import Application

from ..core.life_tracker import get_weeks_lived
from ..database.sqlite_repository import SQLiteRepository
from ..utils.config import CHAT_ID


async def send_weekly_message(application: Application) -> None:
    """Send a weekly notification message about the current week of life.

    :param application: The running Application instance.
    :type application: Application
    :returns: None
    :raises telegram.error.TelegramError: If the message cannot be sent.
    """
    # Get user's birth date from database
    db = SQLiteRepository()
    user = db.get_user_by_chat_id(CHAT_ID)

    if user and user.birth_date:
        weeks_lived = get_weeks_lived(user.birth_date)
        await application.bot.send_message(
            chat_id=CHAT_ID, text=f"The {weeks_lived}th week of your life has begun."
        )
