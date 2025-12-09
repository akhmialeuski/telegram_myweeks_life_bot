"""Notification Gateway Protocol for sending notifications.

This module defines the contract for notification delivery.
Implementations include TelegramNotificationGateway (production)
and FakeNotificationGateway (testing).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class NotificationGatewayProtocol(Protocol):
    """Gateway contract for sending notifications.

    This protocol defines the interface for sending notifications to users.
    Implementations handle the actual delivery mechanism (Telegram, email, etc.).

    Implementations:
        - TelegramNotificationGateway: Production Telegram bot integration
        - FakeNotificationGateway: In-memory implementation for testing
    """

    async def send_message(self, recipient_id: int, message: str) -> bool:
        """Send notification message to recipient.

        :param recipient_id: Unique identifier of the recipient (e.g., Telegram ID)
        :type recipient_id: int
        :param message: Message text to send
        :type message: str
        :returns: True if message sent successfully, False otherwise
        :rtype: bool
        """
        ...

    async def send_photo(
        self,
        recipient_id: int,
        photo: bytes,
        caption: str | None = None,
    ) -> bool:
        """Send photo to recipient.

        :param recipient_id: Unique identifier of the recipient
        :type recipient_id: int
        :param photo: Photo data as bytes
        :type photo: bytes
        :param caption: Optional caption for the photo
        :type caption: str | None
        :returns: True if photo sent successfully, False otherwise
        :rtype: bool
        """
        ...
