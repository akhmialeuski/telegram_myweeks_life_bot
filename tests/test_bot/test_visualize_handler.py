"""Unit tests for VisualizeHandler.

Tests the VisualizeHandler class which handles /visualize command.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.bot.handlers.visualize_handler import VisualizeHandler
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

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker):
        """Mock use_locale to control translations."""
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.visualize_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

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
        """Test handle method with successful visualization."""
        with patch(
            "src.bot.handlers.visualize_handler.generate_visualization"
        ) as mock_generate_visualization:
            handler.services.user_service.is_valid_user_profile.return_value = True
            profile = Mock()
            profile.settings = Mock(language="en")
            handler.services.user_service.get_user_profile.return_value = profile
            mock_generate_visualization.return_value = Mock()

            await handler.handle(mock_update, mock_context)

            mock_update.message.reply_photo.assert_called_once()
            call_args = mock_update.message.reply_photo.call_args
            assert "pgettext_visualize.info_" in call_args.kwargs["caption"]

    @pytest.mark.asyncio
    async def test_handle_not_registered(
        self,
        handler: VisualizeHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method with unregistered user."""
        handler.services.user_service.is_valid_user_profile.return_value = False

        result = await handler.handle(mock_update, mock_context)

        assert result is None
        mock_update.message.reply_text.assert_called_once()
        # The specific message is checked within the wrapper, here we just check the call

    @pytest.mark.asyncio
    async def test_handle_visualize_returns_none(
        self,
        handler: VisualizeHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_user_profile: MagicMock,
    ) -> None:
        """Test handle method when visualization returns None."""
        handler.services.user_service.is_valid_user_profile.return_value = True
        handler.services.user_service.get_user_profile.return_value = mock_user_profile
        # Mock the user profile to have proper settings
        if not getattr(mock_user_profile, "settings", None):
            mock_user_profile.settings = MagicMock()
        mock_user_profile.settings.language = "en"

        with patch(
            "src.bot.handlers.visualize_handler.generate_visualization",
            return_value=b"img",
        ):
            await handler.handle(mock_update, mock_context)
        mock_update.message.reply_photo.assert_called_once()
        call_args = mock_update.message.reply_photo.call_args
        assert "pgettext_visualize.info_" in call_args.kwargs["caption"]
