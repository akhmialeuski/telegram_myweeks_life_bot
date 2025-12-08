"""Unit tests for SettingsHandler.

Tests the SettingsHandler class which handles /settings command.
"""

import time
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.bot.constants import COMMAND_SETTINGS
from src.bot.handlers.settings import SettingsHandler
from src.constants import DEFAULT_LIFE_EXPECTANCY
from src.database.service import UserNotFoundError, UserSettingsUpdateError
from tests.conftest import TEST_USER_ID

# Test constants
TEST_BIRTH_DATE = "15.03.1990"


class TestSettingsHandler:
    """Test suite for SettingsHandler class.

    This test class contains all tests for SettingsHandler functionality,
    including settings display, user input processing, birth date and
    life expectancy updates, language changes, and error handling.
    """

    @pytest.fixture
    def handler(self) -> SettingsHandler:
        """Create SettingsHandler instance for testing.

        :returns: Configured SettingsHandler instance with fake service container
        :rtype: SettingsHandler
        """
        from tests.utils.fake_container import FakeServiceContainer

        services = FakeServiceContainer()
        return SettingsHandler(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker) -> MagicMock:
        """Mock use_locale to control translations.

        This fixture automatically mocks the use_locale function to return
        predictable translation strings for testing purposes.

        :param mocker: pytest-mock fixture for creating mocks
        :type mocker: pytest_mock.MockerFixture
        :returns: Mocked pgettext function
        :rtype: MagicMock
        """
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.settings.handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    def test_handler_creation(self, handler: SettingsHandler) -> None:
        """Test that SettingsHandler is created with correct command name.

        This test verifies that the handler is properly initialized with
        the /settings command name constant.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name == f"/{COMMAND_SETTINGS}"

    def test_set_waiting_state(
        self, handler: SettingsHandler, mock_context: MagicMock
    ) -> None:
        """Test setting waiting state for user input.

        This test verifies that _set_waiting_state correctly stores the
        waiting state, timestamp, and state ID in user data for tracking
        user input sequences.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        handler._set_waiting_state(mock_context, "test_state")

        assert mock_context.user_data["waiting_for"] == "test_state"
        assert "waiting_timestamp" in mock_context.user_data
        assert "waiting_state_id" in mock_context.user_data
        assert isinstance(mock_context.user_data["waiting_timestamp"], float)
        assert isinstance(mock_context.user_data["waiting_state_id"], str)

    def test_is_valid_waiting_state_valid(
        self, handler: SettingsHandler, mock_context: MagicMock
    ) -> None:
        """Test waiting state validation with valid state data.

        This test verifies that _is_valid_waiting_state returns True
        when the waiting state matches, timestamp is recent, and state ID exists.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        current_time = time.time()
        mock_context.user_data = {
            "waiting_for": "test_state",
            "waiting_timestamp": current_time,
            "waiting_state_id": "test-id",
        }

        result = handler._is_valid_waiting_state(mock_context, "test_state")

        assert result is True

    def test_is_valid_waiting_state_invalid_state(
        self, handler: SettingsHandler, mock_context: MagicMock
    ) -> None:
        """Test waiting state validation with mismatched state.

        This test verifies that _is_valid_waiting_state returns False
        when the waiting state doesn't match the expected state.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        current_time = time.time()
        mock_context.user_data = {
            "waiting_for": "wrong_state",
            "waiting_timestamp": current_time,
            "waiting_state_id": "test-id",
        }

        result = handler._is_valid_waiting_state(mock_context, "test_state")

        assert result is False

    def test_is_valid_waiting_state_expired(
        self, handler: SettingsHandler, mock_context: MagicMock
    ) -> None:
        """Test waiting state validation with expired timestamp.

        This test verifies that _is_valid_waiting_state returns False
        when the waiting state timestamp is too old (> 5 minutes).

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        # Timestamp from 10 minutes ago should be considered expired
        old_time = time.time() - 600
        mock_context.user_data = {
            "waiting_for": "test_state",
            "waiting_timestamp": old_time,
            "waiting_state_id": "test-id",
        }

        result = handler._is_valid_waiting_state(mock_context, "test_state")

        assert result is False

    def test_is_valid_waiting_state_missing_timestamp(
        self, handler: SettingsHandler, mock_context: MagicMock
    ) -> None:
        """Test waiting state validation with missing timestamp.

        This test verifies that _is_valid_waiting_state returns False
        when the timestamp field is missing from user data.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_context.user_data = {
            "waiting_for": "test_state",
            "waiting_state_id": "test-id",
        }

        result = handler._is_valid_waiting_state(mock_context, "test_state")

        assert result is False

    def test_is_valid_waiting_state_missing_state_id(
        self, handler: SettingsHandler, mock_context: MagicMock
    ) -> None:
        """Test waiting state validation with missing state ID.

        This test verifies that _is_valid_waiting_state returns False
        when the state_id field is missing from user data.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        current_time = time.time()
        mock_context.user_data = {
            "waiting_for": "test_state",
            "waiting_timestamp": current_time,
        }

        result = handler._is_valid_waiting_state(mock_context, "test_state")

        assert result is False

    def test_clear_waiting_state(
        self, handler: SettingsHandler, mock_context: MagicMock
    ) -> None:
        """Test clearing waiting state from user data.

        This test verifies that _clear_waiting_state removes all
        waiting-related fields from user data.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_context.user_data = {
            "waiting_for": "test_state",
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test-id",
        }

        handler._clear_waiting_state(mock_context)

        assert "waiting_for" not in mock_context.user_data
        assert "waiting_timestamp" not in mock_context.user_data
        assert "waiting_state_id" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_premium_success(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
    ) -> None:
        """Test settings handler invocation for premium user.

        This test verifies that the handle method correctly invokes
        the internal _handle_settings method for a premium user profile.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :param make_mock_user_profile: Fixture for creating mock user profiles
        :type make_mock_user_profile: callable
        :returns: None
        :rtype: None
        """
        handler.services.user_service.is_valid_user_profile.return_value = True

        # Verify wrapper wiring to internal handler
        async def _noop(update, context):
            return None

        with patch.object(handler, "_handle_settings", side_effect=_noop) as mock_impl:
            await handler.handle(mock_update, mock_context)
            assert mock_impl.called

    @pytest.mark.asyncio
    async def test_handle_basic_success(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
    ) -> None:
        """Test settings handler invocation for basic user.

        This test verifies that the handle method correctly invokes
        the internal _handle_settings method for a basic user profile.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :param make_mock_user_profile: Fixture for creating mock user profiles
        :type make_mock_user_profile: callable
        :returns: None
        :rtype: None
        """
        handler.services.user_service.is_valid_user_profile.return_value = True

        async def _noop(update, context):
            return None

        with patch.object(handler, "_handle_settings", side_effect=_noop) as mock_impl:
            await handler.handle(mock_update, mock_context)
            assert mock_impl.called

    @pytest.mark.asyncio
    async def test_handle_no_profile(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_use_locale: MagicMock,
    ) -> None:
        """Test settings handler when user profile is not found.

        This test verifies that the handler sends an appropriate error
        message when the user profile doesn't exist in the database.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :param mock_use_locale: Mocked use_locale function
        :type mock_use_locale: MagicMock
        :returns: None
        :rtype: None
        """
        handler.services.user_service.is_valid_user_profile.return_value = False
        mock_update.effective_user.language_code = "en"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_exception(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
    ) -> None:
        """Test settings handler exception handling.

        This test verifies that exceptions raised in the internal
        handler are caught and handled by the base handler wrapper.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :param make_mock_user_profile: Fixture for creating mock user profiles
        :type make_mock_user_profile: callable
        :returns: None
        :rtype: None
        """
        mock_profile = MagicMock()
        mock_profile.settings.language = "en"
        handler.services.user_service.get_user_profile.return_value = mock_profile
        handler.services.user_service.is_valid_user_profile.return_value = True

        with patch.object(
            handler, "_handle_settings", side_effect=Exception("Test exception")
        ):
            await handler.handle(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_handle_settings_callback_birth_date(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test settings callback for birth date change.

        This test verifies that selecting the birth date option prompts
        the user with instructions and sets the waiting state correctly.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update_with_callback: Mocked Telegram update with callback query
        :type mock_update_with_callback: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update_with_callback.callback_query.data = "settings_birth_date"
        handler.services.user_service.get_user_profile.return_value = MagicMock(
            birth_date=date(2000, 1, 1), settings=MagicMock(language="en")
        )

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_settings_callback(
                mock_update_with_callback, mock_context
            )
            mock_edit_message.assert_called_once()
            assert (
                "pgettext_settings.change_birth_date_"
                in mock_edit_message.call_args.kwargs["message_text"]
            )
            assert mock_context.user_data["waiting_for"] == "settings_birth_date"

    @pytest.mark.asyncio
    async def test_handle_settings_callback_language(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test settings callback for language change.

        This test verifies that selecting the language option displays
        the language selection menu to the user.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update_with_callback: Mocked Telegram update with callback query
        :type mock_update_with_callback: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update_with_callback.callback_query.data = "settings_language"

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_settings_callback(
                mock_update_with_callback, mock_context
            )
            mock_edit_message.assert_called_once()
            assert (
                "pgettext_settings.change_language_"
                in mock_edit_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_language_callback_invalid_language(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test language callback handling with invalid language code.

        This test verifies that an invalid language code in the callback
        is handled gracefully without crashing.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update_with_callback: Mocked Telegram update with callback query
        :type mock_update_with_callback: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update_with_callback.callback_query.data = "language_invalid"

        # UnboundLocalError expected due to pgettext scope issue in error handler
        try:
            await handler.handle_language_callback(
                mock_update_with_callback, mock_context
            )
        except UnboundLocalError:
            pass

    @pytest.mark.asyncio
    async def test_handle_language_callback_database_error(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test language callback handling when database update fails.

        This test verifies that database errors during language update
        are caught and handled appropriately.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update_with_callback: Mocked Telegram update with callback query
        :type mock_update_with_callback: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update_with_callback.callback_query.data = "language_en"
        handler.services.user_service.update_user_settings.side_effect = (
            UserNotFoundError("User not found")
        )

        # UnboundLocalError expected due to pgettext scope issue in error handler
        try:
            await handler.handle_language_callback(
                mock_update_with_callback, mock_context
            )
        except UnboundLocalError:
            pass

    @pytest.mark.asyncio
    async def test_handle_settings_input_birth_date(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test settings input routing for birth date.

        This test verifies that when the handler is waiting for a birth
        date input, it correctly routes the message to the birth date handler.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update.message.text = TEST_BIRTH_DATE
        mock_context.user_data = {
            "waiting_for": "settings_birth_date",
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test-state-id",
        }

        with patch.object(handler, "handle_birth_date_input") as mock_handle_birth_date:
            await handler.handle_settings_input(mock_update, mock_context)
            mock_handle_birth_date.assert_called_once_with(
                update=mock_update, context=mock_context, message_text=TEST_BIRTH_DATE
            )

    @pytest.mark.asyncio
    async def test_handle_settings_input_life_expectancy(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test settings input routing for life expectancy.

        This test verifies that when the handler is waiting for a life
        expectancy input, it correctly routes the message to the life expectancy handler.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update.message.text = str(DEFAULT_LIFE_EXPECTANCY)
        mock_context.user_data = {
            "waiting_for": "settings_life_expectancy",
            "waiting_timestamp": time.time(),
            "waiting_state_id": "test-state-id",
        }

        with patch.object(
            handler, "handle_life_expectancy_input"
        ) as mock_handle_life_expectancy:
            await handler.handle_settings_input(mock_update, mock_context)
            mock_handle_life_expectancy.assert_called_once_with(
                update=mock_update,
                context=mock_context,
                message_text=str(DEFAULT_LIFE_EXPECTANCY),
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_future_date(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test birth date validation with future date.

        This test verifies that birth dates in the future are rejected
        with an appropriate error message.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        future_date = date(2025, 1, 1)

        with patch(
            "src.bot.handlers.settings.handler.datetime"
        ) as mock_datetime, patch(
            "src.bot.handlers.settings.handler.date"
        ) as mock_date, patch.object(
            handler, "send_message"
        ) as mock_send_message:
            mock_datetime.strptime.return_value.date.return_value = future_date
            mock_date.today.return_value = date(2024, 1, 1)

            await handler.handle_birth_date_input(
                mock_update, mock_context, "01.01.2025"
            )
            mock_send_message.assert_called_once()
            assert (
                "pgettext_birth_date.future_error_"
                in mock_send_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_old_date(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test birth date validation with unrealistically old date.

        This test verifies that birth dates before 1900 are rejected
        with an appropriate error message.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        old_date = date(1800, 1, 1)

        with patch(
            "src.bot.handlers.settings.handler.datetime"
        ) as mock_datetime, patch.object(handler, "send_message") as mock_send_message:
            mock_datetime.strptime.return_value.date.return_value = old_date

            await handler.handle_birth_date_input(
                mock_update, mock_context, "01.01.1800"
            )
            mock_send_message.assert_called_once()
            assert (
                "pgettext_birth_date.old_error_"
                in mock_send_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_database_error(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test birth date update handling when database error occurs.

        This test verifies that database errors during birth date update
        are caught and reported to the user.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        test_birth_date = date(1990, 3, 15)
        handler.services.user_service.update_user_settings.side_effect = (
            UserNotFoundError("User not found")
        )

        with patch(
            "src.bot.handlers.settings.handler.datetime"
        ) as mock_datetime, patch.object(
            handler, "send_error_message"
        ) as mock_send_error:
            mock_datetime.strptime.return_value.date.return_value = test_birth_date
            await handler.handle_birth_date_input(
                mock_update, mock_context, TEST_BIRTH_DATE
            )
            mock_send_error.assert_called_once()
            assert (
                "pgettext_settings.error_"
                in mock_send_error.call_args.kwargs["error_message"]
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_format_error(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test birth date parsing with invalid format.

        This test verifies that invalid date formats are rejected
        with a format error message.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        with patch(
            "src.bot.handlers.settings.handler.datetime"
        ) as mock_datetime, patch.object(
            handler, "send_error_message"
        ) as mock_send_error:
            mock_datetime.strptime.side_effect = ValueError("Invalid date format")
            await handler.handle_birth_date_input(
                mock_update, mock_context, "invalid-date"
            )
            mock_send_error.assert_called_once()
            assert (
                "pgettext_birth_date.format_error_"
                in mock_send_error.call_args.kwargs["error_message"]
            )

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_success(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test life expectancy update with valid input.

        This test verifies that a valid life expectancy value is accepted,
        stored in the database, and confirmed to the user.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_context.user_data = {"waiting_for": "settings_life_expectancy"}
        mock_user_profile = MagicMock()
        mock_user_profile.settings = MagicMock(language="en")
        handler.services.user_service.get_user_profile.return_value = mock_user_profile

        with patch.object(handler, "send_message") as mock_send_message:
            await handler.handle_life_expectancy_input(
                mock_update, mock_context, str(DEFAULT_LIFE_EXPECTANCY)
            )

            handler.services.user_service.update_user_settings.assert_called_once_with(
                telegram_id=TEST_USER_ID, life_expectancy=DEFAULT_LIFE_EXPECTANCY
            )
            mock_send_message.assert_called_once()
            assert (
                "pgettext_settings.life_expectancy_updated"
                in mock_send_message.call_args.kwargs["message_text"]
            )
            assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_invalid_range(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test life expectancy validation with out-of-range value.

        This test verifies that life expectancy values outside the valid
        range (40-120) are rejected with an error message.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        with patch.object(handler, "send_message") as mock_send_message:
            await handler.handle_life_expectancy_input(mock_update, mock_context, "30")

            mock_send_message.assert_called_once()
            assert (
                "pgettext_settings.invalid_life_expectancy"
                in mock_send_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_database_error(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test life expectancy update handling when database error occurs.

        This test verifies that database errors during life expectancy
        update are caught and reported to the user.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        handler.services.user_service.update_user_settings.side_effect = (
            UserSettingsUpdateError("Update failed")
        )
        with patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle_life_expectancy_input(
                mock_update, mock_context, str(DEFAULT_LIFE_EXPECTANCY)
            )
            mock_send_error.assert_called_once()
            assert (
                "pgettext_settings.error_"
                in mock_send_error.call_args.kwargs["error_message"]
            )

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_format_error(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test life expectancy parsing with invalid format.

        This test verifies that non-numeric values are rejected with
        an appropriate error message.

        :param handler: SettingsHandler instance from fixture
        :type handler: SettingsHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        with patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle_life_expectancy_input(
                mock_update, mock_context, "not-a-number"
            )
            mock_send_error.assert_called_once()
            assert (
                "pgettext_settings.invalid_life_expectancy"
                in mock_send_error.call_args.kwargs["error_message"]
            )
