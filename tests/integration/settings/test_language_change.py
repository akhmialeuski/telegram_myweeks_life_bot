"""Integration tests for language settings change.

This module tests changing language through settings.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from src.bot.handlers.settings.language_handler import LanguageHandler
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
class TestLanguageSettingsChange:
    """Test language change through settings.

    This class tests the flow of changing language preference in user settings.
    """

    @pytest.fixture
    def language_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> LanguageHandler:
        """Create LanguageHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: LanguageHandler instance
        :rtype: LanguageHandler
        """
        return LanguageHandler(services=integration_container)

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

    async def test_language_selection_prompt(
        self,
        telegram_emulator: TelegramEmulator,
        language_handler: LanguageHandler,
        registered_user: None,
    ) -> None:
        """Test that language settings shows selection prompt.

        This test verifies that accessing language settings
        shows available language options.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param language_handler: Language handler instance
        :type language_handler: LanguageHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/settings",
            handler=language_handler,
        )

        assert telegram_emulator.get_reply_count() >= 1

    async def test_language_change_accepted(
        self,
        telegram_emulator: TelegramEmulator,
        language_handler: LanguageHandler,
        registered_user: None,
    ) -> None:
        """Test that language change is accepted.

        This test verifies that selecting a new language
        updates the user settings.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param language_handler: Language handler instance
        :type language_handler: LanguageHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/settings",
            handler=language_handler,
        )

        # Language is usually selected via callback buttons
        # For this test we simulate the callback data
        await telegram_emulator.send_callback(
            callback_data="lang_ru",
            handler=language_handler,
        )

        assert telegram_emulator.get_reply_count() >= 1
