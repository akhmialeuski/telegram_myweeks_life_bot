"""Unit tests for VisualizeHandler.

Tests the VisualizeHandler class which handles /visualize command.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.bot.handlers.visualize_handler import VisualizeHandler
from src.utils.localization import SupportedLanguage
from tests.utils.fake_container import FakeServiceContainer


class TestVisualizeHandler:
    """Test suite for VisualizeHandler class."""

    @pytest.fixture
    def handler(self) -> VisualizeHandler:
        """Create VisualizeHandler instance.

        :returns: VisualizeHandler instance
        :rtype: VisualizeHandler
        """
        services = FakeServiceContainer()
        return VisualizeHandler(services)

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
        with patch(
            "src.bot.handlers.visualize_handler.generate_message_visualize"
        ) as mock_generate_message:
            with patch(
                "src.bot.handlers.visualize_handler.generate_visualization"
            ) as mock_generate_visualization:
                handler.services.user_service.is_valid_user_profile.return_value = True
                handler.services.user_service.get_user_profile.return_value = Mock()
                mock_generate_message.return_value = "Here's your life visualization!"
                mock_generate_visualization.return_value = Mock()

                # Execute
                await handler.handle(mock_update, mock_context)

                # Assert
                mock_update.message.reply_photo.assert_called_once()
                call_args = mock_update.message.reply_photo.call_args
                assert call_args.kwargs["caption"] == "Here's your life visualization!"
                assert call_args.kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_handle_not_registered(
        self,
        handler: VisualizeHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
        mock_get_message: MagicMock,
    ) -> None:
        """Test handle method with unregistered user.

        :param handler: VisualizeHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_base_handler_user_service: Mocked user_service for base handler
        :param mock_get_user_language: Mocked get_user_language function
        :param mock_get_message: Mocked get_message function
        :returns: None
        """
        # Setup - user not registered
        handler.services.user_service.is_valid_user_profile.return_value = False
        mock_get_user_language.return_value = SupportedLanguage.EN.value
        mock_get_message.return_value = "You need to register first!"

        # Execute
        result = await handler.handle(mock_update, mock_context)

        # Assert
        assert result is None
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_visualize_returns_none(
        self,
        handler: VisualizeHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test that _handle_visualize returns None.

        This test covers line 114: return None in _handle_visualize method.

        :param handler: VisualizeHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        # Mock all required functions in the module where they're imported
        with patch(
            "src.bot.handlers.visualize_handler.generate_visualization"
        ) as mock_generate_viz, patch(
            "src.bot.handlers.visualize_handler.generate_message_visualize"
        ) as mock_generate_msg:
            # Setup mocks
            handler.services.user_service.is_valid_user_profile.return_value = True
            handler.services.user_service.get_user_profile.return_value = MagicMock()
            mock_generate_viz.return_value = b"fake_image_data"
            mock_generate_msg.return_value = "Visualization caption"

            # Mock reply_photo
            mock_update.message.reply_photo = AsyncMock(return_value=None)

            # Execute
            result = await handler.handle(mock_update, mock_context)

            # Assert - the method should return None
            assert result is None
            mock_update.message.reply_photo.assert_called_once()
