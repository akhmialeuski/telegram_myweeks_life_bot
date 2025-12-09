"""Fake Notification Gateway implementation for testing.

This module provides a fake implementation of NotificationGatewayProtocol
that records all sent messages for later verification in tests.
"""


class FakeNotificationGateway:
    """Fake notification gateway for testing.

    This implementation records all sent messages in memory instead of
    actually sending them. Test code can then verify that the expected
    messages were sent.

    Attributes:
        sent_messages: List of (recipient_id, message) tuples for text messages
        sent_photos: List of (recipient_id, photo, caption) tuples for photos

    Example:
        >>> gateway = FakeNotificationGateway()
        >>> await gateway.send_message(recipient_id=123, message="Hello")
        True
        >>> gateway.sent_messages
        [(123, "Hello")]
    """

    def __init__(self) -> None:
        """Initialize the gateway with empty message logs.

        :returns: None
        """
        self.sent_messages: list[tuple[int, str]] = []
        self.sent_photos: list[tuple[int, bytes, str | None]] = []
        self._should_fail: bool = False

    async def send_message(self, recipient_id: int, message: str) -> bool:
        """Record a message as sent.

        :param recipient_id: Unique identifier of the recipient
        :type recipient_id: int
        :param message: Message text to send
        :type message: str
        :returns: True if message recorded, False if configured to fail
        :rtype: bool
        """
        if self._should_fail:
            return False
        self.sent_messages.append((recipient_id, message))
        return True

    async def send_photo(
        self,
        recipient_id: int,
        photo: bytes,
        caption: str | None = None,
    ) -> bool:
        """Record a photo as sent.

        :param recipient_id: Unique identifier of the recipient
        :type recipient_id: int
        :param photo: Photo data as bytes
        :type photo: bytes
        :param caption: Optional caption for the photo
        :type caption: str | None
        :returns: True if photo recorded, False if configured to fail
        :rtype: bool
        """
        if self._should_fail:
            return False
        self.sent_photos.append((recipient_id, photo, caption))
        return True

    def set_should_fail(self, should_fail: bool) -> None:
        """Configure the gateway to simulate failures.

        :param should_fail: If True, all send operations will return False
        :type should_fail: bool
        :returns: None
        """
        self._should_fail = should_fail

    def clear(self) -> None:
        """Clear all recorded messages and photos.

        :returns: None
        """
        self.sent_messages.clear()
        self.sent_photos.clear()

    def get_message_count(self) -> int:
        """Get the total number of messages sent.

        :returns: Number of messages sent
        :rtype: int
        """
        return len(self.sent_messages)

    def get_messages_for_recipient(self, recipient_id: int) -> list[str]:
        """Get all messages sent to a specific recipient.

        :param recipient_id: Recipient ID to filter by
        :type recipient_id: int
        :returns: List of message texts sent to the recipient
        :rtype: list[str]
        """
        return [msg for rid, msg in self.sent_messages if rid == recipient_id]
