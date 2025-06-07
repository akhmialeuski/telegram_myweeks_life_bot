"""Command handlers for the Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes
from ..core.life_tracker import get_weeks_lived, get_months_lived
from ..visualization.grid import generate_visualization
from ..utils.logger import get_logger

logger = get_logger("LifeWeeksBot")

async def weeks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /weeks command to display weeks and months lived.

    :param update: The update object containing the message.
    :type update: Update
    :param context: The context object for the command.
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: None
    """
    user_id = update.effective_user.id
    logger.info(f"Handling /weeks command from user {user_id}")
    weeks_lived = get_weeks_lived()
    months_lived = get_months_lived()
    await update.message.reply_text(
        f"You have lived {weeks_lived} weeks.\n\n"
        f"You have lived {months_lived} months."
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
        user_id = update.effective_user.id
        logger.info(f"Handling /visualize command from user {user_id}")
        img_byte_arr = generate_visualization()
        await update.message.reply_photo(
            photo=img_byte_arr,
            caption="Visual representation of your life in weeks.\n"
                   "🟩 Green cells: weeks lived\n"
                   "⬜ Empty cells: weeks to come"
        )
    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error(f"Error generating visualization: {error}")
        await update.message.reply_text(
            "Sorry, there was an error generating the visualization."
        )
