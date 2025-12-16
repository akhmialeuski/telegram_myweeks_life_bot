"""Unit tests for BirthDateHandler.

Tests the BirthDateHandler class which handles birth date settings.
"""

import time
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.bot.conversations.states import ConversationState
from src.bot.handlers.settings.birth_date_handler import BirthDateHandler
from src.database.service import UserNotFoundError
from tests.conftest import TEST_USER_ID

# Test constants
TEST_BIRTH_DATE = "15.03.1990"


class TestBirthDateHandler:
    """Test suite for BirthDateHandler class."""

    @pytest.fixture
    def handler(self) -> BirthDateHandler:
        """Create BirthDateHandler instance for testing.

        :returns: Configured BirthDateHandler instance
        :rtype: BirthDateHandler
        """
        from tests.utils.fake_container import FakeServiceContainer

        services = FakeServiceContainer()
        return BirthDateHandler(services)

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
            "src.bot.handlers.settings.birth_date_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    @pytest.mark.asyncio
    async def test_handle_callback_success(
        self,
        handler: BirthDateHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test callback handling for birth date change.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update_with_callback: Mocked update with callback
        :type mock_update_with_callback: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        mock_update_with_callback.callback_query.data = "settings_birth_date"

        # Mock user profile locally instead of relying on context
        mock_profile = MagicMock(
            birth_date=date(2000, 1, 1), settings=MagicMock(language="en")
        )
        handler.services.user_service.get_user_profile.return_value = mock_profile

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_callback(mock_update_with_callback, mock_context)

            mock_edit_message.assert_called_once()
            assert (
                "pgettext_settings.change_birth_date_"
                in mock_edit_message.call_args.kwargs["message_text"]
            )

            # Verify state was set
            assert (
                mock_context.user_data["waiting_for"]
                == ConversationState.AWAITING_SETTINGS_BIRTH_DATE
            )

    @pytest.mark.asyncio
    async def test_handle_input_future_date(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test birth date validation with future date.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        from src.core.exceptions import ValidationError as CoreValidationError
        from src.services.validation_service import ERROR_DATE_IN_FUTURE

        # Mock ValidationService
        handler._validation_service.validate_birth_date = MagicMock(
            side_effect=CoreValidationError(
                message="Future date error", error_key=ERROR_DATE_IN_FUTURE
            )
        )

        mock_update.message.text = "2099-01-01"
        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        with patch.object(handler._persistence, "is_state_valid", return_value=True):
            with patch.object(handler, "send_message") as mock_send_message:
                await handler.handle_input(mock_update, mock_context)

            mock_send_message.assert_called_once()
            assert (
                "pgettext_birth_date.future_error_"
                in mock_send_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_input_invalid_format_error(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test birth date validation with invalid format.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        from src.core.exceptions import ValidationError as CoreValidationError
        from src.services.validation_service import ERROR_INVALID_DATE_FORMAT

        handler._validation_service.validate_birth_date = MagicMock(
            side_effect=CoreValidationError(
                message="Invalid date format", error_key=ERROR_INVALID_DATE_FORMAT
            )
        )

        mock_update.message.text = "invalid-date"
        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        with patch.object(handler._persistence, "is_state_valid", return_value=True):
            with patch.object(handler, "send_message") as mock_send_message:
                await handler.handle_input(mock_update, mock_context)

                mock_send_message.assert_called_once()
                assert (
                    "pgettext_birth_date.format_error"
                    in mock_send_message.call_args.kwargs["message_text"]
                )

    @pytest.mark.asyncio
    async def test_handle_input_old_date(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test birth date validation with too old date.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        from src.core.exceptions import ValidationError as CoreValidationError
        from src.services.validation_service import ERROR_DATE_TOO_OLD

        handler._validation_service.validate_birth_date = MagicMock(
            side_effect=CoreValidationError(
                message="Old date error", error_key=ERROR_DATE_TOO_OLD
            )
        )

        mock_update.message.text = "01.01.1800"
        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        with patch.object(handler._persistence, "is_state_valid", return_value=True):
            with patch.object(handler, "send_message") as mock_send_message:
                await handler.handle_input(mock_update, mock_context)

            mock_send_message.assert_called_once()
            assert (
                "pgettext_birth_date.old_error_"
                in mock_send_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_input_success(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test successful birth date update.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        from src.events.domain_events import UserSettingsChangedEvent

        test_date = date(1990, 3, 15)
        mock_update.message.text = TEST_BIRTH_DATE
        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        mock_profile = MagicMock(
            birth_date=date(2000, 1, 1),
            settings=MagicMock(
                language="en", life_expectancy=80, birth_date=date(2000, 1, 1)
            ),
        )
        handler.services.user_service.get_user_profile.return_value = mock_profile

        handler._validation_service.validate_birth_date = MagicMock(
            return_value=test_date
        )

        with patch.object(handler, "send_message") as mock_send_message:
            await handler.handle_input(mock_update, mock_context)

            # Verify DB update
            handler.services.user_service.update_user_settings.assert_called_once_with(
                telegram_id=TEST_USER_ID, birth_date=test_date
            )

            # Verify event published
            handler.services.event_bus.publish.assert_called_once()
            call_args = handler.services.event_bus.publish.call_args
            event = call_args[0][0]
            assert isinstance(event, UserSettingsChangedEvent)
            assert event.user_id == TEST_USER_ID
            assert event.new_value == test_date

            # Verify success message and state clearing
            mock_send_message.assert_called_once()
            assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_input_database_error(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of database errors during update.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        mock_update.message.text = TEST_BIRTH_DATE
        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        handler._validation_service.validate_birth_date = MagicMock(
            return_value=date(1990, 1, 1)
        )
        handler.services.user_service.update_user_settings.side_effect = (
            UserNotFoundError("User not found")
        )

        with patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle_input(mock_update, mock_context)
            mock_send_error.assert_called_once()
            assert (
                "pgettext_settings.error_"
                in mock_send_error.call_args.kwargs["error_message"]
            )

    @pytest.mark.asyncio
    async def test_handle_input_settings_update_error(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of UserSettingsUpdateError during update.

        This test verifies that UserSettingsUpdateError is properly caught
        and an appropriate error message is sent to the user.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        from src.database.service import UserSettingsUpdateError

        mock_update.message.text = TEST_BIRTH_DATE
        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        handler._validation_service.validate_birth_date = MagicMock(
            return_value=date(1990, 1, 1)
        )
        handler.services.user_service.update_user_settings.side_effect = (
            UserSettingsUpdateError("Failed to update settings")
        )

        with patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle_input(mock_update, mock_context)
            mock_send_error.assert_called_once()
            assert (
                "pgettext_settings.error_"
                in mock_send_error.call_args.kwargs["error_message"]
            )

    @pytest.mark.asyncio
    async def test_handle_returns_none(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that handle method returns None.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        result = await handler.handle(mock_update, mock_context)
        assert result is None

    @pytest.mark.asyncio
    async def test_handle_input_invalid_waiting_state(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of invalid waiting state.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        mock_context.user_data = {"waiting_for": "WRONG_STATE"}

        with patch.object(handler, "_clear_waiting_state") as mock_clear:
            await handler.handle_input(mock_update, mock_context)
            mock_clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_input_generic_exception(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of generic exception during processing.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        # Set valid state to pass first check
        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        # Mock validation service to raise exception
        handler._validation_service.validate_birth_date = MagicMock(
            side_effect=Exception("Unexpected error")
        )

        with patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle_input(mock_update, mock_context)
            mock_send_error.assert_called_once()
            assert (
                "pgettext_birth_date.format_error_"
                in mock_send_error.call_args.kwargs["error_message"]
            )

    @pytest.mark.asyncio
    async def test_handle_input_unknown_error(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of unknown validation error.

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        from src.core.exceptions import ValidationError as CoreValidationError

        mock_context.user_data = {
            "waiting_for": ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test_id",
        }

        handler._validation_service.validate_birth_date = MagicMock(
            side_effect=CoreValidationError(
                message="Unknown error", error_key="unknown_error_key"
            )
        )

        with patch.object(handler, "send_message") as mock_send_message:
            await handler.handle_input(mock_update, mock_context)
            mock_send_message.assert_called_once()
            assert (
                "pgettext_birth_date.general_error_"
                in mock_send_message.call_args.kwargs["message_text"]
            )
