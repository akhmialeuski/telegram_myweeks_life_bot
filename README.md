# LifeWeeksBot

Telegram bot that tracks and visualizes the number of weeks lived since birth.

## Features

- Track weeks lived since birth
- Visualize life progress
- Set birth date and preferences
- Weekly notifications
- Multi-user support

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd telegram_myweeks_life_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Set up the database:
```bash
python scripts/setup_database.py
```

## Database Setup

The project uses SQLAlchemy 2.0 with Alembic for database migrations.

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

## Usage

1. Start the bot:
```bash
python src/main.py
```

2. In Telegram, send `/start` to begin using the bot

## Commands

- `/start` - Start the bot
- `/weeks` - Show weeks lived
- `/visualize` - Show life visualization
- `/setbirthdate` - Set your birth date
- `/help` - Show help information

## Architecture

### Dependency Injection Container

The project uses a Dependency Injection (DI) container to manage all application dependencies. This approach:

- **Reduces coupling** between modules
- **Simplifies testing** by allowing easy service substitution
- **Centralizes dependency management** in one place
- **Enables easy configuration changes** without modifying multiple files

#### Key Components

- **ServiceContainer** (`src/services/container.py`): Main container that creates and manages all services
- **FakeServiceContainer** (`tests/utils/fake_container.py`): Mock container for testing
- **Handler Dependencies**: All handlers receive services through their constructor

#### Usage

```python
# Creating handlers with DI
services = ServiceContainer()
handler = StartHandler(services)

# In tests
fake_services = FakeServiceContainer()
handler = StartHandler(fake_services)
```

#### Services Managed by Container

- `user_service`: User management and database operations
- `life_calculator`: Life statistics calculations
- `localization_service`: Message localization and formatting

## Project Structure

```
├── src/
│   ├── services/           # Dependency injection container
│   │   ├── container.py    # ServiceContainer implementation
│   │   └── __init__.py
│   ├── database/           # Database layer
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── constants.py    # Database constants
│   │   ├── abstract_repository.py  # Repository interface
│   │   └── sqlite_repository.py    # SQLite implementation
│   ├── visualization/      # Visualization module
│   └── main.py            # Main application
├── alembic/               # Database migrations
│   ├── versions/          # Migration files
│   ├── env.py            # Alembic environment
│   └── script.py.mako    # Migration template
├── scripts/              # Utility scripts
│   └── setup_database.py # Database setup script
├── requirements.txt      # Python dependencies
├── alembic.ini          # Alembic configuration
└── README.md           # This file
```

## Development

### Adding New Migrations

When you modify the database models:

1. Update the models in `src/database/models.py`
2. Generate a new migration:
   ```bash
   alembic revision --autogenerate -m "Add new feature"
   ```
3. Review the generated migration file
4. Apply the migration:
   ```bash
   alembic upgrade head
   ```

### Database Schema

The database contains two main tables:

- `users` - User information (Telegram ID, username, etc.)
- `user_settings` - User preferences and settings (birth date, notifications, etc.)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
