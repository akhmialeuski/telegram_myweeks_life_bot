"""Notification service for generating notification payloads.

This module provides NotificationService that generates transport-agnostic
notification payloads using domain logic. It is decoupled from the delivery
mechanism (Telegram, email, etc.).
"""

from datetime import date

from babel.numbers import format_decimal, format_percent

from ..constants import DEFAULT_LIFE_EXPECTANCY
from ..contracts.user_service_protocol import UserServiceProtocol
from ..core.life_calculator import calculate_life_statistics
from ..events.domain_events import NotificationPayload
from ..i18n import normalize_babel_locale, use_locale
from ..utils.config import BOT_NAME, DEFAULT_LANGUAGE
from ..utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.NotificationService")

# Message type constants
MESSAGE_TYPE_DAILY_SUMMARY = "daily_summary"
MESSAGE_TYPE_WEEKLY_SUMMARY = "weekly_summary"
MESSAGE_TYPE_MONTHLY_SUMMARY = "monthly_summary"
MESSAGE_TYPE_MILESTONE = "milestone"


class NotificationService:
    """Service for generating notification payloads.

    This service generates transport-agnostic NotificationPayload objects
    that can be delivered via any notification gateway (Telegram, email, etc.).

    :ivar _user_service: User service for retrieving user data
    """

    def __init__(
        self,
        user_service: UserServiceProtocol,
    ) -> None:
        """Initialize the notification service.

        :param user_service: Service for user data access
        :type user_service: UserServiceProtocol
        :returns: None
        """
        self._user_service = user_service

    async def generate_summary(
        self,
        user_id: int,
        message_type: str = MESSAGE_TYPE_WEEKLY_SUMMARY,
    ) -> NotificationPayload | None:
        """Generate life statistics summary notification payload for a user.

        Retrieves user data, calculates life statistics, and creates
        a localized notification payload based on the frequency.

        :param user_id: Telegram user ID
        :type user_id: int
        :param message_type: Type of summary (daily, weekly, monthly)
        :type message_type: str
        :returns: Notification payload or None if user not found
        :rtype: NotificationPayload | None
        """
        try:
            user = await self._user_service.get_user_profile(telegram_id=user_id)

            if not user:
                logger.warning(
                    f"Cannot generate {message_type}: user {user_id} not found"
                )
                return None

            if not user.settings.birth_date:
                logger.warning(
                    f"Cannot generate {message_type}: user {user_id} has no birth date"
                )
                return None

            # Get user language for localization
            user_lang = (
                user.settings.language
                if user.settings and user.settings.language
                else DEFAULT_LANGUAGE
            )

            # Calculate life statistics
            life_expectancy = user.settings.life_expectancy or DEFAULT_LIFE_EXPECTANCY
            stats = calculate_life_statistics(
                birth_date=user.settings.birth_date,
                life_expectancy=life_expectancy,
            )

            # Generate localized message
            _, _, pgettext = use_locale(user_lang)
            babel_locale = normalize_babel_locale(user_lang)

            # Determine title based on message type
            if message_type == MESSAGE_TYPE_DAILY_SUMMARY:
                title = pgettext("notifications.daily", "📉 Your daily life statistics")
            elif message_type == MESSAGE_TYPE_MONTHLY_SUMMARY:
                title = pgettext(
                    "notifications.monthly", "📊 Your monthly life statistics"
                )
            else:
                title = pgettext(
                    "notifications.weekly", "📊 Your weekly life statistics"
                )

            # Use the same pgettext context + msgid as /weeks handler
            # so .po translations are resolved correctly
            body = pgettext(
                "weeks.statistics",
                "📊 <b>Your life statistics:</b>\n\n"
                "🎂 <b>Age:</b> %(age)s years\n"
                "📅 <b>Weeks lived:</b> %(weeks_lived)s\n"
                "⏳ <b>Remaining weeks (until %(life_expectancy)s years):"
                "</b> %(remaining_weeks)s\n"
                "📈 <b>Life progress:</b> %(life_percentage)s\n"
                "🎉 <b>Days until birthday:</b> %(days_until_birthday)s\n\n"
                "💡 Use /visualize to visualize your life weeks",
            ) % {
                "age": format_decimal(stats.age, locale=babel_locale),
                "weeks_lived": format_decimal(
                    stats.total_weeks_lived,
                    locale=babel_locale,
                    format="#,##0",
                ),
                "life_expectancy": format_decimal(life_expectancy, locale=babel_locale),
                "remaining_weeks": format_decimal(
                    stats.remaining_weeks,
                    locale=babel_locale,
                    format="#,##0",
                ),
                "life_percentage": format_percent(
                    stats.percentage_lived,
                    locale=babel_locale,
                    format="#0.1%",
                ),
                "days_until_birthday": format_decimal(
                    stats.days_until_birthday, locale=babel_locale
                ),
            }

            return NotificationPayload(
                recipient_id=user_id,
                message_type=message_type,
                title=title,
                body=body,
                metadata={
                    "language": user_lang,
                    "stats": {
                        "age": stats.age,
                        "life_expectancy": stats.life_expectancy,
                        "lived_weeks": stats.total_weeks_lived,
                        "remaining_weeks": stats.remaining_weeks,
                        "total_weeks": stats.total_weeks_expected,
                        "progress_percent": stats.percentage_lived,
                    },
                },
            )

        except Exception as error:
            logger.error(
                f"Failed to generate {message_type} for user {user_id}: {error}"
            )
            return None

    async def generate_milestone_notification(
        self,
        user_id: int,
        milestone_type: str,
        milestone_value: int,
    ) -> NotificationPayload | None:
        """Generate milestone notification payload.

        :param user_id: Telegram user ID
        :type user_id: int
        :param milestone_type: Type of milestone (e.g., "week", "year", "percentage")
        :type milestone_type: str
        :param milestone_value: Milestone value
        :type milestone_value: int
        :returns: Notification payload or None if user not found
        :rtype: NotificationPayload | None
        """
        try:
            user = await self._user_service.get_user_profile(telegram_id=user_id)

            if not user:
                logger.warning(f"Cannot generate milestone: user {user_id} not found")
                return None

            user_lang = (
                user.settings.language
                if user.settings and user.settings.language
                else DEFAULT_LANGUAGE
            )

            _, _, pgettext = use_locale(user_lang)

            title = pgettext("notifications.milestone", "🎉 Milestone reached!")
            body = pgettext(
                "notifications.milestone_body",
                "Congratulations! You've reached a milestone: "
                "%(milestone_type)s = %(milestone_value)s",
            ) % {
                "milestone_type": milestone_type,
                "milestone_value": milestone_value,
            }

            return NotificationPayload(
                recipient_id=user_id,
                message_type=MESSAGE_TYPE_MILESTONE,
                title=title,
                body=body,
                metadata={
                    "milestone_type": milestone_type,
                    "milestone_value": milestone_value,
                    "language": user_lang,
                },
            )

        except Exception as error:
            logger.error(f"Failed to generate milestone for user {user_id}: {error}")
            return None

    def _format_date(self, birth_date: date, language: str) -> str:
        """Format date according to user's locale.

        :param birth_date: Date to format
        :type birth_date: date
        :param language: Language code
        :type language: str
        :returns: Formatted date string
        :rtype: str
        """
        # Use DD.MM.YYYY format as default
        return birth_date.strftime("%d.%m.%Y")
