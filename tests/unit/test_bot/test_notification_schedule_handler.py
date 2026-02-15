"""Unit tests for notification schedule settings handler."""

from datetime import time

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
