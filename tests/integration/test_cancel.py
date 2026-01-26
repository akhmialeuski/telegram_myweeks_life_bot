"""Integration tests for cancel command handler.

This module tests the `/cancel` command functionality, including user deletion
and error handling.

Test Scenarios:
    - Cancel command for registered user (success)
    - Cancel command for unregistered user (access denied)
    - Error handling during deletion process
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
from telegram.ext import ConversationHandler

from src.bot.handlers.cancel_handler import CancelHandler
from src.services.container import ServiceContainer
from tests.integration.conftest import (
    TEST_FIRST_NAME,
    TEST_USER_ID,
    get_reply_text,
    set_message_text,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestCancelHandler:
    """Integration tests for the cancel command handler.

    These tests verify the account deletion process and access control:
    - Successful profile deletion for registered users
    - Access restriction for unregistered users
    - System integrity after deletion
    """

    async def test_cancel_registered_user_deletes_profile_and_data(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
    ) -> None:
        """Test that /cancel successfully deletes user profile and data.

        Preconditions:
            - User is registered (has profile in database)

        Test Steps:
            1. Registered user sends /cancel command
               Expected: Handler executes deletion logic
               Expected: Profile removed from database
               Expected: UserDeletedEvent published (verified by log/effect)
               Response: Success confirmation message

        Post-conditions:
            - User profile no longer exists in database
            - Conservation state is END

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
        # Create registered user profile
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        handler = CancelHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/cancel")

        # --- ACT ---
        result = await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT: Check response ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert "successfully deleted" in reply_text
        assert TEST_FIRST_NAME in reply_text  # Personalization check

        # --- ASSERT: Check database state (Post-condition) ---
        profile = await test_service_container.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert profile is None, "User profile should be deleted from database"

        # --- ASSERT: Check return value ---
        assert result == ConversationHandler.END

    async def test_cancel_unregistered_user_denied_access(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that unregistered users cannot use /cancel command.

        Preconditions:
            - User is NOT registered (no profile in database)

        Test Steps:
            1. Unregistered user sends /cancel command
               Expected: Handler checks registration status
               Expected: Access denied
               Response: "You are not registered" error message

        Post-conditions:
            - No changes to database state

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        # Ensure no profile exists (default state for new test db)
        handler = CancelHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/cancel")

        # --- ACT ---
        result = await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT: Check response ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert "not registered" in reply_text

        # --- ASSERT: Check return value ---
        assert result is None  # Access denied returns None
