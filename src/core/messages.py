"""Message generation modules.

This module provides classes for generating localized messages for different
domains of the application, isolating string formatting and key management.
"""

from typing import Any, Protocol, runtime_checkable

from . import templates
from .dtos import UserProfileDTO, UserSubscriptionDTO
from .message_context import MessageContext


@runtime_checkable
class I18nServiceProtocol(Protocol):
    """Protocol for internationalization service.

    Defines the interface for translating messages with variable substitution.
    """

    def translate(self, key: str, default: str, **kwargs: Any) -> str:
        """Translate a message key with arguments.

        :param key: Message key (context for pgettext)
        :type key: str
        :param default: Default message text (msgid for pgettext)
        :type default: str
        :param kwargs: Arguments for string formatting
        :type kwargs: Any
        :returns: Localized and formatted string
        :rtype: str
        """
        ...


@runtime_checkable
class MessageBuilder(Protocol):
    """Protocol for message generation."""

    def build(self, context: MessageContext) -> str:
        """Generate localized message from context.

        :param context: Message context containing user info and language
        :type context: MessageContext
        :returns: Generated message string
        :rtype: str
        """
        ...


class StartMessages:
    """Messages for /start command flow."""

    def __init__(self, i18n: I18nServiceProtocol) -> None:
        """Initialize start messages.

        :param i18n: Internationalization service
        :type i18n: I18nServiceProtocol
        """
        self._i18n = i18n

    def welcome_existing(self, user: UserProfileDTO) -> str:
        """Generate welcome message for existing users.

        :param user: User profile DTO
        :type user: UserProfileDTO
        :returns: Localized welcome message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.START_WELCOME_EXISTING_KEY,
            default=templates.START_WELCOME_EXISTING_DEFAULT,
            first_name=user.first_name,
        )

    def welcome_new(self, first_name: str) -> str:
        """Generate welcome message for new users.

        :param first_name: User's first name
        :type first_name: str
        :returns: Localized welcome message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.START_WELCOME_NEW_KEY,
            default=templates.START_WELCOME_NEW_DEFAULT,
            first_name=first_name,
        )


class RegistrationMessages:
    """Messages for registration flow."""

    def __init__(self, i18n: I18nServiceProtocol) -> None:
        """Initialize registration messages.

        :param i18n: Internationalization service
        :type i18n: I18nServiceProtocol
        """
        self._i18n = i18n

    def success(
        self,
        birth_date: str,
        age: str,
        weeks_lived: str,
        remaining_weeks: str,
        life_percentage: str,
    ) -> str:
        """Generate registration success message.

        :param birth_date: Formatted birth date
        :type birth_date: str
        :param age: Formatted age
        :type age: str
        :param weeks_lived: Formatted weeks lived
        :type weeks_lived: str
        :param remaining_weeks: Formatted remaining weeks
        :type remaining_weeks: str
        :param life_percentage: Formatted life percentage
        :type life_percentage: str
        :returns: Localized success message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.REGISTRATION_SUCCESS_KEY,
            default=templates.REGISTRATION_SUCCESS_DEFAULT,
            birth_date=birth_date,
            age=age,
            weeks_lived=weeks_lived,
            remaining_weeks=remaining_weeks,
            life_percentage=life_percentage,
        )

    def error(self) -> str:
        """Generate distinct generic error message.

        :returns: Localized error message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.REGISTRATION_ERROR_KEY,
            default=templates.REGISTRATION_ERROR_DEFAULT,
        )


class ErrorMessages:
    """Common error messages."""

    def __init__(self, i18n: I18nServiceProtocol) -> None:
        """Initialize error messages.

        :param i18n: Internationalization service
        :type i18n: I18nServiceProtocol
        """
        self._i18n = i18n

    def birth_date_future(self) -> str:
        """Generate future birth date error.

        :returns: Localized error message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.BIRTH_DATE_FUTURE_KEY,
            default=templates.BIRTH_DATE_FUTURE_DEFAULT,
        )

    def birth_date_too_old(self) -> str:
        """Generate too old birth date error.

        :returns: Localized error message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.BIRTH_DATE_TOO_OLD_KEY,
            default=templates.BIRTH_DATE_TOO_OLD_DEFAULT,
        )

    def birth_date_format(self) -> str:
        """Generate invalid format error.

        :returns: Localized error message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.BIRTH_DATE_FORMAT_KEY,
            default=templates.BIRTH_DATE_FORMAT_DEFAULT,
        )

    def not_registered(self) -> str:
        """Generate not registered error.

        :returns: Localized error message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.COMMON_NOT_REGISTERED_KEY,
            default=templates.COMMON_NOT_REGISTERED_DEFAULT,
        )


