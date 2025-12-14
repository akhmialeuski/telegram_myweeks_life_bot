"""Tests for TelegramNotificationGateway.

This module contains unit tests for the TelegramNotificationGateway
that implements NotificationGatewayProtocol for Telegram delivery.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.error import TelegramError

from src.bot.gateways.telegram_gateway import TelegramNotificationGateway
from src.events.domain_events import NotificationPayload

# Test constants
TEST_USER_ID = 123456789
TEST_MESSAGE = "Test notification message"
TEST_CAPTION = "Test photo caption"


class TestTelegramGatewaySendMessage:
    """Test class for TelegramNotificationGateway.send_message method."""

    @pytest.fixture
    def mock_bot(self) -> MagicMock:
        """Provide mock Telegram Bot."""
        bot = MagicMock()
        bot.send_message = AsyncMock()
        bot.send_photo = AsyncMock()
        return bot

    @pytest.fixture
    def gateway(self, mock_bot: MagicMock) -> TelegramNotificationGateway:
        """Provide gateway instance with mock bot."""
        return TelegramNotificationGateway(bot=mock_bot)

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        gateway: TelegramNotificationGateway,
        mock_bot: MagicMock,
    ) -> None:
        """Test successful message sending."""
        result = await gateway.send_message(
            recipient_id=TEST_USER_ID,
            message=TEST_MESSAGE,
        )

        assert result is True
        mock_bot.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_message_failure(
        self,
        gateway: TelegramNotificationGateway,
        mock_bot: MagicMock,
    ) -> None:
        """Test message sending failure handling."""
        mock_bot.send_message.side_effect = TelegramError("Network error")

        result = await gateway.send_message(
            recipient_id=TEST_USER_ID,
            message=TEST_MESSAGE,
        )

        assert result is False


class TestTelegramGatewaySendPhoto:
    """Test class for TelegramNotificationGateway.send_photo method."""

    @pytest.fixture
    def mock_bot(self) -> MagicMock:
        """Provide mock Telegram Bot."""
        bot = MagicMock()
        bot.send_photo = AsyncMock()
        return bot

    @pytest.fixture
    def gateway(self, mock_bot: MagicMock) -> TelegramNotificationGateway:
        """Provide gateway instance with mock bot."""
        return TelegramNotificationGateway(bot=mock_bot)

    @pytest.mark.asyncio
    async def test_send_photo_success(
        self,
        gateway: TelegramNotificationGateway,
        mock_bot: MagicMock,
    ) -> None:
        """Test successful photo sending."""
        result = await gateway.send_photo(
            recipient_id=TEST_USER_ID,
            photo=b"fake_photo_data",
            caption=TEST_CAPTION,
        )

        assert result is True
        mock_bot.send_photo.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_photo_failure(
        self,
        gateway: TelegramNotificationGateway,
        mock_bot: MagicMock,
    ) -> None:
        """Test photo sending failure handling."""
        mock_bot.send_photo.side_effect = TelegramError("Photo too large")

        result = await gateway.send_photo(
            recipient_id=TEST_USER_ID,
            photo=b"fake_photo_data",
        )

        assert result is False


class TestTelegramGatewaySendNotification:
    """Test class for TelegramNotificationGateway.send_notification method."""

    @pytest.fixture
    def mock_bot(self) -> MagicMock:
        """Provide mock Telegram Bot."""
        bot = MagicMock()
        bot.send_message = AsyncMock()
        return bot

    @pytest.fixture
    def gateway(self, mock_bot: MagicMock) -> TelegramNotificationGateway:
        """Provide gateway instance with mock bot."""
        return TelegramNotificationGateway(bot=mock_bot)

    @pytest.mark.asyncio
    async def test_send_notification_success(
        self,
        gateway: TelegramNotificationGateway,
        mock_bot: MagicMock,
    ) -> None:
        """Test successful notification delivery."""
        payload = NotificationPayload(
            recipient_id=TEST_USER_ID,
            message_type="weekly_summary",
            title="Your Week",
            body="Stats here",
        )

        result = await gateway.send_notification(payload=payload)

        assert result.success is True
        assert result.recipient_id == TEST_USER_ID
        assert result.error is None

    @pytest.mark.asyncio
    async def test_send_notification_failure(
        self,
        gateway: TelegramNotificationGateway,
        mock_bot: MagicMock,
    ) -> None:
        """Test notification delivery failure."""
        mock_bot.send_message.side_effect = TelegramError("User blocked bot")
        payload = NotificationPayload(
            recipient_id=TEST_USER_ID,
            message_type="weekly_summary",
            title="Test",
            body="Body",
        )

        result = await gateway.send_notification(payload=payload)

        assert result.success is False
        assert result.error is not None
        assert "User blocked bot" in result.error

    @pytest.mark.asyncio
    async def test_send_notification_formats_message_with_title(
        self,
        gateway: TelegramNotificationGateway,
        mock_bot: MagicMock,
    ) -> None:
        """Test that notification message includes formatted title."""
        payload = NotificationPayload(
            recipient_id=TEST_USER_ID,
            message_type="weekly_summary",
            title="Weekly Summary",
            body="Your stats",
        )

        await gateway.send_notification(payload=payload)

        call_args = mock_bot.send_message.call_args
        sent_text = call_args.kwargs.get("text")
        assert "<b>Weekly Summary</b>" in sent_text
        assert "Your stats" in sent_text


class TestTelegramGatewaySendBatch:
    """Test class for TelegramNotificationGateway.send_batch method."""

    @pytest.fixture
    def mock_bot(self) -> MagicMock:
        """Provide mock Telegram Bot."""
        bot = MagicMock()
        bot.send_message = AsyncMock()
        return bot

    @pytest.fixture
    def gateway(self, mock_bot: MagicMock) -> TelegramNotificationGateway:
        """Provide gateway instance with mock bot."""
        return TelegramNotificationGateway(bot=mock_bot)

    @pytest.mark.asyncio
    async def test_send_batch_all_success(
        self,
        gateway: TelegramNotificationGateway,
        mock_bot: MagicMock,
    ) -> None:
        """Test batch sending with all successful deliveries."""
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
        assert mock_bot.send_message.await_count == 2

    @pytest.mark.asyncio
    async def test_send_batch_partial_failure(
        self,
        gateway: TelegramNotificationGateway,
        mock_bot: MagicMock,
    ) -> None:
        """Test batch sending with partial failures."""
        mock_bot.send_message.side_effect = [
            None,  # First succeeds
            TelegramError("Failed"),  # Second fails
        ]
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
        assert results[0].success is True
        assert results[1].success is False
