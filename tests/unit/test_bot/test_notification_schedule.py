"""Tests for notification_schedule.py."""

from datetime import time

from src.bot.notification_schedule import build_notification_trigger
from src.constants import DEFAULT_TIMEZONE
from src.core.dtos import UserSettingsDTO
from src.enums import NotificationFrequency, WeekDay


class TestBuildNotificationTrigger:
    """Test class for build_notification_trigger function."""

    def test_daily_notification(self):
        """Test building daily notification trigger."""
        settings = UserSettingsDTO(
            notifications=True,
            notification_frequency=NotificationFrequency.DAILY,
            notifications_time=time(10, 30),
            timezone="UTC",
            birth_date=None,
            notifications_day=None,
            notifications_month_day=None,
            life_expectancy=None,
            language=None,
        )
        trigger = build_notification_trigger(settings)
        assert trigger is not None
        assert trigger.day_of_week == "*"
        assert trigger.hour == 10
        assert trigger.minute == 30
        assert trigger.timezone == "UTC"

    def test_monthly_notification(self):
        """Test building monthly notification trigger."""
        settings = UserSettingsDTO(
            notifications=True,
            notification_frequency=NotificationFrequency.MONTHLY,
            notifications_time=time(12, 0),
            notifications_month_day=15,
            timezone="Europe/Moscow",
            birth_date=None,
            notifications_day=None,
            life_expectancy=None,
            language=None,
        )
        trigger = build_notification_trigger(settings)
        assert trigger is not None
        assert trigger.day_of_month == 15
        assert trigger.hour == 12
        assert trigger.minute == 0
        assert trigger.timezone == "Europe/Moscow"

    def test_weekly_notification(self):
        """Test building weekly notification trigger."""
        settings = UserSettingsDTO(
            notifications=True,
            notification_frequency=NotificationFrequency.WEEKLY,
            notifications_time=time(18, 45),
            notifications_day=WeekDay.WEDNESDAY,
            timezone="UTC",
            birth_date=None,
            notifications_month_day=None,
            life_expectancy=None,
            language=None,
        )
        trigger = build_notification_trigger(settings)
        assert trigger is not None
        assert trigger.day_of_week == 2  # Wednesday is 2
        assert trigger.hour == 18
        assert trigger.minute == 45

    def test_invalid_frequency(self):
        """Test building trigger with invalid frequency."""
        settings = UserSettingsDTO(
            notifications=True,
            notification_frequency=None,  # type: ignore
            notifications_time=time(10, 0),
            birth_date=None,
            notifications_day=None,
            notifications_month_day=None,
            life_expectancy=None,
            timezone=None,
            language=None,
        )
        trigger = build_notification_trigger(settings)
        assert trigger is None

    def test_default_values(self):
        """Test building trigger with default values."""
        settings = UserSettingsDTO(
            notifications=True,
            notification_frequency=NotificationFrequency.DAILY,
            notifications_time=None,  # Should use default
            timezone=None,  # Should use default
            birth_date=None,
            notifications_day=None,
            notifications_month_day=None,
            life_expectancy=None,
            language=None,
        )
        trigger = build_notification_trigger(settings)
        assert trigger is not None
        assert trigger.timezone == DEFAULT_TIMEZONE

    def test_weekly_invalid_day(self):
        """Test building weekly trigger with invalid day."""
        settings = UserSettingsDTO(
            notifications=True,
            notification_frequency=NotificationFrequency.WEEKLY,
            notifications_day="INVALID",  # type: ignore
            birth_date=None,
            notifications_time=None,
            notifications_month_day=None,
            life_expectancy=None,
            timezone=None,
            language=None,
        )
        trigger = build_notification_trigger(settings)
        assert trigger is None
