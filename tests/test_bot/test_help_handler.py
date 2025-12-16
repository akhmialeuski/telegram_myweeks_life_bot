"""Unit tests for HelpHandler.

This module contains tests for the HelpHandler class which handles
the /help command and provides users with bot usage instructions.
"""

from unittest.mock import MagicMock

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_HELP
from src.bot.handlers.help_handler import HelpHandler
from tests.utils.fake_container import FakeServiceContainer


class TestHelpHandler:
    """Test suite for HelpHandler class.

    This class contains tests verifying that the HelpHandler correctly
    handles /help command requests and sends proper help messages to users.
    """

    @pytest.fixture
    def handler(self) -> HelpHandler:
        """Create HelpHandler instance for testing.

        :returns: Configured HelpHandler with fake service container
        :rtype: HelpHandler
        """
        services = FakeServiceContainer()
        return HelpHandler(services)

    @pytest.fixture(autouse=True)
    def mock_localization(self, mocker):
        """Configure localization service mock.

        This fixture mocks the BabelI18nAdapter class used in the handler
        to return predictable translation strings incorporating the key.

        :param mocker: pytest-mock fixture
        :type mocker: pytest_mock.MockerFixture
        :returns: Mocked translate method
        :rtype: MagicMock
        """
        mock_adapter = MagicMock()
        # Setup translate side effect
        mock_adapter.translate.side_effect = (
            lambda key, default, **kwargs: f"pgettext_{key}_{default}"
        )

        mocker.patch(
            "src.bot.handlers.help_handler.BabelI18nAdapter",
            return_value=mock_adapter,
        )
        return mock_adapter.translate

    def test_handler_creation(self, handler: HelpHandler) -> None:
        """Test that HelpHandler is created with correct command name.

        This test verifies that the handler is properly initialized
        with the /help command name constant.

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
    ) -> None:
        """Test successful help message generation and sending.

        This test verifies that the handle method correctly processes
        /help command and sends a properly formatted help message with
        HTML parse mode to the user.

        :param handler: HelpHandler instance
        :type handler: HelpHandler
        :param mock_update: Mocked Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        profile = MagicMock()
        profile.settings.language = "en"
        handler.services.user_service.get_user_profile.return_value = profile

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_help.text" in call_args.kwargs["text"]
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML
