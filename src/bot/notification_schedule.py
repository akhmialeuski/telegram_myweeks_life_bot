"""Utilities for building scheduler triggers from user settings."""

from datetime import datetime, time

from src.constants import (
    DEFAULT_NOTIFICATIONS_DAY,
    DEFAULT_NOTIFICATIONS_MONTH_DAY,
    DEFAULT_NOTIFICATIONS_TIME,
    DEFAULT_TIMEZONE,
)
from src.contracts.scheduler_port_protocol import ScheduleTrigger
from src.core.dtos import UserSettingsDTO
from src.enums import NotificationFrequency, WeekDay

WEEKDAY_MAP: dict[WeekDay, int] = {
    WeekDay.MONDAY: 0,
    WeekDay.TUESDAY: 1,
    WeekDay.WEDNESDAY: 2,
    WeekDay.THURSDAY: 3,
    WeekDay.FRIDAY: 4,
    WeekDay.SATURDAY: 5,
    WeekDay.SUNDAY: 6,
}

DAILY_DAY_OF_WEEK = "*"


def build_notification_trigger(settings: UserSettingsDTO) -> ScheduleTrigger | None:
    """Build schedule trigger from user settings.

    :param settings: User settings DTO
    :type settings: UserSettingsDTO
    :returns: Trigger or None when settings are invalid
    :rtype: ScheduleTrigger | None
    """
    notification_time: time = settings.notifications_time or datetime.strptime(
        DEFAULT_NOTIFICATIONS_TIME,
        "%H:%M:%S",
    ).time()

    frequency = settings.notification_frequency

    if frequency == NotificationFrequency.DAILY:
        return ScheduleTrigger(
            day_of_week=DAILY_DAY_OF_WEEK,
            day_of_month=None,
            hour=notification_time.hour,
            minute=notification_time.minute,
            timezone=settings.timezone or DEFAULT_TIMEZONE,
        )

    if frequency == NotificationFrequency.MONTHLY:
        month_day = settings.notifications_month_day or DEFAULT_NOTIFICATIONS_MONTH_DAY
        return ScheduleTrigger(
            day_of_week=DAILY_DAY_OF_WEEK,
            day_of_month=month_day,
            hour=notification_time.hour,
            minute=notification_time.minute,
            timezone=settings.timezone or DEFAULT_TIMEZONE,
        )

    day = settings.notifications_day or DEFAULT_NOTIFICATIONS_DAY
    day_int = WEEKDAY_MAP.get(day)
    if day_int is None:
        return None

    return ScheduleTrigger(
        day_of_week=day_int,
        day_of_month=None,
        hour=notification_time.hour,
        minute=notification_time.minute,
        timezone=settings.timezone or DEFAULT_TIMEZONE,
    )
