# LifeWeeksBot

Telegram bot that tracks and visualizes the number of weeks lived since birth with multi-language support.

## Features

- 📅 Track weeks lived since birth with detailed statistics
- 📊 Visualize life progress as an interactive grid
- 🌍 Multi-language support (Russian, English, Ukrainian, Belarusian)
- ⚙️ Personal settings and preferences management
- 📢 Weekly notification system with customizable schedule
- 👥 Multi-user support with individual profiles
- 🎨 Beautiful visualizations with matplotlib and Pillow
- 🔒 Race condition prevention with proper locking mechanisms
- 🏗️ Modern architecture with dependency injection

## Requirements

- Python 3.12 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

## Installation

### 1. Clone the repository:
```bash
git clone <repository-url>
cd telegram_myweeks_life_bot
```

### 2. Set up virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies:
```bash
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

### 5. Set up the database:
```bash
python scripts/setup_database.py
```

## Database Setup

The project uses SQLAlchemy 2.0 with Alembic for database migrations and SQLite as the default database.

### Initial Setup

Run the setup script to create the database and apply migrations:

```bash
python scripts/setup_database.py
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

## Development

### Code Quality

This project enforces high code quality standards with automated checks:

```bash
# Fix code formatting and imports
./scripts/fix_code_style.sh

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html

# Check code style manually
black --check .
isort --check-only .
flake8 .
```

### Translation Management

For managing translations:

```bash
# Extract messages for translation
make extract

# Update translation files
make update

# Compile translation files
make compile
```

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

## Architecture

- **Bot Framework**: python-telegram-bot 20.7
- **Database**: SQLAlchemy 2.0 with SQLite
- **Visualization**: matplotlib + Pillow
- **Scheduling**: APScheduler for notifications
- **Internationalization**: Custom i18n system with Babel support
- **Testing**: pytest with async support and coverage reporting
- **Code Quality**: black, isort, flake8 with pre-commit hooks

## Project Structure

```
telegram_myweeks_life_bot/
├── src/                    # Main source code
│   ├── bot/               # Telegram bot implementation
│   ├── core/              # Core business logic
│   ├── database/          # Database models and repositories
│   ├── i18n.py           # Internationalization utilities
│   └── ...
├── tests/                 # Test suite
├── locales/               # Translation files
├── scripts/               # Utility scripts
├── docs/                  # Documentation
└── requirements*.txt       # Dependencies
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
