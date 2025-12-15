"""Unit tests for LifeExpectancyHandler.

Tests the LifeExpectancyHandler class which handles life expectancy settings.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.bot.conversations.states import ConversationState
from src.bot.handlers.settings.life_expectancy_handler import LifeExpectancyHandler
from src.database.service import UserNotFoundError
from tests.conftest import TEST_USER_ID


class TestLifeExpectancyHandler:
    """Test suite for LifeExpectancyHandler class."""

    @pytest.fixture
    def handler(self) -> LifeExpectancyHandler:
        """Create LifeExpectancyHandler instance for testing.

        :returns: Configured LifeExpectancyHandler instance
        :rtype: LifeExpectancyHandler
        """
        from tests.utils.fake_container import FakeServiceContainer

        services = FakeServiceContainer()
        return LifeExpectancyHandler(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker) -> MagicMock:
        """Mock use_locale to control translations.

        :param mocker: pytest-mock fixture
        :type mocker: pytest_mock.MockerFixture
        :returns: Mocked pgettext function
        :rtype: MagicMock
        """
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.settings.life_expectancy_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    @pytest.mark.asyncio
    async def test_handle_callback_success(
        self,
        handler: LifeExpectancyHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test callback handling for life expectancy change.

        :param handler: LifeExpectancyHandler instance
        :type handler: LifeExpectancyHandler
        :param mock_update_with_callback: Mocked update
        :type mock_update_with_callback: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        mock_update_with_callback.callback_query.data = "settings_life_expectancy"

        mock_profile = MagicMock()
        mock_profile.settings.language = "en"
        mock_profile.settings.life_expectancy = 80
        handler.services.user_service.get_user_profile.return_value = mock_profile

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_callback(mock_update_with_callback, mock_context)

            mock_edit_message.assert_called_once()
            assert (
                "pgettext_settings.change_life_expectancy_"
                in mock_edit_message.call_args.kwargs["message_text"]
            )

            # Verify waiting state set
            assert (
                mock_context.user_data["waiting_for"]
                == ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY
            )

    @pytest.mark.asyncio
    async def test_handle_input_success(
        self,
        handler: LifeExpectancyHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test successful life expectancy update.

        :param handler: LifeExpectancyHandler instance
        :type handler: LifeExpectancyHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        from src.events.domain_events import UserSettingsChangedEvent
        from src.services.validation_service import ValidationResult

        mock_update.message.text = "85"
        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        mock_profile = MagicMock()
        mock_profile.settings.language = "en"
        mock_profile.settings.life_expectancy = 80
        handler.services.user_service.get_user_profile.return_value = mock_profile

        handler._validation_service.validate_life_expectancy = MagicMock(
            return_value=ValidationResult.success(value=85)
        )

        with patch.object(handler, "send_message") as mock_send_message:
            await handler.handle_input(mock_update, mock_context)

            # Verify DB update
            handler.services.user_service.update_user_settings.assert_called_once_with(
                telegram_id=TEST_USER_ID, life_expectancy=85
            )

            # Verify event published
            handler.services.event_bus.publish.assert_called_once()
            call_args = handler.services.event_bus.publish.call_args
            event = call_args[0][0]
            assert isinstance(event, UserSettingsChangedEvent)
            assert event.user_id == TEST_USER_ID
            assert event.new_value == 85
            assert event.setting_name == "life_expectancy"

            # Verify success message and state clearing
            mock_send_message.assert_called_once()
            assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_input_invalid_range(
        self,
        handler: LifeExpectancyHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test validation failure for out-of-range value.

        :param handler: LifeExpectancyHandler instance
        :type handler: LifeExpectancyHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        from src.services.validation_service import (
            ERROR_INVALID_NUMBER,
            ValidationResult,
        )

        mock_update.message.text = "150"
        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        handler._validation_service.validate_life_expectancy = MagicMock(
            return_value=ValidationResult.failure(error_key=ERROR_INVALID_NUMBER)
        )

        with patch.object(handler, "send_message") as mock_send_message:
            await handler.handle_input(mock_update, mock_context)

            mock_send_message.assert_called_once()
            # The current implementation uses generic "invalid_life_expectancy" message on error
            assert (
                "pgettext_settings.invalid_life_expectancy_"
                in mock_send_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_input_db_error(
        self,
        handler: LifeExpectancyHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of database error during update.

        :param handler: LifeExpectancyHandler instance
        :type handler: LifeExpectancyHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        from src.services.validation_service import ValidationResult

        mock_update.message.text = "85"
        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        handler._validation_service.validate_life_expectancy = MagicMock(
            return_value=ValidationResult.success(value=85)
        )
        handler.services.user_service.update_user_settings.side_effect = (
            UserNotFoundError("User not found")
        )

        with patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle_input(mock_update, mock_context)
            mock_send_error.assert_called_once()
