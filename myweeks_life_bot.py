"""Telegram bot that tracks and reports the number of weeks lived since birth.

This script implements a Telegram bot that:
- Calculates the number of weeks lived since a specified birth date
- Responds to /weeks command with the current count
- Sends weekly notifications on Mondays
- Provides monthly statistics
- Generates visual representation of weeks lived in a grid format
  - Each cell represents one week
  - Each row represents one year (52 weeks)
  - Green cells show weeks lived
  - Empty cells show weeks to come
  - Years and weeks are labeled on axes
  - Includes a legend for easy interpretation

:requires: Environment variables:
    - TELEGRAM_BOT_TOKEN: The Telegram bot API token
    - DATE_OF_BIRTH: Birth date in YYYY-MM-DD format
    - CHAT_ID: The Telegram chat ID for notifications

:example: To run the bot, ensure all environment variables are set in .env file and execute:
    python myweeks_life_bot.py

:note: This version is compatible with Python 3.13 and python-telegram-bot v20+ (async API).
"""

import os
import datetime
import asyncio
from typing import NoReturn, Tuple
from io import BytesIO
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from PIL import Image, ImageDraw, ImageFont

# Load environment variables
load_dotenv()
TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
DATE_OF_BIRTH: str = os.getenv("DATE_OF_BIRTH")  # Format: YYYY-MM-DD
CHAT_ID: str = os.getenv("CHAT_ID")  # User's Telegram ID

# Constants for visualization
CELL_SIZE = 10
PADDING = 40
FONT_SIZE = 12
MAX_YEARS = 90
WEEKS_PER_YEAR = 52

# Colors
COLORS = {
    'background': (255, 255, 255),  # White
    'grid': (200, 200, 200),        # Light gray
    'lived': (76, 175, 80),         # Green
    'text': (0, 0, 0),              # Black
    'axis': (100, 100, 100),        # Dark gray
}


def get_weeks_lived() -> int:
    """Calculate the number of weeks lived since birth date.

    :returns: The number of complete weeks lived since birth date.
    :rtype: int
    :note: Uses the DATE_OF_BIRTH environment variable for calculation.
    """
    birth_date = datetime.datetime.strptime(DATE_OF_BIRTH, "%Y-%m-%d").date()
    today = datetime.date.today()
    return (today - birth_date).days // 7


def calculate_grid_dimensions() -> Tuple[int, int]:
    """Calculate the dimensions of the visualization grid.

    :returns: Tuple of (width, height) in pixels.
    :rtype: Tuple[int, int]
    """
    width = (WEEKS_PER_YEAR * CELL_SIZE) + (2 * PADDING)
    height = (MAX_YEARS * CELL_SIZE) + (2 * PADDING)
    return width, height


def generate_visualization() -> BytesIO:
    """Generate a visual representation of weeks lived.

    Creates a grid where:
    - Each cell represents one week
    - Each row represents one year (52 weeks)
    - Green cells represent weeks lived
    - Empty cells represent weeks not yet lived
    - Years are labeled on the vertical axis
    - Weeks are labeled on the horizontal axis (every 4th week)
    - A legend is included at the bottom

    :returns: BytesIO object containing the generated image.
    :rtype: BytesIO
    """
    width, height = calculate_grid_dimensions()
    image = Image.new('RGB', (width, height), COLORS['background'])
    draw = ImageDraw.Draw(image)

    # Draw grid and cells
    weeks_lived = get_weeks_lived()
    current_week = 0

    # Prepare font (use default to avoid missing font issues)
    try:
        font = ImageFont.truetype("arial.ttf", FONT_SIZE)
    except OSError:
        font = ImageFont.load_default()

    # Draw vertical axis (years)
    for year in range(MAX_YEARS):
        y = PADDING + (year * CELL_SIZE)
        draw.text((5, y), str(year), fill=COLORS['axis'], font=font)

    # Draw horizontal axis (weeks)
    for week in range(0, WEEKS_PER_YEAR, 4):  # Label every 4th week
        x = PADDING + (week * CELL_SIZE)
        draw.text((x, 5), str(week + 1), fill=COLORS['axis'], font=font)

    # Draw cells (one row per year, 52 cells per row)
    for year in range(MAX_YEARS):
        for week in range(WEEKS_PER_YEAR):
            x = PADDING + (week * CELL_SIZE)
            y = PADDING + (year * CELL_SIZE)
            # Draw cell border
            draw.rectangle([x, y, x + CELL_SIZE - 1, y + CELL_SIZE - 1], outline=COLORS['grid'])
            # Fill cell if week has been lived
            if current_week < weeks_lived:
                draw.rectangle([x + 1, y + 1, x + CELL_SIZE - 2, y + CELL_SIZE - 2], fill=COLORS['lived'])
            current_week += 1

    # Add legend
    legend_y = height - PADDING + 10
    draw.rectangle([PADDING, legend_y, PADDING + 20, legend_y + 20], fill=COLORS['lived'])
    draw.text((PADDING + 30, legend_y), "Weeks Lived", fill=COLORS['text'], font=font)

    # Save to BytesIO
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


async def weeks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /weeks command to display weeks and months lived.

    :param update: The update object containing the message.
    :type update: Update
    :param context: The context object for the command.
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: None
    :note: Responds with both weeks and months lived since birth date.
    """
    weeks_lived = get_weeks_lived()
    print("Weeks lived:", weeks_lived)
    await update.message.reply_text(f"You have lived {weeks_lived} weeks."
                                    f"\n\nYou have lived month: {weeks_lived // 4} months.")


async def visualize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /visualize command to show a visual representation of weeks lived.

    :param update: The update object containing the message.
    :type update: Update
    :param context: The context object for the command.
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: None
    :note: Sends an image showing a grid representation of weeks lived, with each row representing one year (52 weeks).
    """
    try:
        img_byte_arr = generate_visualization()
        await update.message.reply_photo(
            photo=img_byte_arr,
            caption="Visual representation of your life in weeks.\n"
                   "🟩 Green cells: weeks lived\n"
                   "⬜ Empty cells: weeks to come"
        )
    except Exception as e:
        print(f"Error generating visualization: {e}")
        await update.message.reply_text("Sorry, there was an error generating the visualization.")


async def send_weekly_message(application: Application) -> None:
    """Send a weekly notification message about the current week of life.

    :param application: The running Application instance.
    :type application: Application
    :returns: None
    :note: Uses the global TOKEN and CHAT_ID variables for authentication. This function is scheduled by APScheduler and runs in the bot's event loop.
    :raises telegram.error.TelegramError: If the message cannot be sent.
    """
    weeks_lived = get_weeks_lived()
    await application.bot.send_message(chat_id=CHAT_ID, text=f"The {weeks_lived}th week of your life has begun.")


def main() -> None:
    """Initialize and run the Telegram bot with scheduled tasks.

    This function:
    1. Builds the Telegram bot application
    2. Sets up command handlers
    3. Registers an async post-init callback to start the scheduler after the event loop is running
    4. Configures the scheduler for weekly messages
    5. Starts the bot in polling mode

    :returns: None
    :rtype: None
    :note: The scheduler is started in an async post-init callback to ensure it runs in the correct event loop context (required for Python 3.13 and PTB v20+).
    :raises RuntimeError: If the bot cannot be started or if the scheduler fails to start.
    """
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("weeks", weeks))
    app.add_handler(CommandHandler("visualize", visualize))

    async def on_startup(app: Application) -> None:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(lambda: asyncio.create_task(send_weekly_message(app)), "cron", day_of_week="mon", hour=9, minute=0)
        scheduler.start()

    app.post_init = on_startup

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
