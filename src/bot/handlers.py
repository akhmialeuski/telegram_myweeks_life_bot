"""Command handlers for the Telegram bot."""

from datetime import date, datetime

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ..database import SQLAlchemyUserRepository, User, UserSettings
from ..database.constants import (
    DEFAULT_NOTIFICATIONS_DAY,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DEFAULT_NOTIFICATIONS_TIME,
    DEFAULT_TIMEZONE,
)
from ..utils.logger import get_logger
from ..visualization.grid import generate_visualization

logger = get_logger("LifeWeeksBot")

# Conversation states
WAITING_BIRTH_DATE = 1

# Global repository instance
repository = SQLAlchemyUserRepository()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command - ask for birth date and register user.

    :param update: The update object containing the message.
    :param context: The context object for the command.
    :returns: Conversation state
    """
    user = update.effective_user

    logger.info(f"User {user.id} ({user.username}) started the bot")

    # Check if user already exists
    existing_user = repository.get_user(user.id)
    if existing_user:
        await update.message.reply_text(
            f"👋 Привет, {user.first_name}! Ты уже зарегистрирован.\n\n"
            f"Используй /weeks чтобы посмотреть свои недели жизни.\n"
            f"Используй /help для справки."
        )
        return ConversationHandler.END

    # Ask for birth date
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}! Добро пожаловать в LifeWeeksBot!\n\n"
        f"Этот бот поможет тебе отслеживать недели твоей жизни.\n\n"
        f"📅 Пожалуйста, введи свою дату рождения в формате ДД.ММ.ГГГГ\n"
        f"Например: 15.03.1990"
    )

    return WAITING_BIRTH_DATE


async def handle_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle birth date input from user.

    :param update: The update object containing the message.
    :param context: The context object for the command.
    :returns: Conversation state
    """
    user = update.effective_user
    birth_date_text = update.message.text.strip()

    try:
        # Parse birth date
        birth_date = datetime.strptime(birth_date_text, "%d.%m.%Y").date()

        # Validate birth date (not in future, reasonable past)
        today = date.today()
        if birth_date > today:
            await update.message.reply_text(
                "❌ Дата рождения не может быть в будущем!\n"
                "Пожалуйста, введи корректную дату в формате ДД.ММ.ГГГГ"
            )
            return WAITING_BIRTH_DATE

        if birth_date.year < 1900:
            await update.message.reply_text(
                "❌ Дата рождения слишком старая!\n"
                "Пожалуйста, введи корректную дату в формате ДД.ММ.ГГГГ"
            )
            return WAITING_BIRTH_DATE

        # Parse default notifications time
        notifications_time = datetime.strptime(
            DEFAULT_NOTIFICATIONS_TIME, "%H:%M:%S"
        ).time()

        # Create user and settings
        new_user = User(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            created_at=datetime.utcnow(),
        )

        new_settings = UserSettings(
            telegram_id=user.id,
            birth_date=birth_date,
            notifications=DEFAULT_NOTIFICATIONS_ENABLED,
            timezone=DEFAULT_TIMEZONE,
            notifications_day=DEFAULT_NOTIFICATIONS_DAY,
            notifications_time=notifications_time,
            updated_at=datetime.utcnow(),
        )

        # Save to database
        if repository.create_user_profile(new_user, new_settings):
            # Calculate weeks lived
            weeks_lived = calculate_weeks_lived(birth_date)

            await update.message.reply_text(
                f"✅ Отлично! Ты успешно зарегистрирован!\n\n"
                f"📅 Дата рождения: {birth_date.strftime('%d.%m.%Y')}\n"
                f"📊 Недель прожито: {weeks_lived:,}\n\n"
                f"Теперь ты можешь использовать команды:\n"
                f"• /weeks - показать недели жизни\n"
                f"• /help - справка"
            )

            logger.info(f"User {user.id} registered with birth date {birth_date}")
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "❌ Произошла ошибка при сохранении данных.\n"
                "Попробуй еще раз или обратись к администратору."
            )
            return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты!\n"
            "Пожалуйста, введи дату в формате ДД.ММ.ГГГГ\n"
            "Например: 15.03.1990"
        )
        return WAITING_BIRTH_DATE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command to cancel registration.

    :param update: The update object containing the message.
    :param context: The context object for the command.
    :returns: Conversation state
    """
    await update.message.reply_text(
        "❌ Регистрация отменена.\n" "Используй /start чтобы начать заново."
    )
    return ConversationHandler.END


async def weeks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /weeks command to display weeks and months lived.

    :param update: The update object containing the message.
    :type update: Update
    :param context: The context object for the command.
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: None
    """
    user = update.effective_user
    user_id = user.id

    logger.info(f"Handling /weeks command from user {user_id}")

    # Get user profile from database
    user_profile = repository.get_user_profile(user_id)
    if not user_profile or not user_profile.settings.birth_date:
        await update.message.reply_text(
            "❌ Ты еще не зарегистрирован!\n"
            "Используй /start чтобы зарегистрироваться."
        )
        return

    # Calculate weeks from user's birth date
    birth_date = user_profile.settings.birth_date
    weeks_lived = calculate_weeks_lived(birth_date)
    age = calculate_age(birth_date)

    await update.message.reply_text(
        f"📊 Твои недели жизни:\n\n"
        f"📅 Дата рождения: {birth_date.strftime('%d.%m.%Y')}\n"
        f"📈 Недель прожито: {weeks_lived:,}\n"
        f"🎯 Недель в году: 52\n"
        f"📅 Возраст: {age} лет"
    )


