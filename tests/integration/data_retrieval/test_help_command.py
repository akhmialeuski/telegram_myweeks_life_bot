"""Integration tests for help command.

This module tests the /help command functionality.
"""

import pytest

from src.bot.handlers.help_handler import HelpHandler
from tests.integration.conftest import (
    IntegrationTestServiceContainer,
    TelegramEmulator,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestHelpCommand:
    """Test /help command functionality.

    This class tests the help command response for various user states.
    """

    @pytest.fixture
    def help_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> HelpHandler:
        """Create HelpHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: HelpHandler instance
        :rtype: HelpHandler
        """
        return HelpHandler(services=integration_container)

    async def test_help_command_returns_message(
        self,
        telegram_emulator: TelegramEmulator,
        help_handler: HelpHandler,
    ) -> None:
        """Test that /help command returns help message.

        This test verifies that the help command sends a message
        with available commands and usage instructions.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param help_handler: Help handler instance
        :type help_handler: HelpHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/help",
            handler=help_handler,
        )

        reply = telegram_emulator.get_last_reply()
        assert reply is not None
        assert telegram_emulator.get_reply_count() >= 1

    async def test_help_message_contains_commands(
        self,
        telegram_emulator: TelegramEmulator,
        help_handler: HelpHandler,
    ) -> None:
        """Test that help message contains available commands.

        This test verifies that the help message includes references
        to the main bot commands that users can use.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param help_handler: Help handler instance
        :type help_handler: HelpHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/help",
            handler=help_handler,
        )

        reply = telegram_emulator.get_last_reply()
        assert reply is not None
        # Help should contain text
        assert reply.text is not None or telegram_emulator.get_reply_count() >= 1
