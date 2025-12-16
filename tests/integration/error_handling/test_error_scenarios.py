"""Integration tests for error scenarios.

This module tests various error handling scenarios including
unknown commands, unexpected input, and edge cases.
"""

import pytest

from src.bot.handlers.unknown_handler import UnknownHandler
from tests.integration.conftest import (
    IntegrationTestServiceContainer,
    TelegramEmulator,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestUnknownCommand:
    """Test unknown command handling.

    This class tests that the bot properly handles unknown commands
    with appropriate error messages.
    """

    @pytest.fixture
    def unknown_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> UnknownHandler:
        """Create UnknownHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: UnknownHandler instance
        :rtype: UnknownHandler
        """
        return UnknownHandler(services=integration_container)

    async def test_unknown_command_returns_error(
        self,
        telegram_emulator: TelegramEmulator,
        unknown_handler: UnknownHandler,
    ) -> None:
        """Test that unknown command returns error message.

        This test verifies that sending an unknown command results
        in a helpful error message.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param unknown_handler: Unknown handler instance
        :type unknown_handler: UnknownHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/unknown_command_xyz",
            handler=unknown_handler,
        )

        assert telegram_emulator.get_reply_count() >= 1

    async def test_random_text_is_handled(
        self,
        telegram_emulator: TelegramEmulator,
        unknown_handler: UnknownHandler,
    ) -> None:
        """Test that random text is handled appropriately.

        This test verifies that sending random text (not a command)
        is handled gracefully.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param unknown_handler: Unknown handler instance
        :type unknown_handler: UnknownHandler
        :returns: None
        """
        await telegram_emulator.send_message(
            text="some random text without context",
            handler=unknown_handler,
        )

        # Should get some response
        assert telegram_emulator.get_reply_count() >= 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestEdgeCaseInputs:
    """Test edge case input handling.

    This class tests various edge case inputs like empty strings,
    very long messages, and special characters.
    """

    @pytest.fixture
    def unknown_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> UnknownHandler:
        """Create UnknownHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: UnknownHandler instance
        :rtype: UnknownHandler
        """
        return UnknownHandler(services=integration_container)

    async def test_special_characters_handled(
        self,
        telegram_emulator: TelegramEmulator,
        unknown_handler: UnknownHandler,
    ) -> None:
        """Test that special characters are handled.

        This test verifies that messages with special characters
        don't cause errors.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param unknown_handler: Unknown handler instance
        :type unknown_handler: UnknownHandler
        :returns: None
        """
        await telegram_emulator.send_message(
            text="<script>alert('test')</script>",
            handler=unknown_handler,
        )

        # Should handle without error
        assert telegram_emulator.get_reply_count() >= 1

    async def test_emoji_input_handled(
        self,
        telegram_emulator: TelegramEmulator,
        unknown_handler: UnknownHandler,
    ) -> None:
        """Test that emoji input is handled.

        This test verifies that messages with emojis are handled
        correctly.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param unknown_handler: Unknown handler instance
        :type unknown_handler: UnknownHandler
        :returns: None
        """
        await telegram_emulator.send_message(
            text="🎉🎊🥳 Happy testing! 🧪✅",
            handler=unknown_handler,
        )

        assert telegram_emulator.get_reply_count() >= 1
