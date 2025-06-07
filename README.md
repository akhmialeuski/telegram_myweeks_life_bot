# MyWeeks Life Bot

A Telegram bot that tracks and visualizes the number of weeks lived since a specified birth date.

## Features

- Calculates and reports the number of weeks lived since birth
- Sends weekly notifications on Mondays
- Provides monthly statistics
- Generates a visual representation of weeks lived in a grid format
  - Each cell represents one week
  - Each row represents one year (52 weeks)
  - Green cells show weeks lived
  - Empty cells show weeks to come
  - Years and weeks are labeled on axes
  - Includes a legend for easy interpretation

## Prerequisites

- Python 3.13 or higher
- A Telegram bot token (obtain from [@BotFather](https://t.me/botfather))
- Your birth date
- Your Telegram chat ID

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python3.12 -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Create a `.env` file in the project root with the following variables:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   DATE_OF_BIRTH=YYYY-MM-DD
   CHAT_ID=your_telegram_chat_id
   ```

## Usage

1. Start the bot:
   ```bash
   python myweeks_life_bot.py
   ```
2. Available commands:
   - `/weeks` - Display the current number of weeks and months lived
   - `/visualize` - Generate and send a visual representation of weeks lived

## Technical Notes

- Uses `python-telegram-bot` v20+ with async API
- Implements APScheduler for weekly notifications
- Uses Pillow for image generation
- The visualization grid shows up to 90 years of life
- Each row represents one year (52 weeks)
- The grid includes labeled axes and a legend for easy interpretation

## Visualization Details

The visualization is generated as a grid where:
- Each cell represents one week of life
- Each row represents one year (52 weeks)
- Green cells (🟩) indicate weeks that have been lived
- Empty cells (⬜) represent weeks that are yet to come
- The vertical axis shows years (0-90)
- The horizontal axis shows weeks (1-52)
- A legend is included at the bottom of the image
- The grid is designed to be easily readable on mobile devices

## License

This project is licensed under the MIT License - see the LICENSE file for details.