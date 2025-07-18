"""Unit tests for SubscriptionHandler.

Tests the SubscriptionHandler class which handles /subscription command.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.handlers.subscription_handler import SubscriptionHandler
from src.database.models import SubscriptionType


class TestSubscriptionHandler:
    """Test suite for SubscriptionHandler class."""

    @pytest.fixture
    def handler(self) -> SubscriptionHandler:
        """Create SubscriptionHandler instance.

        :returns: SubscriptionHandler instance
        :rtype: SubscriptionHandler
        """
        return SubscriptionHandler()

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

    @pytest.fixture
    def mock_user_profile(self) -> Mock:
        """Create mock user profile.

        :returns: Mock user profile
        :rtype: Mock
        """
        profile = Mock()
        profile.subscription_type = SubscriptionType.BASIC
        profile.is_active = True
        return profile

    def test_handler_creation(self, handler: SubscriptionHandler) -> None:
        """Test SubscriptionHandler creation.

        :param handler: SubscriptionHandler instance
        :returns: None
        """
        assert handler.command_name == "/subscription"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: SubscriptionHandler,
        mock_update: Mock,
        mock_context: Mock,
        mock_user_profile: Mock,
    ) -> None:
        """Test handle method with successful subscription info.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_user_profile: Mock user profile
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.subscription_handler.user_service"
        ) as mock_user_service:
            with patch(
                "src.bot.handlers.base_handler.user_service"
            ) as mock_base_user_service:
                with patch(
                    "src.bot.handlers.subscription_handler.generate_message_subscription_current"
                ) as mock_generate_message:
                    with patch(
                        "src.bot.handlers.subscription_handler.get_user_language"
                    ) as mock_get_language:
                        mock_base_user_service.is_valid_user_profile.return_value = True
                        mock_user_service.get_user_profile.return_value = (
                            mock_user_profile
                        )
                        mock_generate_message.return_value = "Your subscription info!"
                        mock_get_language.return_value = "en"

                        # Execute
                        await handler.handle(mock_update, mock_context)

                        # Assert
                        mock_update.message.reply_text.assert_called_once()
                        call_args = mock_update.message.reply_text.call_args
                        assert call_args.kwargs["text"] == "Your subscription info!"
                        assert call_args.kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_handle_no_profile(
        self, handler: SubscriptionHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with no user profile.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.subscription_handler.user_service"
        ) as mock_user_service:
            with patch(
                "src.bot.handlers.base_handler.user_service"
            ) as mock_base_user_service:
                with patch(
                    "src.bot.handlers.subscription_handler.get_user_language"
                ) as mock_get_language:
                    with patch(
                        "src.bot.handlers.subscription_handler.get_message"
                    ) as mock_get_message:
                        mock_base_user_service.is_valid_user_profile.return_value = True
                        mock_user_service.get_user_profile.return_value = None
                        mock_get_language.return_value = "en"
                        mock_get_message.return_value = "No profile found!"

                        # Execute
                        await handler.handle(mock_update, mock_context)

                        # Assert
                        mock_update.message.reply_text.assert_called_once_with(
                            "No profile found!"
                        )

    @pytest.mark.asyncio
    async def test_handle_exception(
        self, handler: SubscriptionHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with exception.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.subscription_handler.user_service"
        ) as mock_user_service:
            mock_user_service.get_user_profile.side_effect = Exception("Service error")

            # Execute and assert no exception is raised
            await handler.handle(mock_update, mock_context)
