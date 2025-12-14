"""Logging gateway for testing notification delivery.

This module provides LoggingGateway that implements NotificationGatewayProtocol
by logging notifications instead of actually sending them. Useful for integration
tests without needing real Telegram API access.
"""

from ...events.domain_events import DeliveryResult, NotificationPayload
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.LoggingGateway")


class LoggingGateway:
    """Logging implementation of notification delivery.

    This gateway logs all notifications instead of sending them.
    Useful for testing and development without Telegram API access.

    :ivar sent_messages: List of sent messages for verification in tests
    :ivar sent_notifications: List of sent notifications for verification
    """

    def __init__(self) -> None:
        """Initialize the logging gateway.

        :returns: None
        """
        self.sent_messages: list[dict[str, str | int]] = []
        self.sent_notifications: list[NotificationPayload] = []
        self.sent_photos: list[dict[str, int | bytes | str | None]] = []

    async def send_message(self, recipient_id: int, message: str) -> bool:
        """Log message instead of sending.

        :param recipient_id: Intended recipient ID
        :type recipient_id: int
        :param message: Message text
        :type message: str
        :returns: Always True
        :rtype: bool
        """
        self.sent_messages.append(
            {
                "recipient_id": recipient_id,
                "message": message,
            }
        )
        logger.info(f"[LOG] Message to {recipient_id}: {message[:50]}...")
        return True

    async def send_photo(
        self,
        recipient_id: int,
        photo: bytes,
        caption: str | None = None,
    ) -> bool:
        """Log photo instead of sending.

        :param recipient_id: Intended recipient ID
        :type recipient_id: int
        :param photo: Photo data
        :type photo: bytes
        :param caption: Optional caption
        :type caption: str | None
        :returns: Always True
        :rtype: bool
        """
        self.sent_photos.append(
            {
                "recipient_id": recipient_id,
                "photo_size": len(photo),
                "caption": caption,
            }
        )
        logger.info(
            f"[LOG] Photo to {recipient_id}: {len(photo)} bytes, "
            f"caption: {caption or 'None'}"
        )
        return True

    async def send_notification(self, payload: NotificationPayload) -> DeliveryResult:
        """Log notification instead of sending.

        :param payload: Notification payload
        :type payload: NotificationPayload
        :returns: Successful delivery result
        :rtype: DeliveryResult
        """
        self.sent_notifications.append(payload)
        logger.info(
            f"[LOG] Notification to {payload.recipient_id}: "
            f"type={payload.message_type}, title={payload.title}"
        )
        return DeliveryResult(
            success=True,
            recipient_id=payload.recipient_id,
        )

    async def send_batch(
        self,
        payloads: list[NotificationPayload],
    ) -> list[DeliveryResult]:
        """Log batch of notifications.

        :param payloads: List of notification payloads
        :type payloads: list[NotificationPayload]
        :returns: List of successful delivery results
        :rtype: list[DeliveryResult]
        """
        results: list[DeliveryResult] = []
        for payload in payloads:
            result = await self.send_notification(payload=payload)
            results.append(result)
        logger.info(f"[LOG] Batch of {len(payloads)} notifications logged")
        return results

    def clear(self) -> None:
        """Clear all stored messages and notifications.

        :returns: None
        """
        self.sent_messages.clear()
        self.sent_notifications.clear()
        self.sent_photos.clear()
