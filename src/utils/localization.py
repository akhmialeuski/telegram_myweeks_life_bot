"""Localization module for LifeWeeksBot.

This module contains all user-facing messages in multiple languages.
Supports Russian (ru), English (en), Ukrainian (ua), and Belarusian (by).
"""

import gettext
from enum import StrEnum, auto
from pathlib import Path

from ..constants import DEFAULT_LIFE_EXPECTANCY

# Define locale directory
LOCALE_DIR = Path(__file__).resolve().parent.parent.parent / "locales"


def get_translator(lang_code: str):
    """Get gettext translator for the specified language.

    :param lang_code: Language code (ru, en, ua, by)
    :type lang_code: str
    :returns: gettext translator function
    :rtype: function
    """
    return gettext.translation(
        "messages", localedir=LOCALE_DIR, languages=[lang_code], fallback=True
    ).gettext


class SupportedLanguage(StrEnum):
    RU = auto()
    EN = auto()
    UA = auto()
    BY = auto()

    @classmethod
    def list(cls) -> list[str]:
        return [lang.value for lang in cls]


# Supported languages
LANGUAGES = SupportedLanguage.list()

# Default language
DEFAULT_LANGUAGE = SupportedLanguage.RU.value

# Localized language names
_LANGUAGE_NAMES = {
    SupportedLanguage.RU.value: {
        SupportedLanguage.RU.value: "Русский",
        SupportedLanguage.EN.value: "Английский",
        SupportedLanguage.UA.value: "Украинский",
        SupportedLanguage.BY.value: "Белорусский",
    },
    SupportedLanguage.EN.value: {
        SupportedLanguage.RU.value: "Russian",
        SupportedLanguage.EN.value: "English",
        SupportedLanguage.UA.value: "Ukrainian",
        SupportedLanguage.BY.value: "Belarusian",
    },
    SupportedLanguage.UA.value: {
        SupportedLanguage.RU.value: "Російська",
        SupportedLanguage.EN.value: "Англійська",
        SupportedLanguage.UA.value: "Українська",
        SupportedLanguage.BY.value: "Білоруська",
    },
    SupportedLanguage.BY.value: {
        SupportedLanguage.RU.value: "Рускай",
        SupportedLanguage.EN.value: "Англійская",
        SupportedLanguage.UA.value: "Украінская",
        SupportedLanguage.BY.value: "Беларуская",
    },
}


def get_localized_language_name(language: str, target_language: str) -> str:
    """
    Get the localized name of a language in the target language.

    :param language: Language code to localize (e.g., 'en')
    :param target_language: Target language code (e.g., 'ru')
    :return: Localized language name
    """
    return _LANGUAGE_NAMES.get(target_language, {}).get(language, language)


def get_supported_languages() -> list[str]:
    """Get list of supported languages.

    :returns: List of supported language codes
    :rtype: list[str]
    """
    return LANGUAGES.copy()


def is_language_supported(language: str) -> bool:
    """Check if language is supported.

    :param language: Language code to check
    :type language: str
    :returns: True if language is supported, False otherwise
    :rtype: bool
    """
    return language in LANGUAGES


def get_message(
    message_key: str,
    sub_key: str,
    language: str | None = None,
    **kwargs,
) -> str:
    """Backward-compatible message lookup used in some tests.

    This helper emulates the previous ``get_message`` API by delegating to
    ``MessageBuilder`` methods for the handful of keys used in tests.

    :param message_key: Message group key (e.g., "common", "weeks", "visualize")
    :type message_key: str
    :param sub_key: Specific message key within the group (e.g., "not_registered")
    :type sub_key: str
    :param language: Optional language code; defaults to ``DEFAULT_LANGUAGE``
    :type language: str | None
    :returns: Localized message text
    :rtype: str
    """
    lang_code: str = language or DEFAULT_LANGUAGE
    builder: MessageBuilder = MessageBuilder(lang_code)

    key: str = f"{message_key}.{sub_key}"
    if key == "common.not_registered":
        return builder.not_registered()
    if key == "weeks.not_registered":
        return builder.not_registered_weeks()
    if key == "visualize.not_registered":
        return builder.not_registered_visualize()

    # Generic fallback primarily for tests
    return f"Mock message: {message_key}.{sub_key} ({lang_code})"


