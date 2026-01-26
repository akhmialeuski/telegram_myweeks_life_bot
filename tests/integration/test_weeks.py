"""Integration tests for weeks command handler.

This module tests the `/weeks` command functionality, ensuring valid
statistics calculation and display.

Test Scenarios:
    - View weeks statistics (registered user)
    - Access denied (unregistered user)
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.bot.handlers.weeks_handler import WeeksHandler
from src.services.container import ServiceContainer
from tests.integration.conftest import (
    get_reply_text,
    set_message_text,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestWeeksHandler:
    """Integration tests for weeks statistics handler.

    These tests verify the core statistics display functionality:
    - Correct data calculation and display
    - Access control
    """

    async def test_weeks_registered_user_success(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
    ) -> None:
        """Test that registered users can view weeks statistics.

        Preconditions:
            - User is registered

        Test Steps:
            1. Registered user sends /weeks
               Expected: Handler calculates and shows stats
               Response: Message with Age, Weeks lived, etc.

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
        # Create user
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        handler = WeeksHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/weeks")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)

        assert reply_text is not None
        assert "Age:" in reply_text
        assert "Weeks lived:" in reply_text
        assert "Life progress:" in reply_text

    async def test_access_denied_for_unregistered_user(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that unregistered users cannot access weeks stats.

        Preconditions:
            - User is NOT registered

        Test Steps:
            1. Unregistered user sends /weeks
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
        handler = WeeksHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/weeks")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert "not registered" in reply_text
