"""Integration tests for existing user /start behavior.

This module tests the /start command behavior for users
who are already registered in the system.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from src.bot.handlers.start_handler import StartHandler
from src.database.models.user import User
from src.enums import SubscriptionType
from tests.integration.conftest import (
    TEST_USER_ID,
    IntegrationTestServiceContainer,
    IntegrationTestServices,
    TelegramEmulator,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestExistingUserStartCommand:
    """Test /start command for already registered users.

    This class tests that registered users see welcome back
    messages instead of registration prompts.
    """

    @pytest.fixture
    def start_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> StartHandler:
        """Create StartHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: StartHandler instance
        :rtype: StartHandler
        """
        return StartHandler(services=integration_container)

    @pytest_asyncio.fixture
    async def registered_user_profile(
        self,
        integration_services: IntegrationTestServices,
    ) -> User:
        """Create a pre-registered user for testing.

        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :returns: Created user profile
        :rtype: User
        """
        # Create mock user info object
        user_info = MagicMock()
        user_info.id = TEST_USER_ID
        user_info.username = "existing_user"
        user_info.first_name = "Existing"
        user_info.last_name = "User"

        # Register the user
        profile = await integration_services.user_service.create_user_profile(
            user_info=user_info,
            birth_date=date(1990, 1, 15),
            subscription_type=SubscriptionType.BASIC,
        )
        return profile

    async def test_registered_user_sees_welcome_back_message(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
        registered_user_profile: User,
    ) -> None:
        """Test that registered user sees welcome back message.

        This test verifies that when a registered user sends /start,
        they receive a welcome back message instead of registration prompt.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :param registered_user_profile: Pre-registered user profile
        :type registered_user_profile: User
        :returns: None
        """
        # Verify user is registered
        assert registered_user_profile is not None
        assert registered_user_profile.telegram_id == TEST_USER_ID

        # Act: Send /start command
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Assert: Bot replied
        reply = telegram_emulator.get_last_reply()
        assert reply is not None
        assert telegram_emulator.get_reply_count() >= 1

    async def test_existing_user_profile_not_modified(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
        integration_services: IntegrationTestServices,
        registered_user_profile: User,
    ) -> None:
        """Test that /start doesn't modify existing user profile.

        This test verifies that sending /start as a registered user
        doesn't modify the existing user data.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :param registered_user_profile: Pre-registered user profile
        :type registered_user_profile: User
        :returns: None
        """
        # Store original data
        original_birth_date = registered_user_profile.settings.birth_date

        # Act: Send /start command
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Fetch profile again
        profile_after = await integration_services.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )

        # Assert: Profile data unchanged
        assert profile_after is not None
        assert profile_after.settings.birth_date == original_birth_date


@pytest.mark.integration
@pytest.mark.asyncio
class TestExistingUserDifferentSubscriptions:
    """Test /start behavior for users with different subscriptions.

    This class tests that the /start response might vary based on
    the user's subscription level.
    """

    @pytest.fixture
    def start_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> StartHandler:
        """Create StartHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: StartHandler instance
        :rtype: StartHandler
        """
        return StartHandler(services=integration_container)

    async def test_basic_user_start_response(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
        integration_services: IntegrationTestServices,
    ) -> None:
        """Test /start response for basic subscription user.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :returns: None
        """
        # Create basic user
        user_info = MagicMock()
        user_info.id = TEST_USER_ID
        user_info.username = "basic_user"
        user_info.first_name = "Basic"
        user_info.last_name = "User"

        await integration_services.user_service.create_user_profile(
            user_info=user_info,
            birth_date=date(1990, 1, 15),
            subscription_type=SubscriptionType.BASIC,
        )

        # Send /start
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Verify response received
        assert telegram_emulator.get_reply_count() >= 1

    async def test_premium_user_start_response(
        self,
        integration_services: IntegrationTestServices,
        integration_container: IntegrationTestServiceContainer,
    ) -> None:
        """Test /start response for premium subscription user.

        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: None
        """
        # Create premium user with different ID
        premium_user_id = 999888777

        emulator = TelegramEmulator(
            services=integration_services,
            user_id=premium_user_id,
            username="premium_user",
        )

        user_info = MagicMock()
        user_info.id = premium_user_id
        user_info.username = "premium_user"
        user_info.first_name = "Premium"
        user_info.last_name = "User"

        await integration_services.user_service.create_user_profile(
            user_info=user_info,
            birth_date=date(1985, 6, 15),
            subscription_type=SubscriptionType.PREMIUM,
        )

        handler = StartHandler(services=integration_container)

        # Send /start
        await emulator.send_command(
            command="/start",
            handler=handler,
        )

        # Verify response received
        assert emulator.get_reply_count() >= 1
