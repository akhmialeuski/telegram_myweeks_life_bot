# Life Weeks Bot

Telegram bot for tracking and visualizing your life in weeks. This bot helps you understand how many weeks of your life have passed and how many are left, providing a unique perspective on time management and life planning.

## Features

- Track your life weeks with `/weeks` command
- Visualize your life progress with `/visualize` command
- Clean and intuitive interface
- Detailed logging system
- Configurable through environment variables

## Installation

1. Clone the repository:
```bash
git clone https://github.com/akhmialeuski/telegram_myweeks_life_bot.git
cd telegram_myweeks_life_bot
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your configuration:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATE_OF_BIRTH=YYYY-MM-DD
CHAT_ID=your_chat_id
```

## Usage

1. Start the bot:
```bash
python main.py
```

2. Available commands:
   - `/weeks` - Show how many weeks of your life have passed
   - `/visualize` - Generate a visualization of your life weeks

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from @BotFather | Yes |
| `DATE_OF_BIRTH` | Your birth date in YYYY-MM-DD format | Yes |
| `CHAT_ID` | Your Telegram chat ID for notifications | Yes |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
