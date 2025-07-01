"""Scheduler for weekly notifications."""

from telegram.ext import Application

from ..utils.config import BOT_NAME
from ..utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.Scheduler")


async def send_weekly_message(application: Application) -> None:
    """Send a weekly notification message about the current week of life.

    :param application: The running Application instance.
    :type application: Application
    :returns: None
    :raises telegram.error.TelegramError: If the message cannot be sent.
    """
    pass