class HelpMessages:
    """Messages for help flow."""

    def __init__(self, i18n: I18nServiceProtocol) -> None:
        """Initialize help messages.

        :param i18n: Internationalization service
        :type i18n: I18nServiceProtocol
        """
        self._i18n = i18n

    def main_help(self) -> str:
        """Generate main help message.

        :returns: Localized help message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.HELP_MAIN_KEY,
            default=templates.HELP_MAIN_DEFAULT,
        )


class SubscriptionMessages:
    """Messages for subscription flow."""

    def __init__(self, i18n: I18nServiceProtocol) -> None:
        """Initialize subscription messages.

        :param i18n: Internationalization service
        :type i18n: I18nServiceProtocol
        """
        self._i18n = i18n

    def status_active(self, subscription: UserSubscriptionDTO) -> str:
        """Generate active subscription status message.

        :param subscription: User subscription DTO containing all subscription info
        :type subscription: UserSubscriptionDTO
        :returns: Localized status message
        :rtype: str
        """
        expiry_date = (
            subscription.expires_at.strftime("%Y-%m-%d")
            if subscription.expires_at
            else "N/A"
        )
        plan_name = subscription.subscription_type.value.title()

        return self._i18n.translate(
            key=templates.SUBSCRIPTION_STATUS_ACTIVE_KEY,
            default=templates.SUBSCRIPTION_STATUS_ACTIVE_DEFAULT,
            expiry_date=expiry_date,
            plan_name=plan_name,
        )

    def status_inactive(self) -> str:
        """Generate inactive subscription status message.

        :returns: Localized status message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.SUBSCRIPTION_STATUS_INACTIVE_KEY,
            default=templates.SUBSCRIPTION_STATUS_INACTIVE_DEFAULT,
        )

    def basic_info(self, buymeacoffee_url: str) -> str:
        """Generate basic subscription info.

        :param buymeacoffee_url: URL for Buy Me a Coffee
        :type buymeacoffee_url: str
        :returns: Localized info message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.SUBSCRIPTION_BASIC_INFO_KEY,
            default=templates.SUBSCRIPTION_BASIC_INFO_DEFAULT,
            buymeacoffee_url=buymeacoffee_url,
        )

    def premium_content(self) -> str:
        """Generate premium content description.

        :returns: Localized description
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.SUBSCRIPTION_PREMIUM_CONTENT_KEY,
            default=templates.SUBSCRIPTION_PREMIUM_CONTENT_DEFAULT,
        )

    def management(self, subscription_type: str, subscription_description: str) -> str:
        """Generate subscription management message.

        :param subscription_type: Current subscription type
        :type subscription_type: str
        :param subscription_description: Description of current subscription
        :type subscription_description: str
        :returns: Localized management message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.SUBSCRIPTION_MANAGEMENT_KEY,
            default=templates.SUBSCRIPTION_MANAGEMENT_DEFAULT,
            subscription_type=subscription_type,
            subscription_description=subscription_description,
        )

    def already_active(self, subscription: UserSubscriptionDTO) -> str:
        """Generate already active subscription message.

        :param subscription: User subscription DTO
        :type subscription: UserSubscriptionDTO
        :returns: Localized message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.SUBSCRIPTION_ALREADY_ACTIVE_KEY,
            default=templates.SUBSCRIPTION_ALREADY_ACTIVE_DEFAULT,
            subscription_type=subscription.subscription_type.value,
        )

    def change_success(
        self, subscription_type: str, subscription_description: str
    ) -> str:
        """Generate subscription change success message.

        :param subscription_type: New subscription type
        :type subscription_type: str
        :param subscription_description: Description of new subscription
        :type subscription_description: str
        :returns: Localized success message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.SUBSCRIPTION_CHANGE_SUCCESS_KEY,
            default=templates.SUBSCRIPTION_CHANGE_SUCCESS_DEFAULT,
            subscription_type=subscription_type,
            subscription_description=subscription_description,
        )

    def change_failed(self) -> str:
        """Generate subscription change failed message.

        :returns: Localized error message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.SUBSCRIPTION_CHANGE_FAILED_KEY,
            default=templates.SUBSCRIPTION_CHANGE_FAILED_DEFAULT,
        )

    def change_error(self) -> str:
        """Generate subscription change error message.

        :returns: Localized error message
        :rtype: str
        """
        return self._i18n.translate(
            key=templates.SUBSCRIPTION_CHANGE_ERROR_KEY,
            default=templates.SUBSCRIPTION_CHANGE_ERROR_DEFAULT,
        )
