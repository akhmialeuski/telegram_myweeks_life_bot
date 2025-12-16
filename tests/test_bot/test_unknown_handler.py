"""Unit tests for UnknownHandler.

This module contains tests for the UnknownHandler class which handles
messages and commands that the bot does not recognize.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.constants import COMMAND_UNKNOWN
from src.bot.handlers.unknown_handler import UnknownHandler
from tests.utils.fake_container import FakeServiceContainer


class TestUnknownHandler:
    """Test suite for UnknownHandler class.

    This class contains tests verifying that the UnknownHandler correctly
    processes unrecognized commands and messages, providing appropriate
    feedback to users through the MessageContext system.
    """

    @pytest.fixture
    def handler(self) -> UnknownHandler:
        """Create UnknownHandler instance for testing.

        :returns: Configured UnknownHandler with fake service container
        :rtype: UnknownHandler
        """
        services = FakeServiceContainer()
        return UnknownHandler(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker):
        """Mock use_locale function to control translation behavior.

        This fixture automatically mocks the use_locale function to return
        predictable translation strings for testing purposes.

        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        :returns: Mocked pgettext function
        :rtype: MagicMock
        """
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.unknown_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    def test_handler_creation(self, handler: UnknownHandler) -> None:
        """Test that UnknownHandler is created with correct command identifier.

        This test verifies that the handler is properly initialized
        with the unknown command identifier constant.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name == f"/{COMMAND_UNKNOWN}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test successful handling of unknown command or message.

        This test verifies that the handle method correctly processes
        unrecognized input and sends an appropriate response message
        to inform the user.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mocked Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_unknown.command_" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_uses_message_context(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that handle method properly uses MessageContext for localization.

        This test verifies that the handler correctly utilizes the
        MessageContext system to determine user language and send
        localized messages.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mocked Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        handler.send_message = AsyncMock()
        mock_update.effective_user.language_code = "en"

        await handler.handle(mock_update, mock_context)

        handler.send_message.assert_called_once()
        call_args = handler.send_message.call_args
        message_text = call_args.kwargs["message_text"]
        assert "pgettext_unknown.command_" in message_text

    @pytest.mark.asyncio
    async def test_handle_unknown_command(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of unknown command starting with /.

        This test verifies that unknown commands starting with / are handled correctly.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mocked Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        # Set message text to an unknown command
        mock_update.message.text = "/invalid_command"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_unknown_text_message(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of unknown text message (not a command).

        This test verifies that unknown text messages (not commands) are handled correctly.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mocked Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        # Set message text to a plain text (not starting with /)
        mock_update.message.text = "some random text message"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
