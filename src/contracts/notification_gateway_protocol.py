"""Notification Gateway Protocol for sending notifications.

This module defines the contract for notification delivery.
Implementations include TelegramNotificationGateway (production)
and LoggingGateway/FakeNotificationGateway (testing).
"""

from typing import Protocol, runtime_checkable

from ..events.domain_events import DeliveryResult, NotificationPayload


@runtime_checkable
class NotificationGatewayProtocol(Protocol):
    """Gateway contract for sending notifications.

    This protocol defines the interface for sending notifications to users.
    Implementations handle the actual delivery mechanism (Telegram, email, etc.).

    Implementations:
        - TelegramNotificationGateway: Production Telegram bot integration
        - LoggingGateway: Logs notifications for testing
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

    async def send_notification(self, payload: NotificationPayload) -> DeliveryResult:
        """Send notification using domain payload.

        This method sends a notification using the transport-agnostic
        NotificationPayload, which can be formatted appropriately for
        the specific delivery channel.

        :param payload: Notification payload with message content and metadata
        :type payload: NotificationPayload
        :returns: Result of the delivery attempt
        :rtype: DeliveryResult
        """
        ...

    async def send_batch(
        self,
        payloads: list[NotificationPayload],
    ) -> list[DeliveryResult]:
        """Send multiple notifications efficiently.

        For channels that support batching, this can be more efficient
        than sending individual notifications.

        :param payloads: List of notification payloads to send
        :type payloads: list[NotificationPayload]
        :returns: List of delivery results in the same order as payloads
        :rtype: list[DeliveryResult]
        """
        ...
