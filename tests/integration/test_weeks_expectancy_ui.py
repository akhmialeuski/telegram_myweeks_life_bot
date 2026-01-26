"""Integration tests for life expectancy UI label bug.

This module reproduces the bug where the /weeks command label
is hardcoded to (until 80 years) even if user expectancy is different.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.bot.handlers.weeks_handler import WeeksHandler
from src.services.container import ServiceContainer
from tests.integration.conftest import (
    TEST_USER_ID,
    get_reply_text,
    set_message_text,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestWeeksExpectancyUI:
    """Integration tests for /weeks command UI labels."""

    async def test_weeks_label_reflects_updated_expectancy(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that /weeks command label matches user life expectancy.

        Preconditions:
            - User is registered
            - User has life expectancy set to 100

        Test Steps:
            1. Register user and update life expectancy to 100
            2. Send /weeks command
            3. Verify response label contains "(until 100 years)"

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        user_info = MagicMock()
        user_info.id = TEST_USER_ID
        user_info.username = "test_ui"
        user_info.first_name = "UI"
        user_info.last_name = "Tester"
        user_info.language_code = "en"

        # 1. Register user
        await test_service_container.user_service.create_user_profile(
            user_info=user_info,
            birth_date=date(1990, 1, 1),
        )
        # 2. Update life expectancy to 100
        await test_service_container.user_service.update_user_settings(
            telegram_id=TEST_USER_ID, life_expectancy=100
        )

        handler = WeeksHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/weeks")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None

        # This is where the bug should manifest
        # Expected: "(until 100 years)"
        # Actual (current): "(until 80 years)"
        assert (
            "(until 100 years)" in reply_text
        ), f"Label should reflect life expectancy 100. Got: {reply_text}"
