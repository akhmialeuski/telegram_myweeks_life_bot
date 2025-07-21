"""Unit tests for WeeksHandler.

Tests the WeeksHandler class which handles /weeks command.
"""

from unittest.mock import MagicMock

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_WEEKS
from src.bot.handlers.weeks_handler import WeeksHandler
from src.utils.localization import SupportedLanguage


class TestWeeksHandler:
    """Test suite for WeeksHandler class."""

    @pytest.fixture
    def handler(self) -> WeeksHandler:
        """Create WeeksHandler instance.

        :returns: WeeksHandler instance
        :rtype: WeeksHandler
        """
        return WeeksHandler()

    def test_handler_creation(self, handler: WeeksHandler) -> None:
        """Test WeeksHandler creation.

        :param handler: WeeksHandler instance
        :returns: None
        """
        assert handler.command_name == f"/{COMMAND_WEEKS}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: WeeksHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_user_profile: MagicMock,
        mock_base_handler_user_service: MagicMock,
        mock_generate_message_week: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with successful week calculation.

        :param handler: WeeksHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_user_profile: Mock user profile
        :param mock_base_handler_user_service: Mocked user_service for base handler
        :param mock_generate_message_week: Mocked generate_message_week function
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_base_handler_user_service.is_valid_user_profile.return_value = True
        mock_base_handler_user_service.get_user_profile.return_value = mock_user_profile
        mock_generate_message_week.return_value = "You have lived 1234 weeks!"
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        # Execute
        await handler.handle(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "You have lived 1234 weeks!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_not_registered(
        self,
        handler: WeeksHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_base_handler_user_service: MagicMock,
        mock_get_message: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with unregistered user.

        :param handler: WeeksHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_base_handler_user_service: Mocked user_service for base handler
        :param mock_get_message: Mocked get_message function
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_base_handler_user_service.is_valid_user_profile.return_value = False
        mock_get_user_language.return_value = SupportedLanguage.EN.value
        mock_get_message.return_value = "Please register first!"

        # Execute
        await handler.handle(mock_update, mock_context)

        # Assert
        mock_get_message.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.args[0] == "Please register first!"
