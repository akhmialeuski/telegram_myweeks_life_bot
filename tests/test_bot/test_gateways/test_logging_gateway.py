"""Tests for LoggingGateway.

This module contains unit tests for the LoggingGateway
that implements NotificationGatewayProtocol for testing.
"""

import pytest

from src.bot.gateways.logging_gateway import LoggingGateway
from src.events.domain_events import NotificationPayload

# Test constants
TEST_USER_ID = 123456789


class TestLoggingGatewaySendMessage:
    """Test class for LoggingGateway.send_message method."""

    @pytest.fixture
    def gateway(self) -> LoggingGateway:
        """Provide fresh LoggingGateway instance."""
        return LoggingGateway()

    @pytest.mark.asyncio
    async def test_send_message_stores_message(
        self,
        gateway: LoggingGateway,
    ) -> None:
        """Test that send_message stores the message."""
        result = await gateway.send_message(
            recipient_id=TEST_USER_ID,
            message="Test message",
        )

        assert result is True
        assert len(gateway.sent_messages) == 1
        assert gateway.sent_messages[0]["recipient_id"] == TEST_USER_ID
        assert gateway.sent_messages[0]["message"] == "Test message"

    @pytest.mark.asyncio
    async def test_send_message_always_succeeds(
        self,
        gateway: LoggingGateway,
    ) -> None:
        """Test that send_message always returns True."""
        result = await gateway.send_message(
            recipient_id=TEST_USER_ID,
            message="Any message",
        )

        assert result is True


class TestLoggingGatewaySendPhoto:
    """Test class for LoggingGateway.send_photo method."""

    @pytest.fixture
    def gateway(self) -> LoggingGateway:
        """Provide fresh LoggingGateway instance."""
        return LoggingGateway()

    @pytest.mark.asyncio
    async def test_send_photo_stores_photo_info(
        self,
        gateway: LoggingGateway,
    ) -> None:
        """Test that send_photo stores photo information."""
        photo_data = b"fake_photo_data"
        result = await gateway.send_photo(
            recipient_id=TEST_USER_ID,
            photo=photo_data,
            caption="Test caption",
        )

        assert result is True
        assert len(gateway.sent_photos) == 1
        assert gateway.sent_photos[0]["recipient_id"] == TEST_USER_ID
        assert gateway.sent_photos[0]["photo_size"] == len(photo_data)
        assert gateway.sent_photos[0]["caption"] == "Test caption"


class TestLoggingGatewaySendNotification:
    """Test class for LoggingGateway.send_notification method."""

    @pytest.fixture
    def gateway(self) -> LoggingGateway:
        """Provide fresh LoggingGateway instance."""
        return LoggingGateway()

    @pytest.mark.asyncio
    async def test_send_notification_stores_payload(
        self,
        gateway: LoggingGateway,
    ) -> None:
        """Test that send_notification stores the payload."""
        payload = NotificationPayload(
            recipient_id=TEST_USER_ID,
            message_type="weekly_summary",
            title="Test Title",
            body="Test body",
        )

        result = await gateway.send_notification(payload=payload)

        assert result.success is True
        assert result.recipient_id == TEST_USER_ID
        assert len(gateway.sent_notifications) == 1
        assert gateway.sent_notifications[0] == payload


class TestLoggingGatewaySendBatch:
    """Test class for LoggingGateway.send_batch method."""

    @pytest.fixture
    def gateway(self) -> LoggingGateway:
        """Provide fresh LoggingGateway instance."""
        return LoggingGateway()

    @pytest.mark.asyncio
    async def test_send_batch_stores_all_payloads(
        self,
        gateway: LoggingGateway,
    ) -> None:
        """Test that send_batch stores all payloads."""
        payloads = [
            NotificationPayload(
                recipient_id=1,
                message_type="test",
                title="Test 1",
                body="Body 1",
            ),
            NotificationPayload(
                recipient_id=2,
                message_type="test",
                title="Test 2",
                body="Body 2",
            ),
        ]

        results = await gateway.send_batch(payloads=payloads)

        assert len(results) == 2
        assert all(r.success for r in results)
        assert len(gateway.sent_notifications) == 2


class TestLoggingGatewayClear:
    """Test class for LoggingGateway.clear method."""

    @pytest.fixture
    def gateway(self) -> LoggingGateway:
        """Provide fresh LoggingGateway instance."""
        return LoggingGateway()

    @pytest.mark.asyncio
    async def test_clear_removes_all_stored_data(
        self,
        gateway: LoggingGateway,
    ) -> None:
        """Test that clear removes all stored messages and notifications."""
        # Add some data
        await gateway.send_message(recipient_id=TEST_USER_ID, message="Test")
        await gateway.send_photo(
            recipient_id=TEST_USER_ID,
            photo=b"data",
            caption="cap",
        )
        await gateway.send_notification(
            payload=NotificationPayload(
                recipient_id=TEST_USER_ID,
                message_type="test",
                title="Test",
                body="Body",
            )
        )

        # Verify data exists
        assert len(gateway.sent_messages) == 1
        assert len(gateway.sent_photos) == 1
        assert len(gateway.sent_notifications) == 1

        # Clear and verify
        gateway.clear()

        assert len(gateway.sent_messages) == 0
        assert len(gateway.sent_photos) == 0
        assert len(gateway.sent_notifications) == 0
