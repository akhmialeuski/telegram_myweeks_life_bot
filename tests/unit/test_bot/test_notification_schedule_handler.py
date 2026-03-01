from datetime import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.handlers.settings.notification_schedule_handler import (
    NotificationScheduleHandler,
)
from src.enums import NotificationFrequency, WeekDay
from tests.unit.utils.fake_container import FakeServiceContainer


class TestNotificationScheduleHandler:
    """Unit test suite for schedule parsing logic."""

    @pytest.fixture
    def handler(self) -> NotificationScheduleHandler:
        return NotificationScheduleHandler(services=FakeServiceContainer())

    def test_parse_daily_schedule(self, handler: NotificationScheduleHandler) -> None:
        parsed = handler._parse_schedule_input("daily 09:15")

        assert parsed.frequency == NotificationFrequency.DAILY
        assert parsed.notifications_time == time(9, 15)
        assert parsed.notifications_day is None
        assert parsed.notifications_month_day is None

    def test_parse_weekly_schedule(self, handler: NotificationScheduleHandler) -> None:
        parsed = handler._parse_schedule_input("weekly tuesday 21:45")

        assert parsed.frequency == NotificationFrequency.WEEKLY
        assert parsed.notifications_day == WeekDay.TUESDAY
        assert parsed.notifications_time == time(21, 45)

    def test_parse_monthly_schedule(self, handler: NotificationScheduleHandler) -> None:
        parsed = handler._parse_schedule_input("monthly 15 07:30")

        assert parsed.frequency == NotificationFrequency.MONTHLY
        assert parsed.notifications_month_day == 15
        assert parsed.notifications_time == time(7, 30)

    def test_parse_invalid_weekday_raises_error(
        self, handler: NotificationScheduleHandler
    ) -> None:
        """Test that invalid weekday raises ValueError."""
        with pytest.raises(ValueError, match="Invalid weekday"):
            handler._parse_schedule_input("weekly funday 09:00")

    def test_parse_invalid_format_raises_error(
        self, handler: NotificationScheduleHandler
    ) -> None:
        """Test that invalid schedule format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid schedule format"):
            handler._parse_schedule_input("invalid format")

    def test_parse_invalid_time_raises_error(
        self, handler: NotificationScheduleHandler
    ) -> None:
        """Test that invalid time format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid time format"):
            handler._parse_schedule_input("daily 25:00")

    def test_parse_monthly_invalid_day_raises_error(
        self, handler: NotificationScheduleHandler
    ) -> None:
        """Test that invalid month day raises ValueError."""
        with pytest.raises(ValueError, match="Invalid month day"):
            handler._parse_schedule_input("monthly 31 10:00")

    @pytest.mark.asyncio
    async def test_handle_returns_none(
        self, handler: NotificationScheduleHandler
    ) -> None:
        """Test that handle method returns None as it's not used directly."""
        from unittest.mock import MagicMock

        assert await handler.handle(update=MagicMock(), context=MagicMock()) is None

    @pytest.mark.asyncio
    @patch("src.bot.handlers.settings.notification_schedule_handler.use_locale")
    async def test_handle_input_invalid_state(
        self,
        mock_use_locale: MagicMock,
        handler: NotificationScheduleHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test processing input with invalid waiting state."""
        # Setup mocks
        mock_pgettext = MagicMock(return_value="Translated message")
        mock_use_locale.return_value = (None, None, mock_pgettext)

        handler._extract_command_context = AsyncMock()
        handler._extract_command_context.return_value.user_id = 123
        handler._extract_command_context.return_value.language = "en"

        handler._is_valid_waiting_state = AsyncMock(return_value=False)
        handler._clear_waiting_state = AsyncMock()

        result = await handler.handle_input(
            update=mock_update,
            context=mock_context,
        )

        assert result is None
        handler._clear_waiting_state.assert_called_once_with(
            user_id=123, context=mock_context
        )

    @pytest.mark.asyncio
    @patch("src.bot.handlers.settings.notification_schedule_handler.use_locale")
    async def test_handle_input_update_error(
        self,
        mock_use_locale: MagicMock,
        handler: NotificationScheduleHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test processing input when settings update fails."""
        from src.bot.handlers.base_handler import CommandContext
        from src.database.service import UserNotFoundError

        # Setup mocks
        mock_pgettext = MagicMock(side_effect=lambda c, m: "error_translated")
        mock_use_locale.return_value = (None, None, mock_pgettext)

        mock_cmd_context = MagicMock(spec=CommandContext)
        mock_cmd_context.user_id = 123456
        mock_cmd_context.language = "en"

        # Mock dependencies
        handler._extract_command_context = AsyncMock(return_value=mock_cmd_context)
        handler._is_valid_waiting_state = AsyncMock(return_value=True)
        handler._clear_waiting_state = AsyncMock()
        handler.services.user_service.update_user_settings = AsyncMock(
            side_effect=UserNotFoundError("User not found")
        )

        # Patch send_message on the class directly before use
        with patch.object(
            NotificationScheduleHandler, "send_message", new_callable=AsyncMock
        ) as mock_send_message:
            # Set the text on the update message
            mock_update.message.text = "daily 09:00"

            await handler.handle_input(
                update=mock_update,
                context=mock_context,
            )

            mock_send_message.assert_awaited_once()
            handler._clear_waiting_state.assert_called_once_with(
                user_id=123456, context=mock_context
            )
