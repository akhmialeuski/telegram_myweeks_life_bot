"""Unit tests for SubscriptionHandler.

Tests the SubscriptionHandler class which handles /subscription command.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.constants import COMMAND_SUBSCRIPTION
from src.bot.handlers.subscription_handler import SubscriptionHandler
from src.core.enums import SubscriptionType
from src.database.service import UserSubscriptionUpdateError


class TestSubscriptionHandler:
    """Test suite for SubscriptionHandler class."""

    @pytest.fixture
    def handler(self) -> SubscriptionHandler:
        """Create SubscriptionHandler instance."""
        from tests.utils.fake_container import FakeServiceContainer

        services = FakeServiceContainer()
        return SubscriptionHandler(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker):
        """Mock use_locale to control translations."""
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.subscription_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    @pytest.fixture
    def make_mock_callback_query(self):
        def _make(update, subscription_key: str):
            query = MagicMock()
            query.data = f"subscription_{subscription_key}"
            query.answer = AsyncMock()
            query.edit_message_text = AsyncMock()
            update.callback_query = query
            return query

        return _make

    def test_handler_creation(self, handler: SubscriptionHandler) -> None:
        """Test SubscriptionHandler creation."""
        assert handler.command_name == f"/{COMMAND_SUBSCRIPTION}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
    ) -> None:
        """Test handle method with successful subscription info."""
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        # Mock user profile attributes
        mock_user_profile.settings = MagicMock()
        mock_user_profile.settings.language = "en"
        mock_user_profile.subscription = MagicMock()
        mock_user_profile.subscription.subscription_type = SubscriptionType.BASIC

        handler.services.user_service.is_valid_user_profile.return_value = True
        handler.services.user_service.get_user_profile.return_value = mock_user_profile

        with patch.object(handler, "send_message") as mock_send_message:
            await handler.handle(mock_update, mock_context)
            mock_send_message.assert_called_once()
            call_kwargs = mock_send_message.call_args.kwargs
            assert "pgettext_subscription.management_" in call_kwargs["message_text"]

    @pytest.mark.asyncio
    async def test_handle_no_profile(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method when user profile not found."""
        handler.services.user_service.is_valid_user_profile.return_value = False
        await handler.handle(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_exception(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method with exception."""
        # Setup mock to return valid profile for context extraction, then fail
        mock_profile = MagicMock()
        mock_profile.settings.language = "en"
        handler.services.user_service.get_user_profile.return_value = mock_profile
        handler.services.user_service.is_valid_user_profile.return_value = True

        # Mock the internal handler method to raise exception
        with patch.object(
            handler, "_handle_subscription", side_effect=Exception("Test exception")
        ):
            await handler.handle(mock_update, mock_context)
            # Exception should be caught and handled by base handler

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_same_subscription(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test handle_subscription_callback when user selects same subscription."""
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query(mock_update, "basic")
        handler.services.user_service.get_user_profile.return_value = mock_user_profile

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_subscription_callback(mock_update, mock_context)

            mock_callback_query.answer.assert_called_once()
            mock_edit_message.assert_called_once()
            assert (
                "pgettext_subscription.already_active_"
                in mock_edit_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_successful_change(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test handle_subscription_callback with successful subscription change."""
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query(mock_update, "premium")
        handler.services.user_service.get_user_profile.return_value = mock_user_profile
        handler.services.user_service.update_user_subscription.return_value = None

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_subscription_callback(mock_update, mock_context)

            mock_callback_query.answer.assert_called_once()
            handler.services.user_service.update_user_subscription.assert_called_once_with(
                mock_update.effective_user.id, SubscriptionType.PREMIUM
            )
            mock_edit_message.assert_called_once()
            assert (
                "pgettext_subscription.change_success_"
                in mock_edit_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_update_error(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test handle_subscription_callback with UserSubscriptionUpdateError."""
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query(mock_update, "premium")
        handler.services.user_service.get_user_profile.return_value = mock_user_profile
        handler.services.user_service.update_user_subscription.side_effect = (
            UserSubscriptionUpdateError("Update failed")
        )

        with patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle_subscription_callback(mock_update, mock_context)
            mock_callback_query.answer.assert_called_once()
            mock_send_error.assert_called_once()
            assert (
                "pgettext_subscription.change_failed"
                in mock_send_error.call_args.kwargs["error_message"]
            )

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_general_exception(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test handle_subscription_callback with general exception."""
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query(mock_update, "premium")
        handler.services.user_service.get_user_profile.return_value = mock_user_profile
        handler.services.user_service.update_user_subscription.side_effect = Exception(
            "General error"
        )

        with patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle_subscription_callback(mock_update, mock_context)
            mock_callback_query.answer.assert_called_once()
            mock_send_error.assert_called_once()
            assert (
                "pgettext_subscription.change_error"
                in mock_send_error.call_args.kwargs["error_message"]
            )
