"""Integration test fixtures with real test database.

This module provides shared fixtures for integration tests using a real
SQLite test database file. Tests use actual handlers and services with
only Telegram API calls mocked.
"""

from collections.abc import AsyncIterator, Iterator
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import text
from telegram import Chat, Message, Update, User

from src.database.repositories.sqlite.base_repository import BaseSQLiteRepository
from src.database.service import DatabaseManager
from src.enums import SubscriptionType, SupportedLanguage
from src.services.container import ServiceContainer

# =============================================================================
# Test Constants
# =============================================================================

TEST_USER_ID: int = 123456789
TEST_CHAT_ID: int = 123456789
TEST_USERNAME: str = "test_integration_user"
TEST_FIRST_NAME: str = "Integration"
TEST_LAST_NAME: str = "Tester"
TEST_LANGUAGE_CODE: str = SupportedLanguage.EN.value
TEST_DB_FILENAME: str = "test_integration.db"


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture(scope="function")
def test_db_path(tmp_path: Path) -> Iterator[str]:
    """Create a temporary test database path for each test.

    Each test gets its own unique database file to ensure isolation.
    The database file is created in a temporary directory and is
    automatically cleaned up after the test completes.

    :param tmp_path: Pytest temporary directory fixture
    :type tmp_path: Path
    :returns: Path to the test database file
    :rtype: Iterator[str]
    """
    db_path = str(tmp_path / TEST_DB_FILENAME)
    yield db_path
    # Cleanup is automatic when temp directory is removed


@pytest_asyncio.fixture
async def test_service_container(
    test_db_path: str,
) -> AsyncIterator[ServiceContainer]:
    """Create a ServiceContainer configured for testing.

    This fixture creates a fresh ServiceContainer instance with:
    - Real database connection to test database
    - Telegram gateway disabled (None)
    - All other services initialized normally

    The database is initialized before the test and cleaned up after.

    :param test_db_path: Path to the test database file
    :type test_db_path: str
    :returns: ServiceContainer instance for testing
    :rtype: AsyncIterator[ServiceContainer]
    """
    # Reset any existing singleton state
    BaseSQLiteRepository.reset_instances()
    DatabaseManager.reset_instance()

    # Create test container
    container = ServiceContainer.create_for_testing(db_path=test_db_path)

    # Initialize database
    await container.user_service.initialize()

    yield container

    # Cleanup: close database connections
    await container.user_service.close()

    # Reset singleton state for next test
    BaseSQLiteRepository.reset_instances()
    DatabaseManager.reset_instance()


# =============================================================================
# Telegram Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_telegram_user() -> MagicMock:
    """Create a mock Telegram User object.

    :returns: Mock User object with test user attributes
    :rtype: MagicMock
    """
    user = MagicMock(spec=User)
    user.id = TEST_USER_ID
    user.username = TEST_USERNAME
    user.first_name = TEST_FIRST_NAME
    user.last_name = TEST_LAST_NAME
    user.language_code = TEST_LANGUAGE_CODE
    user.is_bot = False
    return user


@pytest.fixture
def mock_chat() -> MagicMock:
    """Create a mock Telegram Chat object.

    :returns: Mock Chat object
    :rtype: MagicMock
    """
    chat = MagicMock(spec=Chat)
    chat.id = TEST_CHAT_ID
    chat.type = "private"
    return chat


@pytest.fixture
def mock_message(
    mock_telegram_user: MagicMock,
    mock_chat: MagicMock,
) -> MagicMock:
    """Create a mock Telegram Message object with reply methods.

    The message has AsyncMock reply methods that capture sent responses
    for assertion in tests.

    :param mock_telegram_user: Mock user object
    :type mock_telegram_user: MagicMock
    :param mock_chat: Mock chat object
    :type mock_chat: MagicMock
    :returns: Mock Message object
    :rtype: MagicMock
    """
    message = MagicMock(spec=Message)
    message.from_user = mock_telegram_user
    message.chat = mock_chat
    message.message_id = 1
    message.text = ""

    # Capture replies for assertions
    message.reply_text = AsyncMock(return_value=MagicMock())
    message.reply_photo = AsyncMock(return_value=MagicMock())

    return message


@pytest.fixture
def mock_update(
    mock_telegram_user: MagicMock,
    mock_chat: MagicMock,
    mock_message: MagicMock,
) -> MagicMock:
    """Create a mock Telegram Update object.

    :param mock_telegram_user: Mock user object
    :type mock_telegram_user: MagicMock
    :param mock_chat: Mock chat object
    :type mock_chat: MagicMock
    :param mock_message: Mock message object
    :type mock_message: MagicMock
    :returns: Mock Update object
    :rtype: MagicMock
    """
    update = MagicMock(spec=Update)
    update.update_id = 1
    update.message = mock_message
    update.callback_query = None
    update.effective_user = mock_telegram_user
    update.effective_chat = mock_chat
    return update


@pytest.fixture
def mock_context() -> MagicMock:
    """Create a mock Telegram Context object.

    :returns: Mock Context object with user_data storage
    :rtype: MagicMock
    """
    context = MagicMock()
    context.user_data = {}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context


