"""Common fixtures for test_database tests.

Provides shared fixtures for database-related tests including temporary
database paths, sample model objects, and mock repositories.
"""

import os
import tempfile
from collections.abc import Iterator
from datetime import UTC, date, datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.database.models.user import User
from src.database.models.user_settings import UserSettings
from src.database.models.user_subscription import UserSubscription
from src.database.repositories.sqlite.user_repository import SQLiteUserRepository
from src.database.repositories.sqlite.user_settings_repository import (
    SQLiteUserSettingsRepository,
)
from src.database.repositories.sqlite.user_subscription_repository import (
    SQLiteUserSubscriptionRepository,
)
from src.enums import SubscriptionType, WeekDay
from tests.conftest import (
    DEFAULT_LIFE_EXPECTANCY,
    DEFAULT_TIMEZONE,
    TEST_BIRTH_YEAR,
    TEST_FIRST_NAME,
    TEST_LAST_NAME,
    TEST_USER_ID,
    TEST_USERNAME,
)


@pytest.fixture
def temp_db_path() -> Iterator[str]:
    """Create a temporary database path for testing.

    Creates a temporary SQLite database file that is automatically
    cleaned up after the test completes.

    :returns: Path to temporary database file
    :rtype: Iterator[str]
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_user() -> User:
    """Create a sample User object for testing.

    :returns: Sample User object with test data
    :rtype: User
    """
    return User(
        telegram_id=TEST_USER_ID,
        username=TEST_USERNAME,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_settings() -> UserSettings:
    """Create a sample UserSettings object for testing.

    :returns: Sample UserSettings object with test data
    :rtype: UserSettings
    """
    return UserSettings(
        telegram_id=TEST_USER_ID,
        birth_date=date(TEST_BIRTH_YEAR, 1, 1),
        notifications_day=WeekDay.MONDAY,
        life_expectancy=DEFAULT_LIFE_EXPECTANCY,
        timezone=DEFAULT_TIMEZONE,
        notifications=True,
        notifications_time=time(9, 0),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_subscription() -> UserSubscription:
    """Create a sample UserSubscription object for testing.

    :returns: Sample UserSubscription object with test data
    :rtype: UserSubscription
    """
    return UserSubscription(
        telegram_id=TEST_USER_ID,
        subscription_type=SubscriptionType.PREMIUM,
        is_active=True,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )


@pytest.fixture
def mock_user_repository() -> MagicMock:
    """Create mock user repository with async methods.

    :returns: Mock user repository with AsyncMock methods
    :rtype: MagicMock
    """
    mock = MagicMock(spec=SQLiteUserRepository)
    mock.create_user = AsyncMock(return_value=True)
    mock.get_user = AsyncMock(return_value=None)
    mock.delete_user = AsyncMock(return_value=True)
    mock._get_all_entities = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_settings_repository() -> MagicMock:
    """Create mock settings repository with async methods.

    :returns: Mock settings repository with AsyncMock methods
    :rtype: MagicMock
    """
    mock = MagicMock(spec=SQLiteUserSettingsRepository)
    mock.create_user_settings = AsyncMock(return_value=True)
    mock.get_user_settings = AsyncMock(return_value=None)
    mock.update_user_settings = AsyncMock(return_value=True)
    mock.delete_user_settings = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_subscription_repository() -> MagicMock:
    """Create mock subscription repository with async methods.

    :returns: Mock subscription repository with AsyncMock methods
    :rtype: MagicMock
    """
    mock = MagicMock(spec=SQLiteUserSubscriptionRepository)
    mock.create_subscription = AsyncMock(return_value=True)
    mock.get_subscription = AsyncMock(return_value=None)
    mock.update_subscription = AsyncMock(return_value=True)
    mock.delete_subscription = AsyncMock(return_value=True)
    return mock
