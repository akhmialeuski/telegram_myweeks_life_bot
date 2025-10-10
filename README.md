# LifeWeeksBot

**MyWeeksBot** is a public Telegram bot specifically designed for tracking the number of weeks lived and sending periodic notifications to users. The main function of the bot is to regularly send weekly messages displaying the exact number of weeks, months, and years lived. In addition to numerical data, the bot provides a visual representation in the form of a convenient table where lived weeks and remaining weeks are marked, allowing users to visually see the passage of time and better understand its flow.

This project helps users better understand the passage of time and motivates more conscious life planning. The bot supports multiple languages and can work with an unlimited number of users simultaneously.

## Features

- 📅 Track weeks lived since birth with detailed statistics
- 📊 Visualize life progress as an interactive grid
- 🌍 Multi-language support (Russian, English, Ukrainian, Belarusian)
- ⚙️ Personal settings and preferences management
- 📢 Weekly notification system with customizable schedule
- 👥 Multi-user support with individual profiles


## Requirements

- Python 3.12 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

## Installation

### 1. Clone the repository:
```bash
git clone https://github.com/akhmialeuski/telegram_myweeks_life_bot.git
cd telegram_myweeks_life_bot
```

### 2. Set up virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 4. Configure environment variables:
```bash
cp env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from BotFather
- `CHAT_ID` - Your Telegram user ID for notifications

## Database Setup

The project uses SQLAlchemy 2.0 with Alembic for database migrations and SQLite as the default database.

### Initial Setup

Run the setup script to create the database and apply migrations:

```bash
PYTHONPATH=. python scripts/setup_database.py
```

### Manual Migration Commands

If you need to manage migrations manually:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Rollback to previous migration
alembic downgrade -1

# Check current migration status
alembic current

# View migration history
alembic history
```

### Database Configuration

Database settings can be configured via environment variables:

- `DATABASE_URL` - Full database URL (overrides default SQLite)
- `DATABASE_PATH` - Path to SQLite database file (default: `lifeweeks.db`)

## Usage

### Start the bot:
```bash
python main.py
```

### In Telegram, use these commands:

- `/start` - Initialize the bot and register
- `/weeks` - Show detailed weeks lived statistics
- `/visualize` - Generate life progress visualization
- `/settings` - Configure personal preferences and language
- `/subscription` - Manage notification subscriptions
- `/help` - Show help information
- `/cancel` - Cancel current operation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

You can support this project at https://coff.ee/akhmelevskiy
