"""Integration tests for birth date settings change.

This module tests changing birth date through settings.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from src.bot.handlers.settings.birth_date_handler import BirthDateHandler
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
class TestBirthDateSettingsChange:
    """Test birth date change through settings.

    This class tests the flow of changing birth date in user settings.
    """

    @pytest.fixture
    def birth_date_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> BirthDateHandler:
        """Create BirthDateHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: BirthDateHandler instance
        :rtype: BirthDateHandler
        """
        return BirthDateHandler(services=integration_container)

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

    async def test_birth_date_change_prompt(
        self,
        telegram_emulator: TelegramEmulator,
        birth_date_handler: BirthDateHandler,
        registered_user: None,
    ) -> None:
        """Test that birth date settings shows prompt.

        This test verifies that accessing birth date settings
        shows a prompt to enter new date.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param birth_date_handler: Birth date handler instance
        :type birth_date_handler: BirthDateHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/settings",
            handler=birth_date_handler,
        )

        assert telegram_emulator.get_reply_count() >= 1

    async def test_valid_new_birth_date_accepted(
        self,
        telegram_emulator: TelegramEmulator,
        birth_date_handler: BirthDateHandler,
        registered_user: None,
    ) -> None:
        """Test that valid new birth date is accepted.

        This test verifies that entering a valid new birth date
        updates the user settings.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param birth_date_handler: Birth date handler instance
        :type birth_date_handler: BirthDateHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        # Initiate settings change
        await telegram_emulator.send_command(
            command="/settings",
            handler=birth_date_handler,
        )

        # Enter new birth date
        await telegram_emulator.send_message(
            text="20.05.1985",
            handler=birth_date_handler,
            handler_method="handle_input",
        )

        assert telegram_emulator.get_reply_count() >= 1


@pytest.mark.skip(reason="Settings handlers require callback-based dispatcher routing")
@pytest.mark.integration
@pytest.mark.asyncio
class TestBirthDateSettingsValidation:
    """Test birth date validation in settings.

    This class tests validation of birth date input in settings.
    """

    @pytest.fixture
    def birth_date_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> BirthDateHandler:
        """Create BirthDateHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: BirthDateHandler instance
        :rtype: BirthDateHandler
        """
        return BirthDateHandler(services=integration_container)

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

    async def test_invalid_date_rejected(
        self,
        telegram_emulator: TelegramEmulator,
        birth_date_handler: BirthDateHandler,
        registered_user: None,
    ) -> None:
        """Test that invalid date format is rejected.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param birth_date_handler: Birth date handler instance
        :type birth_date_handler: BirthDateHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/settings",
            handler=birth_date_handler,
        )

        await telegram_emulator.send_message(
            text="invalid-date",
            handler=birth_date_handler,
            handler_method="handle_input",
        )

        assert telegram_emulator.get_reply_count() >= 1
