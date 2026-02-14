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

    def test_parse_invalid_schedule_raises_error(
        self, handler: NotificationScheduleHandler
    ) -> None:
        with pytest.raises(ValueError):
            handler._parse_schedule_input("monthly 31 09:00")
