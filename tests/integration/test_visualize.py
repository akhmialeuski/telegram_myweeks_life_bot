"""Integration tests for visualize command handler.

This module tests the `/visualize` command functionality, primarily focusing
on access control and successful invocation of generating logic.

Test Scenarios:
    - Generate visualization (registered user)
    - Access denied (unregistered user)
"""

from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from src.bot.handlers.visualize_handler import VisualizeHandler
from src.services.container import ServiceContainer
from tests.integration.conftest import (
    get_reply_text,
    set_message_text,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestVisualizeHandler:
    """Integration tests for visualization handler.

    These tests verify that users can request their life visualization:
    - Verifies image generation is triggered
    - Verifies access control
    """

    @patch("src.bot.handlers.visualize_handler.generate_visualization")
    async def test_visualize_registered_user_success(
        self,
        mock_generate_visualization,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
    ) -> None:
        """Test that registered users receive the visualization image.

        Preconditions:
            - User is registered
            - User sends /visualize command

        Test Steps:
            1. Registered user sends /visualize
               Expected: Bot generates and sends visualization image
               Response: Photo with correct caption

        Post-conditions:
            - generate_visualization called once
            - reply_photo called with correct arguments

        :param mock_generate_visualization: Mocked visualization function
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
        # Setup mock return value
        mock_img = BytesIO(b"fake_image_data")
        mock_img.name = "life_weeks.png"
        mock_generate_visualization.return_value = mock_img

        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        handler = VisualizeHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/visualize")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_generate_visualization.assert_called_once()
        mock_update.message.reply_photo.assert_called_once()

        # Verify photo arg is our mock
        args = mock_update.message.reply_photo.call_args
        assert args.kwargs["photo"] == mock_img

        # Verify caption contains statistics
        caption = args.kwargs.get("caption")
        assert caption is not None
        assert "Visualization" in caption
        assert "Weeks lived" in caption

    async def test_access_denied_for_unregistered_user(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that unregistered users cannot access visualize.

        Preconditions:
            - User is NOT registered

        Test Steps:
            1. Unregistered user sends /visualize
               Expected: Access denied
               Response: Error message about registration

        Post-conditions:
            - No visualization generated
            - User receives registration prompt

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = VisualizeHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/visualize")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert "not registered" in reply_text
