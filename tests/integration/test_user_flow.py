"""Integration tests for user flow with real database.

Tests the full user lifecycle using SQLite.
"""

import os
import tempfile
from collections.abc import Iterator
from datetime import date
from unittest.mock import MagicMock

import pytest

from src.database.repositories.sqlite.user_repository import SQLiteUserRepository
from src.database.repositories.sqlite.user_settings_repository import (
    SQLiteUserSettingsRepository,
)
from src.database.repositories.sqlite.user_subscription_repository import (
    SQLiteUserSubscriptionRepository,
)
from src.database.service import UserService


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


@pytest.mark.asyncio
class TestUserIntegration:
    """Integration tests for user flows with real database."""

    async def test_full_user_lifecycle(self, temp_db_path: str) -> None:
        """Test complete user lifecycle: create, retrieve, update, delete.

        Verifies that all components (Repositories, Service, DB) work together correctly.

        :param temp_db_path: Path to temporary SQLite database
        :type temp_db_path: str
        """
        # 1. Setup Repositories pointing to temp DB
        user_repo = SQLiteUserRepository(db_path=temp_db_path)
        settings_repo = SQLiteUserSettingsRepository(db_path=temp_db_path)
        sub_repo = SQLiteUserSubscriptionRepository(db_path=temp_db_path)

        # Initialize DB (creates tables) - must initialize all repositories to bind sessions
        await user_repo.initialize()
        await settings_repo.initialize()
        await sub_repo.initialize()

        # 2. Setup UserService
        user_service = UserService(
            user_repository=user_repo,
            settings_repository=settings_repo,
            subscription_repository=sub_repo,
        )

        try:
            # 3. Create User
            telegram_user = MagicMock()
            telegram_user.id = 12345
            telegram_user.username = "test_user_integ"
            telegram_user.first_name = "Test"
            telegram_user.last_name = "Integartion"

            birth_date = date(1990, 1, 1)

            profile = await user_service.create_user_profile(
                user_info=telegram_user,
                birth_date=birth_date,
            )

            assert profile is not None
            assert profile.telegram_id == 12345
            assert profile.settings.birth_date == birth_date

            # 4. Verify Persistence (Fetch again)
            fetched_profile = await user_service.get_user_profile(12345)
            assert fetched_profile is not None
            assert fetched_profile.username == "test_user_integ"

            # 5. Update Settings
            new_birth_date = date(1995, 5, 5)
            await user_service.update_user_settings(
                telegram_id=12345,
                birth_date=new_birth_date,
            )

            updated_profile = await user_service.get_user_profile(12345)
            assert updated_profile.settings.birth_date == new_birth_date

            # 6. Delete User Profile
            await user_service.delete_user_profile(12345)

            # 7. Verify Deletion
            deleted_profile = await user_service.get_user_profile(12345)
            assert deleted_profile is None

        finally:
            # Cleanup connections
            await user_repo.close()
            await settings_repo.close()
            await sub_repo.close()
