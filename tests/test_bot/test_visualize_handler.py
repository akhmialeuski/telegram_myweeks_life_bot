"""Unit tests for VisualizeHandler.

Tests the VisualizeHandler class which handles /visualize command.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.handlers.visualize_handler import VisualizeHandler


class TestVisualizeHandler:
    """Test suite for VisualizeHandler class."""

    @pytest.fixture
    def handler(self) -> VisualizeHandler:
        """Create VisualizeHandler instance.

        :returns: VisualizeHandler instance
        :rtype: VisualizeHandler
        """
        return VisualizeHandler()

    @pytest.fixture
    def mock_update(self) -> Mock:
        """Create mock Update object.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "testuser"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self) -> Mock:
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        return context

    def test_handler_creation(self, handler: VisualizeHandler) -> None:
        """Test VisualizeHandler creation.

        :param handler: VisualizeHandler instance
        :returns: None
        """
        assert handler.command_name == "/visualize"

    @pytest.mark.asyncio
    async def test_handle_success(
        self, handler: VisualizeHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with successful visualization.

        :param handler: VisualizeHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.base_handler.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.visualize_handler.generate_message_visualize"
            ) as mock_generate_message:
                with patch(
                    "src.bot.handlers.visualize_handler.generate_visualization"
                ) as mock_generate_visualization:
                    mock_user_service.is_valid_user_profile.return_value = True
                    mock_user_service.get_user_profile.return_value = Mock()
                    mock_generate_message.return_value = (
                        "Here's your life visualization!"
                    )
                    mock_generate_visualization.return_value = Mock()

                    # Execute
                    await handler.handle(mock_update, mock_context)

                    # Assert
                    mock_update.message.reply_photo.assert_called_once()
                    call_args = mock_update.message.reply_photo.call_args
                    assert (
                        call_args.kwargs["caption"] == "Here's your life visualization!"
                    )
                    assert call_args.kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_handle_not_registered(
        self, handler: VisualizeHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with unregistered user.

        :param handler: VisualizeHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.base_handler.user_service") as mock_user_service:
            with patch("src.bot.handlers.base_handler.get_message") as mock_get_message:
                mock_user_service.is_valid_user_profile.return_value = False
                mock_get_message.return_value = "Please register first!"

                # Execute
                await handler.handle(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with(
                    "Please register first!"
                )
