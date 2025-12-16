"""Integration tests for /visualize command.

This module tests the /visualize command functionality for generating
life visualization images.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from src.bot.handlers.visualize_handler import VisualizeHandler
from src.enums import SubscriptionType
from tests.integration.conftest import (
    TEST_USER_ID,
    IntegrationTestServiceContainer,
    IntegrationTestServices,
    TelegramEmulator,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestVisualizeCommandRegisteredUser:
    """Test /visualize command for registered users.

    This class tests that registered users can generate their
    life visualization.
    """

    @pytest.fixture
    def visualize_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> VisualizeHandler:
        """Create VisualizeHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: VisualizeHandler instance
        :rtype: VisualizeHandler
        """
        return VisualizeHandler(services=integration_container)

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

    @pytest.mark.skip(
        reason="VisualizeHandler sends photos, requires extended mocking for send_photo"
    )
    async def test_visualize_command_returns_response(
        self,
        telegram_emulator: TelegramEmulator,
        visualize_handler: VisualizeHandler,
        registered_user: None,
    ) -> None:
        """Test that /visualize returns a response for registered user.

        This test verifies that a registered user receives a response
        when sending the /visualize command.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param visualize_handler: Visualize handler instance
        :type visualize_handler: VisualizeHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/visualize",
            handler=visualize_handler,
        )

        # Should get at least one reply
        assert telegram_emulator.get_reply_count() >= 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestVisualizeCommandUnregisteredUser:
    """Test /visualize command for unregistered users.

    This class tests that unregistered users are handled properly
    when trying to use the /visualize command.
    """

    @pytest.fixture
    def visualize_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> VisualizeHandler:
        """Create VisualizeHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: VisualizeHandler instance
        :rtype: VisualizeHandler
        """
        return VisualizeHandler(services=integration_container)

    async def test_unregistered_user_gets_response(
        self,
        telegram_emulator: TelegramEmulator,
        visualize_handler: VisualizeHandler,
    ) -> None:
        """Test that unregistered user gets appropriate response.

        This test verifies that when an unregistered user tries
        to use /visualize, they receive an appropriate message.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param visualize_handler: Visualize handler instance
        :type visualize_handler: VisualizeHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/visualize",
            handler=visualize_handler,
        )

        # Should get a response
        assert telegram_emulator.get_reply_count() >= 1
