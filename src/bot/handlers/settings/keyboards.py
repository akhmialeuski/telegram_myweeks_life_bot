from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_settings_keyboard(
    pgettext, *, is_premium: bool = False
) -> InlineKeyboardMarkup:
    """Get the main settings keyboard.

    Builds the inline keyboard for the /settings menu. The notification
    schedule button is only shown to premium/trial subscribers.

    :param pgettext: Localized pgettext translation function
    :param is_premium: Whether the user has an active premium subscription
    :type is_premium: bool
    :returns: Inline keyboard markup for the settings menu
    :rtype: InlineKeyboardMarkup
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=pgettext("buttons.change_birth_date", "📅 Change birth date"),
                callback_data="settings_birth_date",
            )
        ],
        [
            InlineKeyboardButton(
                text=pgettext("buttons.change_language", "🌍 Change language"),
                callback_data="settings_language",
            )
        ],
        [
            InlineKeyboardButton(
                text=pgettext(
                    "buttons.change_life_expectancy",
                    "⏰ Change life expectancy",
                ),
                callback_data="settings_life_expectancy",
            )
        ],
        [
            InlineKeyboardButton(
                text=pgettext("buttons.change_timezone", "🌍 Change timezone"),
                callback_data="settings_timezone",
            )
        ],
    ]

    if is_premium:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=pgettext(
                        "buttons.change_notification_schedule",
                        "🔔 Change reminder schedule",
                    ),
                    callback_data="settings_notification_schedule",
                )
            ]
        )

    return InlineKeyboardMarkup(keyboard)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Get the language selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="language_ru")],
        [InlineKeyboardButton("🇺🇸 English", callback_data="language_en")],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="language_ua")],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="language_ua")],
        [InlineKeyboardButton("🇧🇾 Беларуская", callback_data="language_by")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_timezone_keyboard(pgettext) -> InlineKeyboardMarkup:
    """Get the timezone selection keyboard.

    :param pgettext: Localized pgettext translation function
    :type pgettext: Callable
    :returns: Inline keyboard markup for timezone selection
    :rtype: InlineKeyboardMarkup
    """
    keyboard = [
        [InlineKeyboardButton("UTC", callback_data="timezone_UTC")],
        [InlineKeyboardButton("Europe/Moscow", callback_data="timezone_Europe/Moscow")],
        [InlineKeyboardButton("Europe/Warsaw", callback_data="timezone_Europe/Warsaw")],
        [InlineKeyboardButton("Europe/Minsk", callback_data="timezone_Europe/Minsk")],
        [
            InlineKeyboardButton(
                "America/New_York", callback_data="timezone_America/New_York"
            )
        ],
        [
            InlineKeyboardButton(
                text=pgettext("buttons.other_timezone", "🌐 Other"),
                callback_data="timezone_other",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
