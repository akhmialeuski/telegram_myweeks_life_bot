"""Unit tests for HelpHandler.

Tests the HelpHandler class which handles /help command.
"""

from unittest.mock import MagicMock, patch

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_HELP
from src.bot.handlers.help_handler import HelpHandler
from src.utils.localization import SupportedLanguage
from tests.utils.fake_container import FakeServiceContainer


class TestHelpHandler:
    """Test suite for HelpHandler class."""

    @pytest.fixture
    def handler(self) -> HelpHandler:
        """Create HelpHandler instance.

        :returns: HelpHandler instance
        :rtype: HelpHandler
        """
        services = FakeServiceContainer()
        return HelpHandler(services)

    def test_handler_creation(self, handler: HelpHandler) -> None:
        """Test HelpHandler creation.

        :param handler: HelpHandler instance
        :type handler: HelpHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name == f"/{COMMAND_HELP}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: HelpHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with successful help message.

        :param handler: HelpHandler instance
        :type handler: HelpHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_get_user_language: Mocked get_user_language function
        :type mock_get_user_language: MagicMock
        :returns: None
        :rtype: None
        """
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        with patch(
            "src.bot.handlers.help_handler.generate_message_help"
        ) as mock_generate_message_help:
            mock_generate_message_help.return_value = "Here's the help message!"

            await handler.handle(mock_update, mock_context)

            mock_generate_message_help.assert_called_once_with(
                user_info=mock_update.effective_user
            )
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert call_args.kwargs["text"] == "Here's the help message!"
            assert call_args.kwargs["parse_mode"] == ParseMode.HTML
