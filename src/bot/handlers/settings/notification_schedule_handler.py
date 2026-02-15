"""Handler for notification schedule settings."""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.constants import COMMAND_SETTINGS
from src.bot.conversations.states import ConversationState
from src.database.service import UserNotFoundError, UserSettingsUpdateError
from src.enums import NotificationFrequency, SubscriptionType, WeekDay
from src.events.domain_events import UserSettingsChangedEvent
from src.i18n import use_locale
from src.services.container import ServiceContainer
from src.utils.config import BOT_NAME
from src.utils.logger import get_logger

from .abstract_handler import AbstractSettingsHandler

logger = get_logger(BOT_NAME)

WEEKDAY_BY_NAME: dict[str, WeekDay] = {
    "monday": WeekDay.MONDAY,
    "tuesday": WeekDay.TUESDAY,
    "wednesday": WeekDay.WEDNESDAY,
    "thursday": WeekDay.THURSDAY,
    "friday": WeekDay.FRIDAY,
    "saturday": WeekDay.SATURDAY,
    "sunday": WeekDay.SUNDAY,
}

ALLOWED_PREMIUM_TYPES: tuple[SubscriptionType, ...] = (
    SubscriptionType.PREMIUM,
    SubscriptionType.TRIAL,
)


@dataclass(frozen=True, slots=True)
class ParsedNotificationSchedule:
    """Parsed notification schedule from user input."""

    frequency: NotificationFrequency
    notifications_time: time
    notifications_day: WeekDay | None = None
    notifications_month_day: int | None = None


class NotificationScheduleHandler(AbstractSettingsHandler):
    """Handle notification schedule updates for premium users only."""

    def __init__(self, services: ServiceContainer) -> None:
        super().__init__(services)
        self.command_name = "settings_notification_schedule"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        return None

    async def handle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        cmd_context = await self._extract_command_context(update)
        _, _, pgettext = use_locale(lang=cmd_context.language)

        await query.answer()

        if not self._is_premium(cmd_context.user_profile):
            await self.edit_message(
                query=query,
                message_text=pgettext(
                    "settings.notification_schedule.premium_only",
                    "🔒 This setting is available only for Premium subscription.",
                ),
            )
            return

        await self.edit_message(
            query=query,
            message_text=pgettext(
                "settings.notification_schedule.prompt",
                "🔔 <b>Change reminder schedule</b>\n\n"
                "Send one of the formats:\n"
                "• <code>daily HH:MM</code>\n"
                "• <code>weekly monday HH:MM</code>\n"
                "• <code>monthly 15 HH:MM</code>",
            ),
        )

        await self._set_waiting_state(
            user_id=cmd_context.user_id,
            state=ConversationState.AWAITING_SETTINGS_NOTIFICATION_SCHEDULE,
            context=context,
        )

    async def handle_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        cmd_context = await self._extract_command_context(update)
        user_id = cmd_context.user_id
        _, _, pgettext = use_locale(lang=cmd_context.language)

        if not self._is_premium(cmd_context.user_profile):
            await self.send_message(
                update=update,
                message_text=pgettext(
                    "settings.notification_schedule.premium_only",
                    "🔒 This setting is available only for Premium subscription.",
                ),
            )
            await self._clear_waiting_state(user_id=user_id, context=context)
            return

        if not await self._is_valid_waiting_state(
            user_id=user_id,
            expected_state=ConversationState.AWAITING_SETTINGS_NOTIFICATION_SCHEDULE,
            context=context,
        ):
            await self._clear_waiting_state(user_id=user_id, context=context)
            return

        raw_text = (update.message.text or "").strip()

        try:
            parsed = self._parse_schedule_input(raw_text)
        except ValueError:
            await self.send_message(
                update=update,
                message_text=pgettext(
                    "settings.notification_schedule.invalid",
                    "❌ Invalid format. Use: daily HH:MM, weekly monday HH:MM, monthly 15 HH:MM.",
                ),
            )
            return

        try:
            await self.services.user_service.update_user_settings(
                telegram_id=user_id,
                notification_frequency=parsed.frequency,
                notifications_day=parsed.notifications_day,
                notifications_time=parsed.notifications_time,
                notifications_month_day=parsed.notifications_month_day,
            )

            await self.services.event_bus.publish(
                UserSettingsChangedEvent(
                    user_id=user_id,
                    setting_name="notification_schedule",
                    new_value=raw_text,
                    old_value=None,
                )
            )
        except (UserNotFoundError, UserSettingsUpdateError) as error:
            logger.error("%s: [%s]: failed to update schedule: %s", COMMAND_SETTINGS, user_id, error)
            await self.send_message(
                update=update,
                message_text=pgettext(
                    "settings.error",
                    "❌ An error occurred while updating settings.\nPlease try again later.",
                ),
            )
            return

        await self._clear_waiting_state(user_id=user_id, context=context)
        await self.send_message(
            update=update,
            message_text=pgettext(
                "settings.notification_schedule.updated",
                "✅ Reminder schedule updated successfully.",
            ),
        )

    def _parse_schedule_input(self, text: str) -> ParsedNotificationSchedule:
        parts = text.lower().split()
        if len(parts) == 2 and parts[0] == "daily":
            return ParsedNotificationSchedule(
                frequency=NotificationFrequency.DAILY,
                notifications_time=self._parse_time(parts[1]),
            )

        if len(parts) == 3 and parts[0] == "weekly":
            weekday = WEEKDAY_BY_NAME.get(parts[1])
            if weekday is None:
                raise ValueError("Invalid weekday")
            return ParsedNotificationSchedule(
                frequency=NotificationFrequency.WEEKLY,
                notifications_day=weekday,
                notifications_time=self._parse_time(parts[2]),
            )

        if len(parts) == 3 and parts[0] == "monthly":
            month_day = int(parts[1])
            # Use a conservative 1–28 range so the selected day exists in every month,
            # including February (28 days, 29 in leap years).
            if month_day < 1 or month_day > 28:
                raise ValueError("Invalid month day")
            return ParsedNotificationSchedule(
                frequency=NotificationFrequency.MONTHLY,
                notifications_month_day=month_day,
                notifications_time=self._parse_time(parts[2]),
            )

        raise ValueError("Invalid schedule format")

    @staticmethod
    def _parse_time(value: str) -> time:
        try:
            return datetime.strptime(value, "%H:%M").time()
        except ValueError as error:
            raise ValueError("Invalid time format") from error

    @staticmethod
    def _is_premium(profile) -> bool:
        return bool(
            profile
            and profile.subscription
            and profile.subscription.subscription_type in ALLOWED_PREMIUM_TYPES
            and profile.subscription.is_active
        )
