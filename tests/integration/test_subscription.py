"""Integration tests for subscription command handler.

This module tests the `/subscription` command functionality and callback handling.

Test Scenarios:
    - View subscription status (registered user)
    - Change subscription type (callback)
    - Access denied for unregistered user
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.bot.handlers.subscription_handler import SubscriptionHandler
from src.enums import SubscriptionType
from src.services.container import ServiceContainer
from tests.integration.conftest import (
    TEST_USER_ID,
    get_reply_markup,
    get_reply_text,
    set_message_text,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestSubscriptionHandler:
    """Integration tests for subscription management.

    These tests verify user subscription interactions:
    - Viewing current subscription
    - Upgrading/downgrading subscription
    - Access control
    """

    async def test_view_subscription_registered_user_success(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
    ) -> None:
        """Test that registered users can view subscription status.

        Preconditions:
            - User is registered with BASIC subscription

        Test Steps:
            1. Registered user sends /subscription
               Expected: Handler shows current status
               Response: Message with "Basic" and management keyboard

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        # Create user with default Basic subscription
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        handler = SubscriptionHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/subscription")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)
        markup = get_reply_markup(mock_message=mock_update.message)

        assert reply_text is not None
        assert "Basic" in reply_text  # Default subscription
        assert markup is not None  # Should have inline keyboard

    async def test_change_subscription_callback_updates_db(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
    ) -> None:
        """Test changing subscription via inline keyboard callback.

        Preconditions:
            - User is registered with BASIC subscription

        Test Steps:
            1. User clicks "Premium" button (sends callback)
               Expected: Handler processes callback
               Expected: Database updates subscription to PREMIUM
               Response: Success message (edit message)

        Post-conditions:
            - User profile has PREMIUM subscription

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        # Create user with Basic subscription
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        handler = SubscriptionHandler(services=test_service_container)

        # Setup callback query
        mock_update.message = None
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = (
            f"subscription_{SubscriptionType.PREMIUM.value}"
        )
        mock_update.callback_query.from_user = mock_telegram_user
        mock_update.effective_user = mock_telegram_user

        # Mock edit_message_text on callback_query
        mock_update.callback_query.edit_message_text = MagicMock()
        mock_update.callback_query.edit_message_text.return_value = (
            None  # awaitable if needed?
        )
        # In base_handler.edit_message it awaits query.edit_message_text
        # So it needs to be an AsyncMock or similar if actual code calls await
        # But in conftest we usually mock async methods.
        # Let's assume standard mock setup needs AsyncMock if awaited.
        # But base_handler implementation calls `await query.edit_message_text(...)`
        # So we need AsyncMock here.
        mock_update.callback_query.edit_message_text = MagicMock()
        # Since we are mocking the library, we need to ensure it behaves correctly or check if base uses async
        # Tests run with pytest-asyncio, so we used AsyncMock in conftest for message.reply_text
        # We should do same for edit_message_text if handled directly.
        # However, BaseHandler.edit_message calls it.
        # For simplicity, we just need to ensure it doesn't crash and we can verify call.

        # FIX: Ensure valid async mock for query.edit_message_text if code awaits it
        from unittest.mock import AsyncMock

        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()

        # --- ACT ---
        await handler.handle_subscription_callback(
            update=mock_update, context=mock_context
        )

        # --- ASSERT: Database update ---
        profile = await test_service_container.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert profile.subscription.subscription_type == SubscriptionType.PREMIUM

        # --- ASSERT: UI feedback ---
        mock_update.callback_query.edit_message_text.assert_called_once()
        # Check that success message mentions Premium
        args = mock_update.callback_query.edit_message_text.call_args
        assert "Premium" in args.kwargs["text"]

    async def test_access_denied_for_unregistered_user(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that unregistered users cannot access subscription.

        Preconditions:
            - User is NOT registered

        Test Steps:
            1. Unregistered user sends /subscription
               Expected: Access denied
               Response: Error message

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = SubscriptionHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/subscription")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert "not registered" in reply_text
