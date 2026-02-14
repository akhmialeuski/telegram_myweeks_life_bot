from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_settings_keyboard(pgettext) -> InlineKeyboardMarkup:
    """Get the main settings keyboard."""
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
                text=pgettext(
                    "buttons.change_notification_schedule",
                    "🔔 Change reminder schedule (Premium)",
                ),
                callback_data="settings_notification_schedule",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Get the language selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="language_ru")],
        [InlineKeyboardButton("🇺🇸 English", callback_data="language_en")],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="language_ua")],
        [InlineKeyboardButton("🇧🇾 Беларуская", callback_data="language_by")],
    ]
    return InlineKeyboardMarkup(keyboard)