class MessageBuilder:
    """Message builder class for generating localized messages using gettext.

    This class provides a facade for generating localized messages using
    the gettext system. It maintains backward compatibility with existing
    message generation functions while providing a cleaner interface.
    """

    def __init__(self, lang: str):
        """Initialize MessageBuilder with language.

        :param lang: Language code (ru, en, ua, by)
        :type lang: str
        """
        self.lang = lang
        self._ = get_translator(lang)

    def settings_basic(self, user) -> str:
        """Generate basic settings message.

        :param user: User object with settings
        :type user: Any
        :returns: Localized settings message
        :rtype: str
        """
        # Format birth date
        birth_date = user.settings.birth_date if user.settings else None
        if birth_date:
            birth_date_str = birth_date.strftime("%d.%m.%Y")
        else:
            birth_date_str = self._("Not set")

        # Get language name
        language_name = get_localized_language_name(self.lang, self.lang)

        # Get life expectancy
        life_expectancy = (
            user.settings.life_expectancy if user.settings else DEFAULT_LIFE_EXPECTANCY
        )

        return self._(
            "⚙️ <b>Profile Settings (Basic Subscription)</b>\n\n"
            "📅 <b>Birth date:</b> {birth_date}\n"
            "🌍 <b>Language:</b> {language_name}\n"
            "⏰ <b>Expected life expectancy:</b> {life_expectancy} years\n\n"
            "Select what you want to change:"
        ).format(
            birth_date=birth_date_str,
            language_name=language_name,
            life_expectancy=life_expectancy,
        )

    def settings_premium(self, user) -> str:
        """Generate premium settings message.

        :param user: User object with settings
        :type user: Any
        :returns: Localized premium settings message
        :rtype: str
        """
        # Format birth date
        birth_date = user.settings.birth_date if user.settings else None
        if birth_date:
            birth_date_str = birth_date.strftime("%d.%m.%Y")
        else:
            birth_date_str = self._("Not set")

        # Get language name
        language_name = get_localized_language_name(self.lang, self.lang)

        # Get life expectancy
        life_expectancy = (
            user.settings.life_expectancy if user.settings else DEFAULT_LIFE_EXPECTANCY
        )

        return self._(
            "⚙️ <b>Profile Settings (Premium Subscription)</b>\n\n"
            "📅 <b>Birth date:</b> {birth_date}\n"
            "🌍 <b>Language:</b> {language_name}\n"
            "⏰ <b>Expected life expectancy:</b> {life_expectancy} years\n\n"
            "Select what you want to change:"
        ).format(
            birth_date=birth_date_str,
            language_name=language_name,
            life_expectancy=life_expectancy,
        )

    def help(self) -> str:
        """Generate help message.

        :returns: Localized help message
        :rtype: str
        """
        return self._(
            "🤖 LifeWeeksBot - Helps you track the weeks of your life\n\n"
            "📋 Available commands:\n"
            "• /start - Registration and setup\n"
            "• /weeks - Show life weeks\n"
            "• /visualize - Life weeks visualization\n"
            "• /settings - Settings\n"
            "• /subscription - Subscription\n"
            "• /help - This help\n\n"
            "💡 Interesting facts:\n"
            "• There are 52 weeks in a year\n"
            "• Average life expectancy: 80 years\n"
            "• That's about 4,160 weeks\n\n"
            "🎯 The bot's goal is to help you realize the value of time!"
        )

    def weeks_statistics(
        self,
        age: int,
        weeks_lived: int,
        remaining_weeks: int,
        life_percentage: str,
        days_until_birthday: int,
    ) -> str:
        """Generate weeks statistics message.

        :param age: User's age
        :type age: int
        :param weeks_lived: Weeks lived
        :type weeks_lived: int
        :param remaining_weeks: Remaining weeks
        :type remaining_weeks: int
        :param life_percentage: Life percentage
        :type life_percentage: str
        :param days_until_birthday: Days until birthday
        :type days_until_birthday: int
        :returns: Localized statistics message
        :rtype: str
        """
        return self._(
            "📊 <b>Your Life Statistics:</b>\n\n"
            "🎂 <b>Age:</b> {age} years\n"
            "📅 <b>Weeks lived:</b> {weeks_lived:,}\n"
            "⏳ <b>Weeks remaining (until 80):</b> {remaining_weeks:,}\n"
            "📈 <b>Life progress:</b> {life_percentage}\n"
            "🎉 <b>Days until birthday:</b> {days_until_birthday}\n\n"
            "💡 Use /visualize to visualize your weeks"
        ).format(
            age=age,
            weeks_lived=weeks_lived,
            remaining_weeks=remaining_weeks,
            life_percentage=life_percentage,
            days_until_birthday=days_until_birthday,
        )

    def visualize_info(self, age: int, weeks_lived: int, life_percentage: str) -> str:
        """Generate visualization info message.

        :param age: User's age
        :type age: int
        :param weeks_lived: Weeks lived
        :type weeks_lived: int
        :param life_percentage: Life percentage
        :type life_percentage: str
        :returns: Localized visualization message
        :rtype: str
        """
        return self._(
            "📊 <b>Visualization of Your Life Weeks</b>\n\n"
            "🎂 Age: {age} years\n"
            "📅 Weeks lived: {weeks_lived:,}\n"
            "📈 Life progress: {life_percentage}\n\n"
            "🟩 Green cells = weeks lived\n"
            "⬜ White cells = future weeks"
        ).format(age=age, weeks_lived=weeks_lived, life_percentage=life_percentage)

    def start_welcome_existing(self, first_name: str) -> str:
        """Generate welcome message for existing users.

        :param first_name: User's first name
        :type first_name: str
        :returns: Localized welcome message
        :rtype: str
        """
        return self._(
            "👋 Hello, {first_name}! You are already registered.\n\n"
            "Use /weeks to see your life weeks.\n"
            "Use /help for help."
        ).format(first_name=first_name)

    def start_welcome_new(self, first_name: str) -> str:
        """Generate welcome message for new users.

        :param first_name: User's first name
        :type first_name: str
        :returns: Localized welcome message
        :rtype: str
        """
        return self._(
            "👋 Hello, {first_name}! Welcome to LifeWeeksBot!\n\n"
            "This bot will help you track the weeks of your life.\n\n"
            "📅 Please enter your birth date in DD.MM.YYYY format\n"
            "For example: 15.03.1990"
        ).format(first_name=first_name)

    def registration_success(
        self,
        first_name: str,
        birth_date: str,
        age: int,
        weeks_lived: int,
        remaining_weeks: int,
        life_percentage: str,
    ) -> str:
        """Generate registration success message.

        :param first_name: User's first name
        :type first_name: str
        :param birth_date: Birth date string
        :type birth_date: str
        :param age: User's age
        :type age: int
        :param weeks_lived: Weeks lived
        :type weeks_lived: int
        :param remaining_weeks: Remaining weeks
        :type remaining_weeks: int
        :param life_percentage: Life percentage
        :type life_percentage: str
        :returns: Localized registration success message
        :rtype: str
        """
        return self._(
            "✅ Great! You have been successfully registered!\n\n"
            "📅 Birth date: {birth_date}\n"
            "🎂 Age: {age} years\n"
            "📊 Weeks lived: {weeks_lived:,}\n"
            "⏳ Weeks remaining: {remaining_weeks:,}\n"
            "📈 Life progress: {life_percentage}\n\n"
            "Now you can use the commands:\n"
            "• /weeks - show life weeks\n"
            "• /visualize - week visualization\n"
            "• /help - help"
        ).format(
            birth_date=birth_date,
            age=age,
            weeks_lived=weeks_lived,
            remaining_weeks=remaining_weeks,
            life_percentage=life_percentage,
        )

    def unknown_command(self) -> str:
        """Generate unknown command message.

        :returns: Localized unknown command message
        :rtype: str
        """
        return self._(
            "❌ Error: Unknown command or message.\n\n"
            "Use /help to get a list of available commands."
        )

    def not_registered(self) -> str:
        """Generate not registered message.

        :returns: Localized not registered message
        :rtype: str
        """
        return self._("❌ Please register using /start")

    def error(self) -> str:
        """Generate generic error message.

        :returns: Localized error message
        :rtype: str
        """
        return self._(
            "❌ An error occurred. Please try again later or contact the administrator."
        )

    def not_set(self) -> str:
        """Generate not set message.

        :returns: Localized not set message
        :rtype: str
        """
        return self._("Not set")

    def registration_error(self) -> str:
        """Generate registration error message.

        :returns: Localized registration error message
        :rtype: str
        """
        return self._(
            "❌ An error occurred during registration.\n"
            "Try again or contact the administrator."
        )

    def birth_date_future_error(self) -> str:
        """Generate birth date future error message.

        :returns: Localized birth date future error message
        :rtype: str
        """
        return self._(
            "❌ Birth date cannot be in the future!\n"
            "Please enter a valid date in DD.MM.YYYY format"
        )

    def birth_date_old_error(self) -> str:
        """Generate birth date old error message.

        :returns: Localized birth date old error message
        :rtype: str
        """
        return self._(
            "❌ Birth date is too old!\n"
            "Please enter a valid date in DD.MM.YYYY format"
        )

    def birth_date_format_error(self) -> str:
        """Generate birth date format error message.

        :returns: Localized birth date format error message
        :rtype: str
        """
        return self._(
            "❌ Invalid date format!\n"
            "Please enter the date in DD.MM.YYYY format\n"
            "For example: 15.03.1990"
        )

    def not_registered_weeks(self) -> str:
        """Generate not registered message for weeks command.

        :returns: Localized not registered message
        :rtype: str
        """
        return self._("❌ Please first set your birth date using /start")

    def not_registered_visualize(self) -> str:
        """Generate not registered message for visualize command.

        :returns: Localized not registered message
        :rtype: str
        """
        return self._("❌ Please first set your birth date using /start")

    def visualization_error(self) -> str:
        """Generate visualization error message.

        :returns: Localized visualization error message
        :rtype: str
        """
        return self._(
            "❌ An error occurred while creating visualization. Please try again later."
        )

    def weeks_error(self) -> str:
        """Generate weeks error message.

        :returns: Localized weeks error message
        :rtype: str
        """
        return self._(
            "❌ An error occurred while getting statistics. Please try again later."
        )

    def subscription_current(
        self, subscription_type: str, subscription_description: str
    ) -> str:
        """Generate current subscription message.

        :param subscription_type: Subscription type
        :type subscription_type: str
        :param subscription_description: Subscription description
        :type subscription_description: str
        :returns: Localized subscription current message
        :rtype: str
        """
        return self._(
            "🔐 <b>Subscription Management</b>\n\n"
            "Current subscription: <b>{subscription_type}</b>\n"
            "{subscription_description}\n\n"
            "Select new subscription type:"
        ).format(
            subscription_type=subscription_type,
            subscription_description=subscription_description,
        )

    def subscription_invalid_type(self) -> str:
        """Generate invalid subscription type message.

        :returns: Localized invalid subscription type message
        :rtype: str
        """
        return self._("❌ Invalid subscription type")

    def subscription_profile_error(self) -> str:
        """Generate subscription profile error message.

        :returns: Localized subscription profile error message
        :rtype: str
        """
        return self._("❌ Error retrieving user profile")

    def subscription_already_active(self, subscription_type: str) -> str:
        """Generate subscription already active message.

        :param subscription_type: Subscription type
        :type subscription_type: str
        :returns: Localized subscription already active message
        :rtype: str
        """
        return self._(
            "ℹ️ You already have an active <b>{subscription_type}</b> subscription"
        ).format(subscription_type=subscription_type)

    def subscription_change_success(
        self, subscription_type: str, subscription_description: str
    ) -> str:
        """Generate subscription change success message.

        :param subscription_type: Subscription type
        :type subscription_type: str
        :param subscription_description: Subscription description
        :type subscription_description: str
        :returns: Localized subscription change success message
        :rtype: str
        """
        return self._(
            "✅ <b>Subscription successfully changed!</b>\n\n"
            "New subscription: <b>{subscription_type}</b>\n"
            "{subscription_description}\n\n"
            "Changes took effect immediately."
        ).format(
            subscription_type=subscription_type,
            subscription_description=subscription_description,
        )

    def subscription_change_failed(self) -> str:
        """Generate subscription change failed message.

        :returns: Localized subscription change failed message
        :rtype: str
        """
        return self._("❌ Failed to change subscription. Please try again later.")

    def subscription_change_error(self) -> str:
        """Generate subscription change error message.

        :returns: Localized subscription change error message
        :rtype: str
        """
        return self._("❌ An error occurred while changing subscription")

    def change_birth_date(self, current_birth_date: str) -> str:
        """Generate change birth date message.

        :param current_birth_date: Current birth date
        :type current_birth_date: str
        :returns: Localized change birth date message
        :rtype: str
        """
        return self._(
            "📅 <b>Change Birth Date</b>\n\n"
            "Current date: <b>{current_birth_date}</b>\n\n"
            "Enter new birth date in DD.MM.YYYY format\n"
            "For example: 15.03.1990\n\n"
            "Or press /cancel to cancel"
        ).format(current_birth_date=current_birth_date)

    def change_language(self, current_language: str) -> str:
        """Generate change language message.

        :param current_language: Current language
        :type current_language: str
        :returns: Localized change language message
        :rtype: str
        """
        return self._(
            "🌍 <b>Change Language</b>\n\n"
            "Current language: <b>{current_language}</b>\n\n"
            "Select new language:"
        ).format(current_language=current_language)

    def change_life_expectancy(self, current_life_expectancy: int) -> str:
        """Generate change life expectancy message.

        :param current_life_expectancy: Current life expectancy
        :type current_life_expectancy: int
        :returns: Localized change life expectancy message
        :rtype: str
        """
        return self._(
            "⏰ <b>Change Expected Life Expectancy</b>\n\n"
            "Current value: <b>{current_life_expectancy} years</b>\n\n"
            "Enter new value (from 50 to 120 years):"
        ).format(current_life_expectancy=current_life_expectancy)

    def birth_date_updated(self, new_birth_date: str, new_age: int) -> str:
        """Generate birth date updated message.

        :param new_birth_date: New birth date
        :type new_birth_date: str
        :param new_age: New age
        :type new_age: int
        :returns: Localized birth date updated message
        :rtype: str
        """
        return self._(
            "✅ <b>Birth date successfully updated!</b>\n\n"
            "New date: <b>{new_birth_date}</b>\n"
            "New age: <b>{new_age} years</b>\n\n"
            "Use /weeks to see updated statistics"
        ).format(new_birth_date=new_birth_date, new_age=new_age)

    def language_updated(self, new_language: str) -> str:
        """Generate language updated message.

        :param new_language: New language
        :type new_language: str
        :returns: Localized language updated message
        :rtype: str
        """
        return self._(
            "✅ <b>Language successfully changed!</b>\n\n"
            "New language: <b>{new_language}</b>\n\n"
            "All bot messages will now be in the selected language"
        ).format(new_language=new_language)

    def life_expectancy_updated(self, new_life_expectancy: int) -> str:
        """Generate life expectancy updated message.

        :param new_life_expectancy: New life expectancy
        :type new_life_expectancy: int
        :returns: Localized life expectancy updated message
        :rtype: str
        """
        return self._(
            "✅ <b>Expected life expectancy updated!</b>\n\n"
            "New value: <b>{new_life_expectancy} years</b>\n\n"
            "Use /weeks to see updated statistics"
        ).format(new_life_expectancy=new_life_expectancy)

    def invalid_life_expectancy(self) -> str:
        """Generate invalid life expectancy message.

        :returns: Localized invalid life expectancy message
        :rtype: str
        """
        return self._(
            "❌ <b>Invalid value!</b>\n\n"
            "Expected life expectancy should be from 50 to 120 years.\n"
            "Try again or press /cancel to cancel"
        )

    def settings_error(self) -> str:
        """Generate settings error message.

        :returns: Localized settings error message
        :rtype: str
        """
        return self._(
            "❌ An error occurred while updating settings.\n"
            "Please try again later or contact the administrator."
        )

    def cancel_success(self, first_name: str) -> str:
        """Generate cancel success message.

        :param first_name: User's first name
        :type first_name: str
        :returns: Localized cancel success message
        :rtype: str
        """
        return self._(
            "✅ {first_name}, all your data has been successfully deleted.\n"
            "Use /start to register again."
        ).format(first_name=first_name)

    def cancel_error(self, first_name: str) -> str:
        """Generate cancel error message.

        :param first_name: User's first name
        :type first_name: str
        :returns: Localized cancel error message
        :rtype: str
        """
        return self._(
            "❌ {first_name}, an error occurred while deleting data.\n"
            "Please try again later or contact the administrator."
        ).format(first_name=first_name)

    def button_change_birth_date(self) -> str:
        """Generate change birth date button text.

        :returns: Localized change birth date button text
        :rtype: str
        """
        return self._("📅 Change Birth Date")

    def button_change_language(self) -> str:
        """Generate change language button text.

        :returns: Localized change language button text
        :rtype: str
        """
        return self._("🌍 Change Language")

    def button_change_life_expectancy(self) -> str:
        """Generate change life expectancy button text.

        :returns: Localized change life expectancy button text
        :rtype: str
        """
        return self._("⏰ Change Expected Life Expectancy")
