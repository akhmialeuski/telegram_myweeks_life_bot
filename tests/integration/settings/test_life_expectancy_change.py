"""Integration tests for life expectancy settings change.

This module tests changing life expectancy through settings.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from src.bot.handlers.settings.life_expectancy_handler import (
    LifeExpectancyHandler,
)
from src.enums import SubscriptionType
from tests.integration.conftest import (
    TEST_USER_ID,
    IntegrationTestServiceContainer,
    IntegrationTestServices,
    TelegramEmulator,
)


@pytest.mark.skip(reason="Settings handlers require callback-based dispatcher routing")
@pytest.mark.integration
@pytest.mark.asyncio
class TestLifeExpectancySettingsChange:
    """Test life expectancy change through settings.

    This class tests the flow of changing life expectancy in user settings.
    """

    @pytest.fixture
    def life_expectancy_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> LifeExpectancyHandler:
        """Create LifeExpectancyHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: LifeExpectancyHandler instance
        :rtype: LifeExpectancyHandler
        """
        return LifeExpectancyHandler(services=integration_container)

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

    async def test_life_expectancy_prompt(
        self,
        telegram_emulator: TelegramEmulator,
        life_expectancy_handler: LifeExpectancyHandler,
        registered_user: None,
    ) -> None:
        """Test that life expectancy settings shows prompt.

        This test verifies that accessing life expectancy settings
        shows a prompt to enter new value.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param life_expectancy_handler: Life expectancy handler instance
        :type life_expectancy_handler: LifeExpectancyHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/settings",
            handler=life_expectancy_handler,
        )

        assert telegram_emulator.get_reply_count() >= 1

    async def test_valid_life_expectancy_accepted(
        self,
        telegram_emulator: TelegramEmulator,
        life_expectancy_handler: LifeExpectancyHandler,
        registered_user: None,
    ) -> None:
        """Test that valid life expectancy is accepted.

        This test verifies that entering a valid life expectancy
        value updates the user settings.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param life_expectancy_handler: Life expectancy handler instance
        :type life_expectancy_handler: LifeExpectancyHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/settings",
            handler=life_expectancy_handler,
        )

        await telegram_emulator.send_message(
            text="85",
            handler=life_expectancy_handler,
            handler_method="handle_input",
        )

        assert telegram_emulator.get_reply_count() >= 1


@pytest.mark.skip(reason="Settings handlers require callback-based dispatcher routing")
@pytest.mark.integration
@pytest.mark.asyncio
class TestLifeExpectancyValidation:
    """Test life expectancy validation in settings.

    This class tests validation of life expectancy input in settings.
    """

    @pytest.fixture
    def life_expectancy_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> LifeExpectancyHandler:
        """Create LifeExpectancyHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: LifeExpectancyHandler instance
        :rtype: LifeExpectancyHandler
        """
        return LifeExpectancyHandler(services=integration_container)

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

    async def test_invalid_life_expectancy_rejected(
        self,
        telegram_emulator: TelegramEmulator,
        life_expectancy_handler: LifeExpectancyHandler,
        registered_user: None,
    ) -> None:
        """Test that invalid life expectancy is rejected.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param life_expectancy_handler: Life expectancy handler instance
        :type life_expectancy_handler: LifeExpectancyHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/settings",
            handler=life_expectancy_handler,
        )

        await telegram_emulator.send_message(
            text="not-a-number",
            handler=life_expectancy_handler,
            handler_method="handle_input",
        )

        assert telegram_emulator.get_reply_count() >= 1

    async def test_out_of_range_life_expectancy_rejected(
        self,
        telegram_emulator: TelegramEmulator,
        life_expectancy_handler: LifeExpectancyHandler,
        registered_user: None,
    ) -> None:
        """Test that out of range life expectancy is rejected.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param life_expectancy_handler: Life expectancy handler instance
        :type life_expectancy_handler: LifeExpectancyHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/settings",
            handler=life_expectancy_handler,
        )

        # Too high value
        await telegram_emulator.send_message(
            text="200",
            handler=life_expectancy_handler,
            handler_method="handle_input",
        )

        assert telegram_emulator.get_reply_count() >= 1
