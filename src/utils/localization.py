"""Localization module for LifeWeeksBot.

This module contains all user-facing messages in multiple languages.
Supports Russian (ru), English (en), Ukrainian (ua), and Belarusian (by).
"""

from typing import Any, Dict

# Supported languages
LANGUAGES = ["ru", "en", "ua", "by"]

# Default language
DEFAULT_LANGUAGE = "ru"

ALL_MESSAGES: Dict[str, Dict[str, Dict[str, str]]] = {
    "command_start": {
        "welcome_existing": {
            "ru": "👋 Привет, {first_name}! Ты уже зарегистрирован.\n\n"
            "Используй /weeks чтобы посмотреть свои недели жизни.\n"
            "Используй /help для справки.",
            "en": "👋 Hello, {first_name}! You are already registered.\n\n"
            "Use /weeks to see your life weeks.\n"
            "Use /help for help.",
            "ua": "👋 Привіт, {first_name}! Ти вже зареєстрований.\n\n"
            "Використовуй /weeks щоб подивитися свої тижні життя.\n"
            "Використовуй /help для довідки.",
            "by": "👋 Прывітанне, {first_name}! Ты ўжо зарэгістраваны.\n\n"
            "Выкарыстоўвай /weeks каб паглядзець свае тыдні жыцця.\n"
            "Выкарыстоўвай /help для даведкі.",
        },
        "welcome_new": {
            "ru": "👋 Привет, {first_name}! Добро пожаловать в LifeWeeksBot!\n\n"
            "Этот бот поможет тебе отслеживать недели твоей жизни.\n\n"
            "📅 Пожалуйста, введи свою дату рождения в формате ДД.ММ.ГГГГ\n"
            "Например: 15.03.1990",
            "en": "👋 Hello, {first_name}! Welcome to LifeWeeksBot!\n\n"
            "This bot will help you track the weeks of your life.\n\n"
            "📅 Please enter your birth date in DD.MM.YYYY format\n"
            "For example: 15.03.1990",
            "ua": "👋 Привіт, {first_name}! Ласкаво просимо до LifeWeeksBot!\n\n"
            "Цей бот допоможе тобі відстежувати тижні твого життя.\n\n"
            "📅 Будь ласка, введи свою дату народження у форматі ДД.ММ.РРРР\n"
            "Наприклад: 15.03.1990",
            "by": "👋 Прывітанне, {first_name}! Сардэчна запрашаем у LifeWeeksBot!\n\n"
            "Гэты бот дапаможа табе адсочваць тыдні твайго жыцця.\n\n"
            "📅 Калі ласка, увядзі сваю дату нараджэння ў фармаце ДД.ММ.ГГГГ\n"
            "Напрыклад: 15.03.1990",
        },
    },
    "birth_date_validation": {
        "future_date_error": {
            "ru": "❌ Дата рождения не может быть в будущем!\n"
            "Пожалуйста, введи корректную дату в формате ДД.ММ.ГГГГ",
            "en": "❌ Birth date cannot be in the future!\n"
            "Please enter a valid date in DD.MM.YYYY format",
            "ua": "❌ Дата народження не може бути в майбутньому!\n"
            "Будь ласка, введи коректну дату у форматі ДД.ММ.РРРР",
            "by": "❌ Дата нараджэння не можа быць у будучыні!\n"
            "Калі ласка, увядзі карэктную дату ў фармаце ДД.ММ.ГГГГ",
        },
        "old_date_error": {
            "ru": "❌ Дата рождения слишком старая!\n"
            "Пожалуйста, введи корректную дату в формате ДД.ММ.ГГГГ",
            "en": "❌ Birth date is too old!\n"
            "Please enter a valid date in DD.MM.YYYY format",
            "ua": "❌ Дата народження занадто стара!\n"
            "Будь ласка, введи коректну дату у форматі ДД.ММ.РРРР",
            "by": "❌ Дата нараджэння занадта старая!\n"
            "Калі ласка, увядзі карэктную дату ў фармаце ДД.ММ.ГГГГ",
        },
        "format_error": {
            "ru": "❌ Неверный формат даты!\n"
            "Пожалуйста, введи дату в формате ДД.ММ.ГГГГ\n"
            "Например: 15.03.1990",
            "en": "❌ Invalid date format!\n"
            "Please enter the date in DD.MM.YYYY format\n"
            "For example: 15.03.1990",
            "ua": "❌ Невірний формат дати!\n"
            "Будь ласка, введи дату у форматі ДД.ММ.РРРР\n"
            "Наприклад: 15.03.1990",
            "by": "❌ Няправільны фармат даты!\n"
            "Калі ласка, увядзі дату ў фармаце ДД.ММ.ГГГГ\n"
            "Напрыклад: 15.03.1990",
        },
    },
    "registration": {
        "success": {
            "ru": "✅ Отлично! Ты успешно зарегистрирован!\n\n"
            "📅 Дата рождения: {birth_date}\n"
            "🎂 Возраст: {age} лет\n"
            "📊 Недель прожито: {weeks_lived:,}\n\n"
            "Теперь ты можешь использовать команды:\n"
            "• /weeks - показать недели жизни\n"
            "• /visualize - визуализация недель\n"
            "• /help - справка",
            "en": "✅ Great! You have been successfully registered!\n\n"
            "📅 Birth date: {birth_date}\n"
            "🎂 Age: {age} years\n"
            "📊 Weeks lived: {weeks_lived:,}\n\n"
            "Now you can use the commands:\n"
            "• /weeks - show life weeks\n"
            "• /visualize - week visualization\n"
            "• /help - help",
            "ua": "✅ Відмінно! Ти успішно зареєстрований!\n\n"
            "📅 Дата народження: {birth_date}\n"
            "🎂 Вік: {age} років\n"
            "📊 Тижнів прожито: {weeks_lived:,}\n\n"
            "Тепер ти можеш використовувати команди:\n"
            "• /weeks - показати тижні життя\n"
            "• /visualize - візуалізація тижнів\n"
            "• /help - довідка",
            "by": "✅ Выдатна! Ты паспяхова зарэгістраваны!\n\n"
            "📅 Дата нараджэння: {birth_date}\n"
            "🎂 Узрост: {age} гадоў\n"
            "📊 Тыдняў пражыта: {weeks_lived:,}\n\n"
            "Цяпер ты можаш выкарыстоўваць каманды:\n"
            "• /weeks - паказаць тыдні жыцця\n"
            "• /visualize - візуалізацыя тыдняў\n"
            "• /help - даведка",
        },
        "database_error": {
            "ru": "❌ Произошла ошибка при сохранении данных.\n"
            "Попробуй еще раз или обратись к администратору.",
            "en": "❌ An error occurred while saving data.\n"
            "Try again or contact the administrator.",
            "ua": "❌ Сталася помилка при збереженні даних.\n"
            "Спробуй ще раз або звернися до адміністратора.",
            "by": "❌ Адбылася памылка пры захаванні даных.\n"
            "Паспрабуй яшчэ раз або звярніся да адміністратара.",
        },
    },
    "command_cancel": {
        "cancelled": {
            "ru": "❌ Регистрация отменена.\n" "Используй /start чтобы начать заново.",
            "en": "❌ Registration cancelled.\n" "Use /start to start over.",
            "ua": "❌ Реєстрацію скасовано.\n" "Використовуй /start щоб почати заново.",
            "by": "❌ Рэгістрацыя адменена.\n"
            "Выкарыстоўвай /start каб пачаць нанова.",
        },
        "user_deleted": {
            "ru": "🗑️ Все данные о вас удалены.\n"
            "Используй /start чтобы зарегистрироваться заново.",
            "en": "🗑️ All your data has been deleted.\n" "Use /start to register again.",
            "ua": "🗑️ Всі дані про вас видалені.\n"
            "Використовуй /start щоб зареєструватися заново.",
            "by": "🗑️ Усе даныя пра вас выдалены.\n"
            "Выкарыстоўвай /start каб зарэгістравацца нанова.",
        },
        "deletion_error": {
            "ru": "❌ Произошла ошибка при удалении данных.\n"
            "Попробуйте позже или обратитесь к администратору.",
            "en": "❌ An error occurred while deleting data.\n"
            "Please try again later or contact the administrator.",
            "ua": "❌ Сталася помилка при видаленні даних.\n"
            "Спробуйте пізніше або зверніться до адміністратора.",
            "by": "❌ Адбылася памылка пры выдаленні даных.\n"
            "Паспрабуйце пазней або звярніцеся да адміністратара.",
        },
    },
    "command_weeks": {
        "not_registered": {
            "ru": "❌ Пожалуйста, сначала установите дату рождения с помощью /start",
            "en": "❌ Please first set your birth date using /start",
            "ua": "❌ Будь ласка, спочатку встановіть дату народження за допомогою /start",
            "by": "❌ Калі ласка, спачатку ўсталюйце дату нараджэння з дапамогай /start",
        },
        "statistics": {
            "ru": "📊 <b>Ваша статистика жизни:</b>\n\n"
            "🎂 <b>Возраст:</b> {age} лет\n"
            "📅 <b>Прожито недель:</b> {weeks_lived:,}\n"
            "⏳ <b>Осталось недель (до 80 лет):</b> {remaining_weeks:,}\n"
            "📈 <b>Прогресс жизни:</b> {life_percentage}\n"
            "🎉 <b>Дней до дня рождения:</b> {days_until_birthday}\n\n"
            "💡 Используйте /visualize для визуализации ваших недель",
            "en": "📊 <b>Your Life Statistics:</b>\n\n"
            "🎂 <b>Age:</b> {age} years\n"
            "📅 <b>Weeks lived:</b> {weeks_lived:,}\n"
            "⏳ <b>Weeks remaining (until 80):</b> {remaining_weeks:,}\n"
            "📈 <b>Life progress:</b> {life_percentage}\n"
            "🎉 <b>Days until birthday:</b> {days_until_birthday}\n\n"
            "💡 Use /visualize to visualize your weeks",
            "ua": "📊 <b>Ваша статистика життя:</b>\n\n"
            "🎂 <b>Вік:</b> {age} років\n"
            "📅 <b>Прожито тижнів:</b> {weeks_lived:,}\n"
            "⏳ <b>Залишилося тижнів (до 80 років):</b> {remaining_weeks:,}\n"
            "📈 <b>Прогрес життя:</b> {life_percentage}\n"
            "🎉 <b>Днів до дня народження:</b> {days_until_birthday}\n\n"
            "💡 Використовуйте /visualize для візуалізації ваших тижнів",
            "by": "📊 <b>Ваша статыстыка жыцця:</b>\n\n"
            "🎂 <b>Узрост:</b> {age} гадоў\n"
            "📅 <b>Пражыта тыдняў:</b> {weeks_lived:,}\n"
            "⏳ <b>Засталося тыдняў (да 80 гадоў):</b> {remaining_weeks:,}\n"
            "📈 <b>Прагрэс жыцця:</b> {life_percentage}\n"
            "🎉 <b>Дзён да дня нараджэння:</b> {days_until_birthday}\n\n"
            "💡 Выкарыстоўвайце /visualize для візуалізацыі вашых тыдняў",
        },
        "error": {
            "ru": "❌ Произошла ошибка при получении статистики. Попробуйте позже.",
            "en": "❌ An error occurred while getting statistics. Please try again later.",
            "ua": "❌ Сталася помилка при отриманні статистики. Спробуйте пізніше.",
            "by": "❌ Адбылася памылка пры атрыманні статыстыкі. Паспрабуйце пазней.",
        },
    },
    "command_visualize": {
        "not_registered": {
            "ru": "❌ Пожалуйста, сначала установите дату рождения с помощью /start",
            "en": "❌ Please first set your birth date using /start",
            "ua": "❌ Будь ласка, спочатку встановіть дату народження за допомогою /start",
            "by": "❌ Калі ласка, спачатку ўсталюйце дату нараджэння з дапамогай /start",
        },
        "caption": {
            "ru": "📊 <b>Визуализация ваших недель жизни</b>\n\n"
            "🎂 Возраст: {age} лет\n"
            "📅 Прожито недель: {weeks_lived:,}\n"
            "📈 Прогресс жизни: {life_percentage}\n\n"
            "🟩 Зеленые клетки = прожитые недели\n"
            "⬜ Белые клетки = будущие недели",
            "en": "📊 <b>Visualization of Your Life Weeks</b>\n\n"
            "🎂 Age: {age} years\n"
            "📅 Weeks lived: {weeks_lived:,}\n"
            "📈 Life progress: {life_percentage}\n\n"
            "🟩 Green cells = weeks lived\n"
            "⬜ White cells = future weeks",
            "ua": "📊 <b>Візуалізація ваших тижнів життя</b>\n\n"
            "🎂 Вік: {age} років\n"
            "📅 Прожито тижнів: {weeks_lived:,}\n"
            "📈 Прогрес життя: {life_percentage}\n\n"
            "🟩 Зелені клітинки = прожиті тижні\n"
            "⬜ Білі клітинки = майбутні тижні",
            "by": "📊 <b>Візуалізацыя вашых тыдняў жыцця</b>\n\n"
            "🎂 Узрост: {age} гадоў\n"
            "📅 Пражыта тыдняў: {weeks_lived:,}\n"
            "📈 Прагрэс жыцця: {life_percentage}\n\n"
            "🟩 Зялёныя клеткі = пражытыя тыдні\n"
            "⬜ Белыя клеткі = будучыя тыдні",
        },
        "error": {
            "ru": "❌ Произошла ошибка при создании визуализации. Попробуйте позже.",
            "en": "❌ An error occurred while creating visualization. Please try again later.",
            "ua": "❌ Сталася помилка при створенні візуалізації. Спробуйте пізніше.",
            "by": "❌ Адбылася памылка пры стварэнні візуалізацыі. Паспрабуйце пазней.",
        },
        "legend": {
            "ru": "🟩 Прожитые недели | ⬜ Будущие недели",
            "en": "🟩 Lived weeks | ⬜ Future weeks",
            "ua": "🟩 Прожиті тижні | ⬜ Майбутні тижні",
            "by": "🟩 Пражытыя тыдні | ⬜ Будучыя тыдні",
        },
    },
    "command_help": {
        "help_text": {
            "ru": "🤖 LifeWeeksBot - Помогает отслеживать недели твоей жизни\n\n"
            "📋 Доступные команды:\n"
            "• /start - Регистрация и настройка\n"
            "• /weeks - Показать недели жизни\n"
            "• /visualize - Визуализация недель жизни\n"
            "• /help - Эта справка\n\n"
            "💡 Интересные факты:\n"
            "• В году 52 недели\n"
            "• Средняя продолжительность жизни: 80 лет\n"
            "• Это примерно 4,160 недель\n\n"
            "🎯 Цель бота - помочь тебе осознать ценность времени!",
            "en": "🤖 LifeWeeksBot - Helps you track the weeks of your life\n\n"
            "📋 Available commands:\n"
            "• /start - Registration and setup\n"
            "• /weeks - Show life weeks\n"
            "• /visualize - Life weeks visualization\n"
            "• /help - This help\n\n"
            "💡 Interesting facts:\n"
            "• There are 52 weeks in a year\n"
            "• Average life expectancy: 80 years\n"
            "• That's about 4,160 weeks\n\n"
            "🎯 The bot's goal is to help you realize the value of time!",
            "ua": "🤖 LifeWeeksBot - Допомагає відстежувати тижні твого життя\n\n"
            "📋 Доступні команди:\n"
            "• /start - Реєстрація та налаштування\n"
            "• /weeks - Показати тижні життя\n"
            "• /visualize - Візуалізація тижнів життя\n"
            "• /help - Ця довідка\n\n"
            "💡 Цікаві факти:\n"
            "• У році 52 тижні\n"
            "• Середня тривалість життя: 80 років\n"
            "• Це приблизно 4,160 тижнів\n\n"
            "🎯 Мета бота - допомогти тобі усвідомити цінність часу!",
            "by": "🤖 LifeWeeksBot - Дапамагае адсочваць тыдні твайго жыцця\n\n"
            "📋 Даступныя каманды:\n"
            "• /start - Рэгістрацыя і наладжванне\n"
            "• /weeks - Паказаць тыдні жыцця\n"
            "• /visualize - Візуалізацыя тыдняў жыцця\n"
            "• /help - Гэта даведка\n\n"
            "💡 Цікавыя факты:\n"
            "• У годзе 52 тыдні\n"
            "• Сярэдняя працягласць жыцця: 80 гадоў\n"
            "• Гэта прыблізна 4,160 тыдняў\n\n"
            "🎯 Мэта бота - дапамагчы табе ўсвядоміць каштоўнасць часу!",
        }
    },
    "notifications": {
        "weekly_message": {
            "ru": "📅 Начинается {week_number:,} неделя вашей жизни!",
            "en": "📅 The {week_number:,} week of your life has begun!",
            "ua": "📅 Починається {week_number:,} тиждень вашого життя!",
            "by": "📅 Пачынаецца {week_number:,} тыдзень вашага жыцця!",
        }
    },
    "common": {
        "not_registered": {
            "ru": "❌ Пожалуйста, зарегистрируйтесь с помощью /start",
            "en": "❌ Please register using /start",
            "ua": "❌ Будь ласка, зареєструйтеся за допомогою /start",
            "by": "❌ Калі ласка, зарэгіструйцеся з дапамогай /start",
        },
        "error": {
            "ru": "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору.",
            "en": "❌ An error occurred. Please try again later or contact the administrator.",
            "ua": "❌ Сталася памылка. Спробуйце пізніше або зверніцеся да адміністратора.",
            "by": "❌ Адбылася памылка. Паспрабуйце пазней або звярніцеся да адміністратара.",
        },
    },
}


def get_message(
    message_key: str, sub_key: str, language: str = DEFAULT_LANGUAGE, **kwargs: Any
) -> str:
    """Get localized message with optional formatting.

    :param message_key: Main message key (e.g., 'command_start')
    :type message_key: str
    :param sub_key: Sub-message key (e.g., 'welcome_new')
    :type sub_key: str
    :param language: Language code (ru, en, ua, by)
    :type language: str
    :param kwargs: Format parameters for the message
    :type kwargs: Any
    :returns: Localized and formatted message
    :rtype: str
    :raises KeyError: If message key or language is not found
    """
    if language not in LANGUAGES:
        language = DEFAULT_LANGUAGE

    try:
        message = ALL_MESSAGES[message_key][sub_key][language]
        return message.format(**kwargs) if kwargs else message
    except KeyError as e:
        # Fallback to default language if translation is missing
        if language != DEFAULT_LANGUAGE:
            try:
                message = ALL_MESSAGES[message_key][sub_key][DEFAULT_LANGUAGE]
                return message.format(**kwargs) if kwargs else message
            except KeyError:
                raise KeyError(f"Message not found: {message_key}.{sub_key}") from e
        else:
            raise KeyError(f"Message not found: {message_key}.{sub_key}") from e


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
