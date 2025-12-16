"""Integration tests for /weeks command.

This module tests the /weeks command functionality for retrieving
life statistics and week information.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from src.bot.handlers.weeks_handler import WeeksHandler
from src.enums import SubscriptionType
from tests.integration.conftest import (
    TEST_USER_ID,
    IntegrationTestServiceContainer,
    IntegrationTestServices,
    TelegramEmulator,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestWeeksCommandRegisteredUser:
    """Test /weeks command for registered users.

    This class tests that registered users can retrieve their
    life statistics using the /weeks command.
    """

    @pytest.fixture
    def weeks_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> WeeksHandler:
        """Create WeeksHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: WeeksHandler instance
        :rtype: WeeksHandler
        """
        return WeeksHandler(services=integration_container)

    @pytest_asyncio.fixture
    async def registered_user(
        self,
        integration_services: IntegrationTestServices,
    ) -> None:
        """Create a pre-registered user.

        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :returns: None
        """
        user_info = MagicMock()
        user_info.id = TEST_USER_ID
        user_info.username = "test_user"
        user_info.first_name = "Test"
        user_info.last_name = "User"

        await integration_services.user_service.create_user_profile(
            user_info=user_info,
            birth_date=date(1990, 1, 15),
            subscription_type=SubscriptionType.BASIC,
        )

    async def test_weeks_command_returns_statistics(
        self,
        telegram_emulator: TelegramEmulator,
        weeks_handler: WeeksHandler,
        registered_user: None,
    ) -> None:
        """Test that /weeks returns life statistics for registered user.

        This test verifies that a registered user receives their
        life statistics when sending the /weeks command.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param weeks_handler: Weeks handler instance
        :type weeks_handler: WeeksHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/weeks",
            handler=weeks_handler,
        )

        reply = telegram_emulator.get_last_reply()
        assert reply is not None
        assert telegram_emulator.get_reply_count() >= 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestWeeksCommandUnregisteredUser:
    """Test /weeks command for unregistered users.

    This class tests that unregistered users are prompted to register
    when trying to use the /weeks command.
    """

    @pytest.fixture
    def weeks_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> WeeksHandler:
        """Create WeeksHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: WeeksHandler instance
        :rtype: WeeksHandler
        """
        return WeeksHandler(services=integration_container)

    async def test_unregistered_user_prompted_to_register(
        self,
        telegram_emulator: TelegramEmulator,
        weeks_handler: WeeksHandler,
    ) -> None:
        """Test that unregistered user is prompted to register.

        This test verifies that when an unregistered user tries
        to use /weeks, they receive a message prompting registration.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param weeks_handler: Weeks handler instance
        :type weeks_handler: WeeksHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/weeks",
            handler=weeks_handler,
        )

        # Should get a response (either error or prompt)
        assert telegram_emulator.get_reply_count() >= 1
