"""Unit tests for timezone settings handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Message, Update
from telegram.ext import ContextTypes

from src.bot.conversations.states import ConversationState
from src.bot.handlers.settings.timezone_handler import TimezoneHandler
from src.core.dtos import UserProfileDTO, UserSettingsDTO
from src.database.service import UserSettingsUpdateError
from src.enums import NotificationFrequency
from src.events.domain_events import UserSettingsChangedEvent
from tests.unit.utils.fake_container import FakeServiceContainer


class TestTimezoneHandler:
    """Unit test suite for timezone handler logic."""

    @pytest.fixture
    def handler(self) -> TimezoneHandler:
        """Create a handler instance with fake services.

        :returns: Configured handler instance
        :rtype: TimezoneHandler
        """
        container = FakeServiceContainer()
        # Mock the service methods
        container.user_service.update_user_settings = AsyncMock()
        container.user_service.get_user_profile = AsyncMock(
            return_value=UserProfileDTO(
                telegram_id=123,
                username=None,
                first_name=None,
                last_name=None,
                created_at=None,
                settings=UserSettingsDTO(
                    birth_date=None,
                    notifications=True,
                    notifications_day=None,
                    notifications_time=None,
                    notification_frequency=NotificationFrequency.DAILY,
                    notifications_month_day=None,
                    life_expectancy=None,
                    timezone="UTC",
                    language="en",
                ),
                subscription=None,
            )
        )
        container.event_bus.publish = AsyncMock()
        return TimezoneHandler(services=container)

    @pytest.fixture
    def update_mock(self) -> MagicMock:
        """Create a mock Update object.

        :returns: Mock Update instance
        :rtype: MagicMock
        """
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(id=123, language_code="en")
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def context_mock(self) -> MagicMock:
        """Create a mock ContextTypes.DEFAULT_TYPE object.

        :returns: Mock context instance
        :rtype: MagicMock
        """
        return MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_handle_returns_none(
        self, handler: TimezoneHandler, update_mock: MagicMock, context_mock: MagicMock
    ) -> None:
        """Test that handle method returns None."""
        # We need to mock _wrap_with_registration logic since handle uses it?
        # Actually TimezoneHandler.handle just returns None directly.
        assert await handler.handle(update=update_mock, context=context_mock) is None

    @pytest.mark.asyncio
    @patch("src.bot.handlers.settings.timezone_handler.use_locale")
    @patch("src.bot.handlers.settings.timezone_handler.get_timezone_keyboard")
    async def test_handle_callback_shows_keyboard(
        self,
        mock_get_keyboard: MagicMock,
        mock_use_locale: MagicMock,
        handler: TimezoneHandler,
        update_mock: MagicMock,
        context_mock: MagicMock,
    ) -> None:
        """Test that handle_callback shows the timezone keyboard."""
        # Setup mocks
        mock_pgettext = MagicMock(return_value="Translated message")
        mock_use_locale.return_value = (None, None, mock_pgettext)
        mock_get_keyboard.return_value = "Keyboard"

        # We need to patch _extract_command_context
        handler._extract_command_context = AsyncMock()
        handler._extract_command_context.return_value.language = "en"
        handler.edit_message = AsyncMock()

        await handler.handle_callback(update_mock, context_mock)

        # Verify
        update_mock.callback_query.answer.assert_called_once()
        handler.edit_message.assert_called_once_with(
            query=update_mock.callback_query,
            message_text="Translated message",
            reply_markup="Keyboard",
        )

    @pytest.mark.asyncio
    @patch("src.bot.handlers.settings.timezone_handler.use_locale")
    async def test_handle_selection_callback_other_timezone(
        self,
        mock_use_locale: MagicMock,
        handler: TimezoneHandler,
        update_mock: MagicMock,
        context_mock: MagicMock,
    ) -> None:
        """Test that selecting 'Other' timezone transitions to text input state."""
        # Setup mocks
        mock_pgettext = MagicMock(return_value="Enter timezone")
        mock_use_locale.return_value = (None, None, mock_pgettext)

        update_mock.callback_query.data = "timezone_other"

        handler._extract_command_context = AsyncMock()
        handler._extract_command_context.return_value.user_id = 123
        handler._extract_command_context.return_value.language = "en"
        handler.edit_message = AsyncMock()

        result = await handler.handle_selection_callback(update_mock, context_mock)

        # Verify
        assert result == ConversationState.AWAITING_SETTINGS_TIMEZONE.value
        handler.edit_message.assert_called_once_with(
            query=update_mock.callback_query,
            message_text="Enter timezone",
        )

    @pytest.mark.asyncio
    @patch("src.bot.handlers.settings.timezone_handler.use_locale")
    async def test_handle_selection_callback_valid_timezone(
        self,
        mock_use_locale: MagicMock,
        handler: TimezoneHandler,
        update_mock: MagicMock,
        context_mock: MagicMock,
    ) -> None:
        """Test that selecting a valid timezone updates settings and publishes event."""
        # Setup mocks
        mock_pgettext = MagicMock(return_value="Success")
        mock_use_locale.return_value = (None, None, mock_pgettext)

        update_mock.callback_query.data = "timezone_Europe/London"

        handler._extract_command_context = AsyncMock()
        handler._extract_command_context.return_value.user_id = 123
        handler._extract_command_context.return_value.language = "en"
        handler.edit_message = AsyncMock()

        result = await handler.handle_selection_callback(update_mock, context_mock)

        # Verify
        assert result is None
        handler.services.user_service.update_user_settings.assert_called_once_with(
            telegram_id=123, timezone="Europe/London"
        )
        handler.services.event_bus.publish.assert_called_once()
        event = handler.services.event_bus.publish.call_args[0][0]
        assert isinstance(event, UserSettingsChangedEvent)
        assert event.setting_name == "timezone"
        assert event.new_value == "Europe/London"

        handler.edit_message.assert_called_once_with(
            query=update_mock.callback_query,
            message_text="Success",
        )

    @pytest.mark.asyncio
    @patch("src.bot.handlers.settings.timezone_handler.use_locale")
    async def test_handle_selection_callback_error(
        self,
        mock_use_locale: MagicMock,
        handler: TimezoneHandler,
        update_mock: MagicMock,
        context_mock: MagicMock,
    ) -> None:
        """Test error handling during timezone selection."""
        # Setup mocks
        mock_pgettext = MagicMock(return_value="Error")
        mock_use_locale.return_value = (None, None, mock_pgettext)

        update_mock.callback_query.data = "timezone_Europe/London"

        handler._extract_command_context = AsyncMock()
        handler._extract_command_context.return_value.user_id = 123
        handler._extract_command_context.return_value.language = "en"
        handler.edit_message = AsyncMock()

        handler.services.user_service.update_user_settings.side_effect = (
            UserSettingsUpdateError("DB Error")
        )

        result = await handler.handle_selection_callback(update_mock, context_mock)

        # Verify
        assert result is None
        handler.edit_message.assert_called_once_with(
            query=update_mock.callback_query,
            message_text="Error",
        )

    @pytest.mark.asyncio
    @patch("src.bot.handlers.settings.timezone_handler.use_locale")
    async def test_handle_input_valid_timezone(
        self,
        mock_use_locale: MagicMock,
        handler: TimezoneHandler,
        update_mock: MagicMock,
        context_mock: MagicMock,
    ) -> None:
        """Test manual input with a valid timezone."""
        # Setup mocks
        mock_pgettext = MagicMock(return_value="Success")
        mock_use_locale.return_value = (None, None, mock_pgettext)

        update_mock.message.text = "America/New_York"

        handler._extract_command_context = AsyncMock()
        handler._extract_command_context.return_value.user_id = 123
        handler._extract_command_context.return_value.language = "en"

        result = await handler.handle_input(update_mock, context_mock)

        # Verify
        assert result == ConversationState.IDLE.value
        handler.services.user_service.update_user_settings.assert_called_once_with(
            telegram_id=123, timezone="America/New_York"
        )
        update_mock.message.reply_text.assert_called_once_with(
            "Success", parse_mode="HTML"
        )

    @pytest.mark.asyncio
    @patch("src.bot.handlers.settings.timezone_handler.use_locale")
    async def test_handle_input_invalid_timezone(
        self,
        mock_use_locale: MagicMock,
        handler: TimezoneHandler,
        update_mock: MagicMock,
        context_mock: MagicMock,
    ) -> None:
        """Test manual input with an invalid timezone."""
        # Setup mocks
        mock_pgettext = MagicMock(return_value="Invalid")
        mock_use_locale.return_value = (None, None, mock_pgettext)

        update_mock.message.text = "Invalid/Timezone"

        handler._extract_command_context = AsyncMock()
        handler._extract_command_context.return_value.user_id = 123
        handler._extract_command_context.return_value.language = "en"

        result = await handler.handle_input(update_mock, context_mock)

        # Verify
        assert result == ConversationState.AWAITING_SETTINGS_TIMEZONE.value
        handler.services.user_service.update_user_settings.assert_not_called()
        update_mock.message.reply_text.assert_called_once_with("Invalid")
