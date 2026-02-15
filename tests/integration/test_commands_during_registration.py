"""Integration tests for reproducing and verifying fixes for Enum mismatch bugs."""

from unittest.mock import MagicMock

import pytest

from src.bot.handlers.settings.dispatcher import SettingsDispatcher
from src.bot.handlers.start_handler import StartHandler
from src.bot.handlers.subscription_handler import SubscriptionHandler
from src.bot.handlers.visualize_handler import VisualizeHandler
from src.bot.handlers.weeks_handler import WeeksHandler
from src.services.container import ServiceContainer
from tests.integration.conftest import (
    create_user_with_invalid_enum_value,
    get_reply_text,
)


class TestCommandsDuringRegistration:
    """Test how other commands behave during the registration process."""

    @pytest.mark.asyncio
    async def test_start_command_with_enum_validator_error(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Verify behavior when user exists but settings have enum mismatch (PROD BUG REPRO).

        This test reproduces the issue where 'weekly' (lowercase) in DB causes
        SQLAlchemy validation error, leading to user not found.
        """
        # 1. Setup: Create user with invalid enum value helper
        await create_user_with_invalid_enum_value(test_service_container)

        # 2. Execute /start command
        start_handler = StartHandler(test_service_container)
        mock_update.message.text = "/start"

        await start_handler.handle(update=mock_update, context=mock_context)

        # 3. Verification
        # In the bug state, the user is treated as new, so we get the welcome message.
        reply = get_reply_text(mock_update.message)
        assert reply is not None

        # Should NOT contain
        # "👋 Hello, Anatol! Welcome to LifeWeeksBot!
        #
        # This bot will help you track the weeks of your life.
        #
        # 📅 Please enter your birth date in DD.MM.YYYY format For example: 15.03.1990"
        assert "Welcome to LifeWeeksBot!" not in reply
        assert "Please enter your birth date in" not in reply

    @pytest.mark.asyncio
    async def test_access_to_commands_with_enum_validator_error(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Verify behavior of commands when user exists but has enum mismatch.

        The test ensures that commands are still accessible (or at least don't say
        "not registered") when this bug is present/fixed.
        """
        # 1. Setup: Create user with invalid enum value helper
        await create_user_with_invalid_enum_value(test_service_container)

        # 2. Execute commands
        commands = [
            ("/settings", SettingsDispatcher),
            ("/weeks", WeeksHandler),
            ("/visualize", VisualizeHandler),
            ("/subscription", SubscriptionHandler),
        ]

        for command, handler_class in commands:
            handler = handler_class(test_service_container)
            mock_update.message.text = command
            mock_update.message.reply_text.reset_mock()

            await handler.handle(update=mock_update, context=mock_context)

            # 3. Verification
            # If the bug IS present, this should FAIL because commands might error or treat as not registered.
            # We want to ensure it works CORRECTLY (i.e. access granted), so if bug is present, it fails.
            reply = get_reply_text(mock_update.message)
            assert reply is not None
            # Ensure it's not the "not registered" message
            assert "You are not registered. Use /start to register." != reply