# =============================================================================
# Helper Fixtures
# =============================================================================


def set_message_text(mock_update: MagicMock, text: str) -> None:
    """Set the text of the message in a mock update.

    :param mock_update: Mock update object
    :type mock_update: MagicMock
    :param text: Text to set
    :type text: str
    :returns: None
    """
    mock_update.message.text = text


def get_reply_text(mock_message: MagicMock) -> str | None:
    """Get the text from the last reply_text or reply_photo call.

    :param mock_message: Mock message object
    :type mock_message: MagicMock
    :returns: Reply text or caption (for photo) or None if no reply was made
    :rtype: str | None
    """
    if mock_message.reply_text.called:
        call_args = mock_message.reply_text.call_args
        if call_args and call_args.args:
            return call_args.args[0]
        if call_args and call_args.kwargs.get("text"):
            return call_args.kwargs["text"]

    if mock_message.reply_photo.called:
        call_args = mock_message.reply_photo.call_args
        if call_args and call_args.kwargs.get("caption"):
            return call_args.kwargs["caption"]

    return None


def get_reply_markup(mock_message: MagicMock) -> Any | None:
    """Get the reply_markup from the last reply_text call.

    :param mock_message: Mock message object
    :type mock_message: MagicMock
    :returns: Reply markup or None
    :rtype: Any | None
    """
    if mock_message.reply_text.called:
        call_args = mock_message.reply_text.call_args
        if call_args and call_args.kwargs.get("reply_markup"):
            return call_args.kwargs["reply_markup"]
    return None


# =============================================================================
# User Setup Helpers (for settings tests)
# =============================================================================


async def make_registered_user(
    container: ServiceContainer,
    user_info: Any,
    birth_date: date | None = None,
) -> None:
    """Create a registered user with basic subscription.

    :param container: Service container with database connection
    :type container: ServiceContainer
    :param user_info: Mock or real Telegram User object (must have .id)
    :type user_info: Any
    :param birth_date: Birth date for the user (default: 1990-01-01)
    :type birth_date: date | None
    :returns: None
    :rtype: None
    """
    await container.user_service.create_user_profile(
        user_info=user_info,
        birth_date=birth_date or date(1990, 1, 1),
    )


async def make_premium_user(
    container: ServiceContainer,
    user_info: Any,
    birth_date: date | None = None,
    telegram_id: int | None = None,
) -> None:
    """Create a registered user with Premium subscription.

    :param container: Service container with database connection
    :type container: ServiceContainer
    :param user_info: Mock or real Telegram User object (must have .id)
    :type user_info: Any
    :param birth_date: Birth date for the user (default: 1990-01-01)
    :type birth_date: date | None
    :param telegram_id: Telegram ID to upgrade (default: user_info.id)
    :type telegram_id: int | None
    :returns: None
    :rtype: None
    """
    await make_registered_user(container, user_info, birth_date)
    tid = telegram_id if telegram_id is not None else user_info.id
    await container.user_service.update_user_subscription(
        telegram_id=tid,
        subscription_type=SubscriptionType.PREMIUM,
    )


def setup_notification_schedule_callback(mock_update: MagicMock) -> None:
    """Configure mock_update for notification schedule callback flow.

    :param mock_update: Mock Telegram Update object
    :type mock_update: MagicMock
    :returns: None
    :rtype: None
    """
    mock_update.callback_query = MagicMock()
    mock_update.callback_query.data = "settings_notification_schedule"
    mock_update.callback_query.edit_message_text = AsyncMock()
    mock_update.callback_query.answer = AsyncMock()


async def create_user_with_invalid_enum_value(
    container: ServiceContainer,
    telegram_id: int = TEST_USER_ID,
) -> None:
    """Create a user with an invalid (lowercase) enum value in the database.

    This helper is used to reproduce bugs where database values (lowercase)
    mismatch with Python Enum definitions (uppercase), causing validation errors.
    It uses raw SQL to bypass SQLAlchemy validation.

    :param container: Service container with database connection
    :type container: ServiceContainer
    :param telegram_id: Telegram ID of the user to create
    :type telegram_id: int
    :returns: None
    """
    user_service = container.user_service

    # 1. Create a valid user profile first (this creates user, settings, and subscription)
    # create_user_profile expects a user_info object (telegram.User)
    user_info = User(
        id=telegram_id,
        username=TEST_USERNAME,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        is_bot=False,
    )
    await user_service.create_user_profile(
        user_info=user_info,
        birth_date=date(year=1990, month=1, day=1),
    )

    # 2. Now use raw SQL to UPDATE the settings with an "invalid" enum value
    # This bypasses SQLAlchemy validation for the update but will trigger it on subsequent loads
    repo = user_service.user_repository
    async with repo.async_session() as session:
        await session.execute(
            text(
                "UPDATE user_settings SET notification_frequency = :freq "
                "WHERE telegram_id = :tid"
            ),
            {
                "tid": telegram_id,
                "freq": "weekly",  # Lowercase string causing the mismatch vs Enum.WEEKLY
            },
        )