async def visualize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /visualize command to show a visual representation of weeks lived.

    :param update: The update object containing the message.
    :type update: Update
    :param context: The context object for the command.
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: None
    """
    try:
        user = update.effective_user
        user_id = user.id

        logger.info(f"Handling /visualize command from user {user_id}")

        # Check if user is registered
        user_profile = repository.get_user_profile(user_id)
        if not user_profile or not user_profile.settings.birth_date:
            await update.message.reply_text(
                "❌ Ты еще не зарегистрирован!\n"
                "Используй /start чтобы зарегистрироваться."
            )
            return

        birth_date_str = user_profile.settings.birth_date.strftime("%Y-%m-%d")
        img_byte_arr = generate_visualization(birth_date_str)
        await update.message.reply_photo(
            photo=img_byte_arr,
            caption="Visual representation of your life in weeks.\n"
            "🟩 Green cells: weeks lived\n"
            "⬜ Empty cells: weeks to come",
        )
    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error(f"Error generating visualization: {error}")
        await update.message.reply_text(
            "Sorry, there was an error generating the visualization."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command - show help information.

    :param update: The update object containing the message.
    :param context: The context object for the command.
    :returns: None
    """
    help_text = (
        "🤖 LifeWeeksBot - Помогает отслеживать недели твоей жизни\n\n"
        "📋 Доступные команды:\n"
        "• /start - Регистрация и настройка\n"
        "• /weeks - Показать недели жизни\n"
        "• /visualize - Визуализация недель жизни\n"
        "• /help - Эта справка\n\n"
        "💡 Интересные факты:\n"
        "• В году 52 недели\n"
        "• Средняя продолжительность жизни: 80 лет\n"
        "• Это примерно 4,160 недель\n\n"
        "🎯 Цель бота - помочь тебе осознать ценность времени!"
    )

    await update.message.reply_text(help_text)


def calculate_weeks_lived(birth_date: date) -> int:
    """Calculate weeks lived since birth date.

    :param birth_date: User's birth date
    :returns: Number of weeks lived
    """
    today = date.today()
    days_lived = (today - birth_date).days
    return days_lived // 7


def calculate_age(birth_date: date) -> int:
    """Calculate age in years.

    :param birth_date: User's birth date
    :returns: Age in years
    """
    today = date.today()
    age = today.year - birth_date.year
    if today.month < birth_date.month or (
        today.month == birth_date.month and today.day < birth_date.day
    ):
        age -= 1
    return age
