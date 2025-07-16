"""Localization module for LifeWeeksBot.

This module contains all user-facing messages in multiple languages.
Supports Russian (ru), English (en), Ukrainian (ua), and Belarusian (by).
"""

from enum import StrEnum, auto
from typing import Any, Dict


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
        "registration_success": {
            "ru": "✅ Отлично! Ты успешно зарегистрирован!\n\n"
            "📅 Дата рождения: {birth_date}\n"
            "🎂 Возраст: {age} лет\n"
            "📊 Недель прожито: {weeks_lived:,}\n"
            "⏳ Осталось недель: {remaining_weeks:,}\n"
            "📈 Прогресс жизни: {life_percentage}\n\n"
            "Теперь ты можешь использовать команды:\n"
            "• /weeks - показать недели жизни\n"
            "• /visualize - визуализация недель\n"
            "• /help - справка",
            "en": "✅ Great! You have been successfully registered!\n\n"
            "📅 Birth date: {birth_date}\n"
            "🎂 Age: {age} years\n"
            "📊 Weeks lived: {weeks_lived:,}\n"
            "⏳ Weeks remaining: {remaining_weeks:,}\n"
            "📈 Life progress: {life_percentage}\n\n"
            "Now you can use the commands:\n"
            "• /weeks - show life weeks\n"
            "• /visualize - week visualization\n"
            "• /help - help",
            "ua": "✅ Відмінно! Ти успішно зареєстрований!\n\n"
            "📅 Дата народження: {birth_date}\n"
            "🎂 Вік: {age} років\n"
            "📊 Тижнів прожито: {weeks_lived:,}\n"
            "⏳ Залишилося тижнів: {remaining_weeks:,}\n"
            "📈 Прогрес життя: {life_percentage}\n\n"
            "Тепер ти можеш використовувати команди:\n"
            "• /weeks - показати тижні життя\n"
            "• /visualize - візуалізація тижнів\n"
            "• /help - довідка",
            "by": "✅ Выдатна! Ты паспяхова зарэгістраваны!\n\n"
            "📅 Дата нараджэння: {birth_date}\n"
            "🎂 Узрост: {age} гадоў\n"
            "📊 Тыдняў пражыта: {weeks_lived:,}\n"
            "⏳ Засталося тыдняў: {remaining_weeks:,}\n"
            "📈 Прагрэс жыцця: {life_percentage}\n\n"
            "Цяпер ты можаш выкарыстоўваць каманды:\n"
            "• /weeks - паказаць тыдні жыцця\n"
            "• /visualize - візуалізацыя тыдняў\n"
            "• /help - даведка",
        },
        "registration_error": {
            "ru": "❌ Произошла ошибка при регистрации.\n"
            "Попробуй еще раз или обратись к администратору.",
            "en": "❌ An error occurred during registration.\n"
            "Try again or contact the administrator.",
            "ua": "❌ Сталася помилка при реєстрації.\n"
            "Спробуй ще раз або звернися до адміністратора.",
            "by": "❌ Адбылася памылка пры рэгістрацыі.\n"
            "Паспрабуй яшчэ раз або звярніся да адміністратара.",
        },
        "birth_date_future_error": {
            "ru": "❌ Дата рождения не может быть в будущем!\n"
            "Пожалуйста, введи корректную дату в формате ДД.ММ.ГГГГ",
            "en": "❌ Birth date cannot be in the future!\n"
            "Please enter a valid date in DD.MM.YYYY format",
            "ua": "❌ Дата народження не може бути в майбутньому!\n"
            "Будь ласка, введи коректну дату у форматі ДД.ММ.РРРР",
            "by": "❌ Дата нараджэння не можа быць у будучыні!\n"
            "Калі ласка, увядзі карэктную дату ў фармаце ДД.ММ.ГГГГ",
        },
        "birth_date_old_error": {
            "ru": "❌ Дата рождения слишком старая!\n"
            "Пожалуйста, введи корректную дату в формате ДД.ММ.ГГГГ",
            "en": "❌ Birth date is too old!\n"
            "Please enter a valid date in DD.MM.YYYY format",
            "ua": "❌ Дата народження занадто стара!\n"
            "Будь ласка, введи коректну дату у форматі ДД.ММ.РРРР",
            "by": "❌ Дата нараджэння занадта старая!\n"
            "Калі ласка, увядзі карэктную дату ў фармаце ДД.ММ.ГГГГ",
        },
        "birth_date_format_error": {
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
        "success": {
            "ru": "✅ {first_name}, все данные о вас успешно удалены.\n"
            "Используй /start чтобы зарегистрироваться заново.",
            "en": "✅ {first_name}, all your data has been successfully deleted.\n"
            "Use /start to register again.",
            "ua": "✅ {first_name}, всі дані про вас успішно видалені.\n"
            "Використовуй /start щоб зареєструватися заново.",
            "by": "✅ {first_name}, усе даныя пра вас паспяхова выдалены.\n"
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
        "error": {
            "ru": "❌ {first_name}, произошла ошибка при удалении данных.\n"
            "Попробуйте позже или обратитесь к администратору.",
            "en": "❌ {first_name}, an error occurred while deleting data.\n"
            "Please try again later or contact the administrator.",
            "ua": "❌ {first_name}, сталася помилка при видаленні даних.\n"
            "Спробуйте пізніше або зверніться до адміністратора.",
            "by": "❌ {first_name}, адбылася памылка пры выдаленні даных.\n"
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
        "visualization_info": {
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
            "• /settings - Настройки\n"
            "• /subscription - Подписка\n"
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
            "• /settings - Settings\n"
            "• /subscription - Subscription\n"
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
            "• /settings - Налаштування\n"
            "• /subscription - Підписка\n"
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
            "• /settings - Налады\n"
            "• /subscription - Падпіска\n"
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
            "by": "❌ Калі ласка, зарэгіструйтеся з дапамогай /start",
        },
        "error": {
            "ru": "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору.",
            "en": "❌ An error occurred. Please try again later or contact the administrator.",
            "ua": "❌ Сталася памылка. Спробуйте пізніше або зверніцеся да адміністратора.",
            "by": "❌ Адбылася памылка. Паспрабуйте пазней або звярніцеся да адміністратара.",
        },
        "unknown_command": {
            "ru": "❌ Ошибка: Неизвестная команда или сообщение.\n\nИспользуйте /help для получения списка доступных команд.",
            "en": "❌ Error: Unknown command or message.\n\nUse /help to get a list of available commands.",
            "ua": "❌ Помилка: Невідома команда або повідомлення.\n\nВикористовуйте /help для отримання списку доступних команд.",
            "by": "❌ Памылка: Невядомая каманда або паведамленне.\n\nВыкарыстоўвайце /help для атрымання спісу даступных каманд.",
        },
    },
    "command_subscription": {
        "current_subscription": {
            "ru": "🔐 <b>Управление подпиской</b>\n\n"
            "Текущая подписка: <b>{subscription_type}</b>\n"
            "{subscription_description}\n\n"
            "Выберите новый тип подписки:",
            "en": "🔐 <b>Subscription Management</b>\n\n"
            "Current subscription: <b>{subscription_type}</b>\n"
            "{subscription_description}\n\n"
            "Select new subscription type:",
            "ua": "🔐 <b>Управління підпискою</b>\n\n"
            "Поточна підписка: <b>{subscription_type}</b>\n"
            "{subscription_description}\n\n"
            "Оберіть новий тип підписки:",
            "by": "🔐 <b>Кіраванне падпіскай</b>\n\n"
            "Бягучая падпіска: <b>{subscription_type}</b>\n"
            "{subscription_description}\n\n"
            "Выберыце новы тып падпіскі:",
        },
        "subscription_descriptions": {
            "basic": {
                "ru": "Базовая подписка - стандартный функционал",
                "en": "Basic subscription - standard functionality",
                "ua": "Базова підписка - стандартний функціонал",
                "by": "Базавая падпіска - стандартны функцыянал",
            },
            "premium": {
                "ru": "Премиум подписка - расширенные возможности",
                "en": "Premium subscription - extended features",
                "ua": "Преміум підписка - розширені можливості",
                "by": "Прэміум падпіска - пашыраныя магчымасці",
            },
            "trial": {
                "ru": "Пробная подписка - ограниченный период",
                "en": "Trial subscription - limited period",
                "ua": "Пробна підписка - обмежений період",
                "by": "Пробная падпіска - абмежаваны перыяд",
            },
        },
        "invalid_subscription_type": {
            "ru": "❌ Неверный тип подписки",
            "en": "❌ Invalid subscription type",
            "ua": "❌ Невірний тип підписки",
            "by": "❌ Няправільны тып падпіскі",
        },
        "invalid_type": {
            "ru": "❌ Неверный тип подписки",
            "en": "❌ Invalid subscription type",
            "ua": "❌ Невірний тип підписки",
            "by": "❌ Няправільны тып падпіскі",
        },
        "profile_error": {
            "ru": "❌ Ошибка получения профиля пользователя",
            "en": "❌ Error retrieving user profile",
            "ua": "❌ Помилка отримання профілю користувача",
            "by": "❌ Памылка атрымання профілю карыстальніка",
        },
        "already_active": {
            "ru": "ℹ️ У вас уже активна подписка <b>{subscription_type}</b>",
            "en": "ℹ️ You already have an active <b>{subscription_type}</b> subscription",
            "ua": "ℹ️ У вас вже активна підписка <b>{subscription_type}</b>",
            "by": "ℹ️ У вас ужо актыўная падпіска <b>{subscription_type}</b>",
        },
        "change_success": {
            "ru": "✅ <b>Подписка успешно изменена!</b>\n\n"
            "Новая подписка: <b>{subscription_type}</b>\n"
            "{subscription_description}\n\n"
            "Изменения вступили в силу немедленно.",
            "en": "✅ <b>Subscription successfully changed!</b>\n\n"
            "New subscription: <b>{subscription_type}</b>\n"
            "{subscription_description}\n\n"
            "Changes took effect immediately.",
            "ua": "✅ <b>Підписку успішно змінено!</b>\n\n"
            "Нова підписка: <b>{subscription_type}</b>\n"
            "{subscription_description}\n\n"
            "Зміни набули чинності негайно.",
            "by": "✅ <b>Падпіска паспяхова зменена!</b>\n\n"
            "Новая падпіска: <b>{subscription_type}</b>\n"
            "{subscription_description}\n\n"
            "Змены ўступілі ў сілу неадкладна.",
        },
        "change_failed": {
            "ru": "❌ Не удалось изменить подписку. Попробуйте позже.",
            "en": "❌ Failed to change subscription. Please try again later.",
            "ua": "❌ Не вдалося змінити підписку. Спробуйте пізніше.",
            "by": "❌ Не ўдалося змяніць падпіску. Паспрабуйце пазней.",
        },
        "change_error": {
            "ru": "❌ Произошла ошибка при изменении подписки",
            "en": "❌ An error occurred while changing subscription",
            "ua": "❌ Сталася помилка пры зміні підписки",
            "by": "❌ Адбылася памылка пры змене падпіскі",
        },
    },
    "command_settings": {
        "basic_settings": {
            "ru": "⚙️ <b>Настройки профиля (Базовая подписка)</b>\n\n"
            "📅 <b>Дата рождения:</b> {birth_date}\n"
            "🌍 <b>Язык:</b> {language_name}\n"
            "⏰ <b>Ожидаемая продолжительность жизни:</b> {life_expectancy} лет\n\n"
            "Выберите, что хотите изменить:",
            "en": "⚙️ <b>Profile Settings (Basic Subscription)</b>\n\n"
            "📅 <b>Birth date:</b> {birth_date}\n"
            "🌍 <b>Language:</b> {language_name}\n"
            "⏰ <b>Expected life expectancy:</b> {life_expectancy} years\n\n"
            "Select what you want to change:",
            "ua": "⚙️ <b>Налаштування профілю (Базова підписка)</b>\n\n"
            "📅 <b>Дата народження:</b> {birth_date}\n"
            "🌍 <b>Мова:</b> {language_name}\n"
            "⏰ <b>Очікувана тривалість життя:</b> {life_expectancy} років\n\n"
            "Оберіть, що хочете змінити:",
            "by": "⚙️ <b>Налады профілю (Базавая падпіска)</b>\n\n"
            "📅 <b>Дата нараджэння:</b> {birth_date}\n"
            "🌍 <b>Мова:</b> {language_name}\n"
            "⏰ <b>Чаканая працягласць жыцця:</b> {life_expectancy} гадоў\n\n"
            "Выберыце, што хочаце змяніць:",
        },
        "premium_settings": {
            "ru": "⚙️ <b>Настройки профиля (Премиум подписка)</b>\n\n"
            "📅 <b>Дата рождения:</b> {birth_date}\n"
            "🌍 <b>Язык:</b> {language_name}\n"
            "⏰ <b>Ожидаемая продолжительность жизни:</b> {life_expectancy} лет\n\n"
            "Выберите, что хотите изменить:",
            "en": "⚙️ <b>Profile Settings (Premium Subscription)</b>\n\n"
            "📅 <b>Birth date:</b> {birth_date}\n"
            "🌍 <b>Language:</b> {language_name}\n"
            "⏰ <b>Expected life expectancy:</b> {life_expectancy} years\n\n"
            "Select what you want to change:",
            "ua": "⚙️ <b>Налаштування профілю (Преміум підписка)</b>\n\n"
            "📅 <b>Дата народження:</b> {birth_date}\n"
            "🌍 <b>Мова:</b> {language_name}\n"
            "⏰ <b>Очікувана тривалість життя:</b> {life_expectancy} років\n\n"
            "Оберіть, що хочете змінити:",
            "by": "⚙️ <b>Налады профілю (Прэміум падпіска)</b>\n\n"
            "📅 <b>Дата нараджэння:</b> {birth_date}\n"
            "🌍 <b>Мова:</b> {language_name}\n"
            "⏰ <b>Чаканая працягласць жыцця:</b> {life_expectancy} гадоў\n\n"
            "Выберыце, што хочаце змяніць:",
        },
        "change_birth_date": {
            "ru": "📅 <b>Изменение даты рождения</b>\n\n"
            "Текущая дата: <b>{current_birth_date}</b>\n\n"
            "Введите новую дату рождения в формате ДД.ММ.ГГГГ\n"
            "Например: 15.03.1990\n\n"
            "Или нажмите /cancel для отмены",
            "en": "📅 <b>Change Birth Date</b>\n\n"
            "Current date: <b>{current_birth_date}</b>\n\n"
            "Enter new birth date in DD.MM.YYYY format\n"
            "For example: 15.03.1990\n\n"
            "Or press /cancel to cancel",
            "ua": "📅 <b>Зміна дати народження</b>\n\n"
            "Поточна дата: <b>{current_birth_date}</b>\n\n"
            "Введіть нову дату народження у форматі ДД.ММ.РРРР\n"
            "Наприклад: 15.03.1990\n\n"
            "Або натисніть /cancel для скасування",
            "by": "📅 <b>Змена даты нараджэння</b>\n\n"
            "Бягучая дата: <b>{current_birth_date}</b>\n\n"
            "Увядзіце новую дату нараджэння ў фармаце ДД.ММ.ГГГГ\n"
            "Напрыклад: 15.03.1990\n\n"
            "Або націсніце /cancel для адмены",
        },
        "change_language": {
            "ru": "🌍 <b>Изменение языка</b>\n\n"
            "Текущий язык: <b>{current_language}</b>\n\n"
            "Выберите новый язык:",
            "en": "🌍 <b>Change Language</b>\n\n"
            "Current language: <b>{current_language}</b>\n\n"
            "Select new language:",
            "ua": "🌍 <b>Зміна мови</b>\n\n"
            "Поточна мова: <b>{current_language}</b>\n\n"
            "Оберіть нову мову:",
            "by": "🌍 <b>Змена мовы</b>\n\n"
            "Бягучая мова: <b>{current_language}</b>\n\n"
            "Выберыце новую мову:",
        },
        "change_life_expectancy": {
            "ru": "⏰ <b>Изменение ожидаемой продолжительности жизни</b>\n\n"
            "Текущее значение: <b>{current_life_expectancy} лет</b>\n\n"
            "Введите новое значение (от 50 до 120 лет):",
            "en": "⏰ <b>Change Expected Life Expectancy</b>\n\n"
            "Current value: <b>{current_life_expectancy} years</b>\n\n"
            "Enter new value (from 50 to 120 years):",
            "ua": "⏰ <b>Зміна очікуваної тривалості життя</b>\n\n"
            "Поточне значення: <b>{current_life_expectancy} років</b>\n\n"
            "Введіть нове значення (від 50 до 120 років):",
            "by": "⏰ <b>Змена чаканай працягласці жыцця</b>\n\n"
            "Бягучае значэнне: <b>{current_life_expectancy} гадоў</b>\n\n"
            "Увядзіце новае значэнне (ад 50 да 120 гадоў):",
        },
        "birth_date_updated": {
            "ru": "✅ <b>Дата рождения успешно обновлена!</b>\n\n"
            "Новая дата: <b>{new_birth_date}</b>\n"
            "Новый возраст: <b>{new_age} лет</b>\n\n"
            "Используйте /weeks чтобы увидеть обновленную статистику",
            "en": "✅ <b>Birth date successfully updated!</b>\n\n"
            "New date: <b>{new_birth_date}</b>\n"
            "New age: <b>{new_age} years</b>\n\n"
            "Use /weeks to see updated statistics",
            "ua": "✅ <b>Дату народження успішно оновлено!</b>\n\n"
            "Нова дата: <b>{new_birth_date}</b>\n"
            "Новий вік: <b>{new_age} років</b>\n\n"
            "Використовуйте /weeks щоб побачити оновлену статистику",
            "by": "✅ <b>Дату нараджэння паспяхова абноўлена!</b>\n\n"
            "Новая дата: <b>{new_birth_date}</b>\n"
            "Новы ўзрост: <b>{new_age} гадоў</b>\n\n"
            "Выкарыстоўвайце /weeks каб убачыць абноўленую статыстыку",
        },
        "language_updated": {
            "ru": "✅ <b>Язык успешно изменен!</b>\n\n"
            "Новый язык: <b>{new_language}</b>\n\n"
            "Все сообщения бота теперь будут на выбранном языке",
            "en": "✅ <b>Language successfully changed!</b>\n\n"
            "New language: <b>{new_language}</b>\n\n"
            "All bot messages will now be in the selected language",
            "ua": "✅ <b>Мову успішно змінено!</b>\n\n"
            "Нова мова: <b>{new_language}</b>\n\n"
            "Всі повідомлення бота тепер будуть обраною мовою",
            "by": "✅ <b>Мову паспяхова зменена!</b>\n\n"
            "Новая мова: <b>{new_language}</b>\n\n"
            "Усе паведамленні бота цяпер будуць абранай мовай",
        },
        "life_expectancy_updated": {
            "ru": "✅ <b>Ожидаемая продолжительность жизни обновлена!</b>\n\n"
            "Новое значение: <b>{new_life_expectancy} лет</b>\n\n"
            "Используйте /weeks чтобы увидеть обновленную статистику",
            "en": "✅ <b>Expected life expectancy updated!</b>\n\n"
            "New value: <b>{new_life_expectancy} years</b>\n\n"
            "Use /weeks to see updated statistics",
            "ua": "✅ <b>Очікувану тривалість життя оновлено!</b>\n\n"
            "Нове значення: <b>{new_life_expectancy} років</b>\n\n"
            "Використовуйте /weeks щоб побачити оновлену статистику",
            "by": "✅ <b>Чаканую працягласць жыцця абноўлена!</b>\n\n"
            "Новае значэнне: <b>{new_life_expectancy} гадоў</b>\n\n"
            "Выкарыстоўвайце /weeks каб убачыць абноўленую статыстыку",
        },
        "invalid_life_expectancy": {
            "ru": "❌ <b>Неверное значение!</b>\n\n"
            "Ожидаемая продолжительность жизни должна быть от 50 до 120 лет.\n"
            "Попробуйте еще раз или нажмите /cancel для отмены",
            "en": "❌ <b>Invalid value!</b>\n\n"
            "Expected life expectancy should be from 50 to 120 years.\n"
            "Try again or press /cancel to cancel",
            "ua": "❌ <b>Невірне значення!</b>\n\n"
            "Очікувана тривалість життя повинна бути від 50 до 120 років.\n"
            "Спробуйте ще раз або натисніть /cancel для скасування",
            "by": "❌ <b>Няправільнае значэнне!</b>\n\n"
            "Чаканая працягласць жыцця павінна быць ад 50 да 120 гадоў.\n"
            "Паспрабуйце яшчэ раз або націсніце /cancel для адмены",
        },
        "settings_error": {
            "ru": "❌ Произошла ошибка при обновлении настроек.\n"
            "Попробуйте позже или обратитесь к администратору.",
            "en": "❌ An error occurred while updating settings.\n"
            "Please try again later or contact the administrator.",
            "ua": "❌ Сталася помилка при оновленні налаштувань.\n"
            "Спробуйте пізніше або зверніться до адміністратора.",
            "by": "❌ Адбылася памылка пры абнаўленні налад.\n"
            "Паспрабуйце пазней або звярніцеся да адміністратара.",
        },
        "button_change_birth_date": {
            "ru": "📅 Изменить дату рождения",
            "en": "📅 Change Birth Date",
            "ua": "📅 Змінити дату народження",
            "by": "📅 Змяніць дату нараджэння",
        },
        "button_change_language": {
            "ru": "🌍 Изменить язык",
            "en": "🌍 Change Language",
            "ua": "🌍 Змінити мову",
            "by": "🌍 Змяніць мову",
        },
        "button_change_life_expectancy": {
            "ru": "⏰ Изменить ожидаемую продолжительность жизни",
            "en": "⏰ Change Expected Life Expectancy",
            "ua": "⏰ Змінити очікувану тривалість життя",
            "by": "⏰ Змяніць чаканую працягласць жыцця",
        },
    },
    "subscription_additions": {
        "basic_addition": {
            "ru": "\n\n💡 <b>Базовая подписка</b>\n\n"
            "Вы используете базовую версию бота с основным функционалом.\n\n"
            "🔗 <b>Поддержите проект:</b>\n"
            "• GitHub: https://github.com/your-project/lifeweeks-bot\n"
            "• Донат: {buymeacoffee_url}\n\n"
            "Ваша поддержка помогает развивать бот! 🙏",
            "en": "\n\n💡 <b>Basic Subscription</b>\n\n"
            "You are using the basic version of the bot with core functionality.\n\n"
            "🔗 <b>Support the project:</b>\n"
            "• GitHub: https://github.com/your-project/lifeweeks-bot\n"
            "• Donate: {buymeacoffee_url}\n\n"
            "Your support helps develop the bot! 🙏",
            "ua": "\n\n💡 <b>Базова підписка</b>\n\n"
            "Ви використовуєте базову версію бота з основним функціоналом.\n\n"
            "🔗 <b>Підтримайте проект:</b>\n"
            "• GitHub: https://github.com/your-project/lifeweeks-bot\n"
            "• Донат: {buymeacoffee_url}\n\n"
            "Ваша підтримка допомагає розвивати бот! 🙏",
            "by": "\n\n💡 <b>Базавая падпіска</b>\n\n"
            "Вы выкарыстоўваеце базавую версію бота з асноўным функцыяналам.\n\n"
            "🔗 <b>Падтрымайте праект:</b>\n"
            "• GitHub: https://github.com/your-project/lifeweeks-bot\n"
            "• Донат: {buymeacoffee_url}\n\n"
            "Ваша падтрымка дапамагае развіваць бот! 🙏",
        },
        "premium_addition": {
            "ru": "\n\n✨ <b>Премиум контент</b>\n\n"
            "🧠 <b>Психология времени:</b>\n"
            "Исследования показывают, что визуализация времени помогает принимать более осознанные решения. "
            "Когда мы видим ограниченность наших недель, мы начинаем ценить каждую из них.\n\n"
            "📊 <b>Интересные факты:</b>\n"
            "• Средний человек тратит 26 лет на сон (около 1,352 недель)\n"
            "• 11 лет на работу (572 недели)\n"
            "• 5 лет на еду и готовку (260 недель)\n"
            "• 4 года на транспорт (208 недель)\n\n"
            "🎯 <b>Совет дня:</b> Попробуйте каждую неделю делать что-то новое - это поможет сделать жизнь более насыщенной и запоминающейся!",
            "en": "\n\n✨ <b>Premium Content</b>\n\n"
            "🧠 <b>Psychology of Time:</b>\n"
            "Research shows that time visualization helps make more conscious decisions. "
            "When we see the limitation of our weeks, we begin to value each one.\n\n"
            "📊 <b>Interesting Facts:</b>\n"
            "• Average person spends 26 years sleeping (about 1,352 weeks)\n"
            "• 11 years working (572 weeks)\n"
            "• 5 years eating and cooking (260 weeks)\n"
            "• 4 years commuting (208 weeks)\n\n"
            "🎯 <b>Daily Tip:</b> Try doing something new every week - it will help make life more fulfilling and memorable!",
            "ua": "\n\n✨ <b>Преміум контент</b>\n\n"
            "🧠 <b>Психологія часу:</b>\n"
            "Дослідження показують, що візуалізація часу допомагає приймати більш усвідомлені рішення. "
            "Коли ми бачимо обмеженість наших тижнів, ми починаємо цінувати кожен з них.\n\n"
            "📊 <b>Цікаві факти:</b>\n"
            "• Середня людина витрачає 26 років на сон (близько 1,352 тижнів)\n"
            "• 11 років на роботу (572 тижні)\n"
            "• 5 років на їжу та готування (260 тижнів)\n"
            "• 4 роки на транспорт (208 тижнів)\n\n"
            "🎯 <b>Порада дня:</b> Спробуйте кожного тижня робити щось нове - це допоможе зробити життя більш насиченим та запам'ятовуваним!",
            "by": "\n\n✨ <b>Прэміум кантэнт</b>\n\n"
            "🧠 <b>Псіхалогія часу:</b>\n"
            "Даследаванні паказваюць, што візуалізацыя часу дапамагае прымаць больш усвядомленыя рашэнні. "
            "Калі мы бачым абмежаванасць нашых тыдняў, мы пачынаем цаніць кожны з іх.\n\n"
            "📊 <b>Цікавыя факты:</b>\n"
            "• Сярэдні чалавек траціць 26 гадоў на сон (каля 1,352 тыдняў)\n"
            "• 11 гадоў на працу (572 тыдні)\n"
            "• 5 гадоў на ежу і гатаванне (260 тыдняў)\n"
            "• 4 гады на транспарт (208 тыдняў)\n\n"
            "🎯 <b>Парада дня:</b> Паспрабуйце кожны тыдзень рабіць нешта новае - гэта дапаможа зрабіць жыццё больш насычаным і запамінальным!",
        },
    },
}

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


def get_subscription_description(
    subscription_type: str,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Get subscription description by type.

    :param subscription_type: Subscription type (basic, premium, trial)
    :type subscription_type: str
    :param language: Language code (ru, en, ua, by)
    :type language: str
    :returns: Localized subscription description
    :rtype: str
    """
    if language not in LANGUAGES:
        language = DEFAULT_LANGUAGE

    try:
        return ALL_MESSAGES["command_subscription"]["subscription_descriptions"][
            subscription_type
        ][language]
    except KeyError:
        # Fallback to default language if translation is missing
        if language != DEFAULT_LANGUAGE:
            try:
                return ALL_MESSAGES["command_subscription"][
                    "subscription_descriptions"
                ][subscription_type][DEFAULT_LANGUAGE]
            except KeyError:
                return f"Unknown subscription: {subscription_type}"
        else:
            return f"Unknown subscription: {subscription_type}"
