"""Integration tests for help command handler.

This module tests the `/help` command functionality for both registered
and unregistered users.

Test Scenarios:
    - Help command for registered user
    - Help command for unregistered user
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.bot.handlers.help_handler import HelpHandler
from src.services.container import ServiceContainer
from tests.integration.conftest import (
    get_reply_text,
    set_message_text,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestHelpHandler:
    """Integration tests for the help command handler.

    These tests verify that help information is accessible to all users:
    - Available for new users
    - Available for registered users
    """

    async def test_help_command_unregistered_user_success(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that unregistered users can access help.

        Preconditions:
            - User is NOT registered

        Test Steps:
            1. User sends /help command
               Expected: Bot responds with help message
               Response: Help text with available commands

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = HelpHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/help")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert "/start" in reply_text  # Help should list start command

    async def test_help_command_registered_user_success(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
    ) -> None:
        """Test that registered users can access help.

        Preconditions:
            - User is registered

        Test Steps:
            1. Registered user sends /help command
               Expected: Bot responds with help message
               Response: Help text with available commands

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        # Register user
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        handler = HelpHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/help")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert "/settings" in reply_text  # Registered user help might differ
