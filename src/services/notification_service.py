"""Notification service for generating notification payloads.

This module provides NotificationService that generates transport-agnostic
notification payloads using domain logic. It is decoupled from the delivery
mechanism (Telegram, email, etc.).
"""

from datetime import date

from ..contracts.user_service_protocol import UserServiceProtocol
from ..core.life_calculator import calculate_life_statistics
from ..events.domain_events import NotificationPayload
from ..i18n import use_locale
from ..utils.config import BOT_NAME, DEFAULT_LANGUAGE
from ..utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.NotificationService")

# Message type constants
MESSAGE_TYPE_WEEKLY_SUMMARY = "weekly_summary"
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

    async def generate_weekly_summary(
        self,
        user_id: int,
    ) -> NotificationPayload | None:
        """Generate weekly summary notification payload for a user.

        Retrieves user data, calculates life statistics, and creates
        a localized notification payload.

        :param user_id: Telegram user ID
        :type user_id: int
        :returns: Notification payload or None if user not found
        :rtype: NotificationPayload | None
        """
        try:
            user = await self._user_service.get_user_profile(telegram_id=user_id)

            if not user:
                logger.warning(
                    f"Cannot generate weekly summary: user {user_id} not found"
                )
                return None

            if not user.birth_date:
                logger.warning(
                    f"Cannot generate weekly summary: user {user_id} has no birth date"
                )
                return None

            # Get user language for localization
            user_lang = (
                user.settings.language
                if user.settings and user.settings.language
                else DEFAULT_LANGUAGE
            )

            # Calculate life statistics
            stats = calculate_life_statistics(
                birth_date=user.birth_date,
                life_expectancy=user.settings.life_expectancy or 80,
            )

            # Generate localized message
            _, _, pgettext = use_locale(user_lang)

            title = pgettext("notifications.weekly", "📊 Your weekly life statistics")

            body = pgettext(
                "weeks.statistics",
                "📊 Your Life Statistics:\n\n"
                "🎂 Birth Date: %(birth_date)s\n"
                "📅 Age: %(age)s years\n"
                "📈 Life Expectancy: %(life_expectancy)s years\n"
                "🟩 Lived Weeks: %(lived_weeks)s\n"
                "⬜ Remaining Weeks: %(remaining_weeks)s\n"
                "📊 Total Life Weeks: %(total_weeks)s\n"
                "🎯 Progress: %(progress_percent)s%%",
            ) % {
                "birth_date": self._format_date(
                    birth_date=user.birth_date,
                    language=user_lang,
                ),
                "age": stats.age,
                "life_expectancy": stats.life_expectancy,
                "lived_weeks": stats.total_weeks_lived,
                "remaining_weeks": stats.remaining_weeks,
                "total_weeks": stats.total_weeks_expected,
                "progress_percent": int(stats.percentage_lived * 100),
            }

            return NotificationPayload(
                recipient_id=user_id,
                message_type=MESSAGE_TYPE_WEEKLY_SUMMARY,
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
                f"Failed to generate weekly summary for user {user_id}: {error}"
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
