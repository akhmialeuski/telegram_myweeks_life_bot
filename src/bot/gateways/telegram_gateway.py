"""Telegram notification gateway implementation.

This module provides TelegramNotificationGateway that implements
NotificationGatewayProtocol for sending notifications via Telegram.
"""

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from ...events.domain_events import DeliveryResult, NotificationPayload
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.TelegramGateway")


class TelegramNotificationGateway:
    """Telegram implementation of notification delivery.

    This gateway sends notifications via the Telegram Bot API.
    It accepts a telegram.Bot instance and uses it to deliver messages.

    :ivar _bot: Telegram Bot instance for sending messages
    """

    def __init__(self, bot: Bot) -> None:
        """Initialize the Telegram gateway.

        :param bot: Telegram Bot instance for sending messages
        :type bot: Bot
        :returns: None
        """
        self._bot = bot

    async def send_message(self, recipient_id: int, message: str) -> bool:
        """Send text message to recipient.

        :param recipient_id: Telegram chat ID of the recipient
        :type recipient_id: int
        :param message: Message text to send
        :type message: str
        :returns: True if message sent successfully, False otherwise
        :rtype: bool
        """
        try:
            await self._bot.send_message(
                chat_id=recipient_id,
                text=message,
                parse_mode=ParseMode.HTML,
            )
            logger.debug(f"Sent message to user {recipient_id}")
            return True
        except TelegramError as error:
            logger.error(f"Failed to send message to user {recipient_id}: {error}")
            return False

    async def send_photo(
        self,
        recipient_id: int,
        photo: bytes,
        caption: str | None = None,
    ) -> bool:
        """Send photo to recipient.

        :param recipient_id: Telegram chat ID of the recipient
        :type recipient_id: int
        :param photo: Photo data as bytes
        :type photo: bytes
        :param caption: Optional caption for the photo
        :type caption: str | None
        :returns: True if photo sent successfully, False otherwise
        :rtype: bool
        """
        try:
            await self._bot.send_photo(
                chat_id=recipient_id,
                photo=photo,
                caption=caption,
                parse_mode=ParseMode.HTML if caption else None,
            )
            logger.debug(f"Sent photo to user {recipient_id}")
            return True
        except TelegramError as error:
            logger.error(f"Failed to send photo to user {recipient_id}: {error}")
            return False

    async def send_notification(self, payload: NotificationPayload) -> DeliveryResult:
        """Send notification using domain payload.

        Formats the NotificationPayload for Telegram delivery,
        combining title and body into a formatted message.

        :param payload: Notification payload with message content
        :type payload: NotificationPayload
        :returns: Result of the delivery attempt
        :rtype: DeliveryResult
        """
        try:
            # Format message from payload
            formatted_message = self._format_message(payload=payload)

            await self._bot.send_message(
                chat_id=payload.recipient_id,
                text=formatted_message,
                parse_mode=ParseMode.HTML,
            )

            logger.debug(
                f"Sent {payload.message_type} notification to user "
                f"{payload.recipient_id}"
            )
            return DeliveryResult(
                success=True,
                recipient_id=payload.recipient_id,
            )
        except TelegramError as error:
            error_msg = str(error)
            logger.error(
                f"Failed to send {payload.message_type} notification to user "
                f"{payload.recipient_id}: {error_msg}"
            )
            return DeliveryResult(
                success=False,
                recipient_id=payload.recipient_id,
                error=error_msg,
            )

    async def send_batch(
        self,
        payloads: list[NotificationPayload],
    ) -> list[DeliveryResult]:
        """Send multiple notifications.

        Telegram doesn't support true batch sending, so this method
        sends notifications individually but collects results.

        :param payloads: List of notification payloads to send
        :type payloads: list[NotificationPayload]
        :returns: List of delivery results in the same order as payloads
        :rtype: list[DeliveryResult]
        """
        results: list[DeliveryResult] = []

        for payload in payloads:
            result = await self.send_notification(payload=payload)
            results.append(result)

        logger.debug(
            f"Sent batch of {len(payloads)} notifications, "
            f"{sum(1 for r in results if r.success)} successful"
        )
        return results

    def _format_message(self, payload: NotificationPayload) -> str:
        """Format NotificationPayload into Telegram message.

        :param payload: Notification payload to format
        :type payload: NotificationPayload
        :returns: Formatted message text
        :rtype: str
        """
        if payload.title:
            return f"<b>{payload.title}</b>\n\n{payload.body}"
        return payload.body
