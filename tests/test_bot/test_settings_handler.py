"""Unit tests for SettingsHandler.

Tests the SettingsHandler class which handles /settings command.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_SETTINGS
from src.bot.handlers.settings_handler import SettingsHandler
from src.constants import DEFAULT_LIFE_EXPECTANCY
from src.core.enums import SubscriptionType
from src.database.service import UserNotFoundError, UserSettingsUpdateError
from src.utils.config import MAX_LIFE_EXPECTANCY, MIN_BIRTH_YEAR, MIN_LIFE_EXPECTANCY
from src.utils.localization import SupportedLanguage
from tests.conftest import TEST_USER_ID

# Test constants
TEST_BIRTH_DATE = "15.03.1990"
TEST_LANGUAGE = SupportedLanguage.EN.value


class TestSettingsHandler:
    """Test suite for SettingsHandler class."""

    @pytest.fixture
    def handler(self) -> SettingsHandler:
        """Create SettingsHandler instance.

        :returns: SettingsHandler instance
        :rtype: SettingsHandler
        """
        return SettingsHandler()

    def test_handler_creation(self, handler: SettingsHandler) -> None:
        """Test SettingsHandler creation.

        :param handler: SettingsHandler instance
        :returns: None
        """
        assert handler.command_name == f"/{COMMAND_SETTINGS}"

    @pytest.mark.asyncio
    async def test_handle_premium_success(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with premium user.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = "en"

        # Create premium user profile mock
        mock_premium_user_profile = MagicMock()
        mock_premium_user_profile.subscription = MagicMock()
        mock_premium_user_profile.subscription.subscription_type = (
            SubscriptionType.PREMIUM
        )

        # Mock all required functions in the module where they're imported
        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.settings_handler.generate_message_settings_premium"
        ) as mock_generate_premium, patch(
            "src.bot.handlers.settings_handler.generate_settings_buttons"
        ) as mock_generate_buttons, patch(
            "src.bot.handlers.settings_handler.InlineKeyboardButton"
        ) as mock_button, patch(
            "src.bot.handlers.settings_handler.InlineKeyboardMarkup"
        ) as mock_markup:

            # Setup mocks
            mock_user_service.is_valid_user_profile.return_value = True
            mock_base_user_service.is_valid_user_profile.return_value = True
            mock_base_user_service.get_user_profile.return_value = (
                mock_premium_user_profile
            )
            mock_generate_premium.return_value = "Premium settings!"
            # Return button configurations to cover keyboard creation lines
            mock_generate_buttons.return_value = [
                [{"text": "Change Birth Date", "callback_data": "settings_birth_date"}]
            ]
            mock_button.return_value = MagicMock()
            mock_markup.return_value = MagicMock()

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_generate_premium.assert_called_once_with(
                user_info=mock_update.effective_user
            )
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert call_args.kwargs["text"] == "Premium settings!"
            assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_basic_success(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with basic user.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = "en"

        # Create basic user profile mock
        mock_basic_user_profile = MagicMock()
        mock_basic_user_profile.subscription = MagicMock()
        mock_basic_user_profile.subscription.subscription_type = SubscriptionType.BASIC

        # Mock all required functions in the module where they're imported
        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.settings_handler.generate_message_settings_basic"
        ) as mock_generate_basic, patch(
            "src.bot.handlers.settings_handler.generate_settings_buttons"
        ) as mock_generate_buttons, patch(
            "src.bot.handlers.settings_handler.InlineKeyboardButton"
        ) as mock_button, patch(
            "src.bot.handlers.settings_handler.InlineKeyboardMarkup"
        ) as mock_markup:

            # Setup mocks
            mock_user_service.is_valid_user_profile.return_value = True
            mock_base_user_service.is_valid_user_profile.return_value = True
            mock_base_user_service.get_user_profile.return_value = (
                mock_basic_user_profile
            )
            mock_generate_basic.return_value = "Basic settings!"
            mock_generate_buttons.return_value = []
            mock_button.return_value = MagicMock()
            mock_markup.return_value = MagicMock()

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_generate_basic.assert_called_once_with(
                user_info=mock_update.effective_user
            )
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert call_args.kwargs["text"] == "Basic settings!"
            assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_no_profile(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with no user profile.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = "en"

        # Mock all required functions in the module where they're imported
        with patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.base_handler.get_message"
        ) as mock_get_message:

            # Setup mocks - user not registered
            mock_base_user_service.is_valid_user_profile.return_value = False
            mock_get_message.return_value = "You need to register first!"

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_get_message.assert_called_once_with(
                message_key="common", sub_key="not_registered", language="en"
            )
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            # Check if text was passed as positional argument or kwargs
            if call_args.args:
                assert call_args.args[0] == "You need to register first!"
            else:
                assert call_args.kwargs["text"] == "You need to register first!"

    @pytest.mark.asyncio
    async def test_handle_exception(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with exception.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = "en"

        # Create user profile mock
        mock_user_profile = MagicMock()
        mock_user_profile.subscription = MagicMock()
        mock_user_profile.subscription.subscription_type = SubscriptionType.BASIC

        # Mock all required functions in the module where they're imported
        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.settings_handler.generate_message_settings_basic"
        ) as mock_generate_basic:

            # Setup mocks
            mock_user_service.is_valid_user_profile.return_value = True
            mock_user_service.get_user_profile.return_value = mock_user_profile
            mock_generate_basic.side_effect = Exception("Test exception")

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert that error message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Test exception" in call_args.kwargs["text"]
            assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_settings_callback_birth_date(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_settings_callback method with birth_date callback.

        :param handler: SettingsHandler instance
        :param mock_update_with_callback: Mock Update object with callback
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update_with_callback.callback_query.data = "settings_birth_date"

        with patch(
            "src.bot.handlers.settings_handler.generate_message_change_birth_date"
        ) as mock_generate_msg:
            mock_generate_msg.return_value = "Change birth date message"

            # Execute
            await handler.handle_settings_callback(
                mock_update_with_callback, mock_context
            )

            # Assert
            mock_update_with_callback.callback_query.answer.assert_called_once()
            mock_generate_msg.assert_called_once_with(
                user_info=mock_update_with_callback.effective_user
            )
            assert mock_context.user_data["waiting_for"] == "settings_birth_date"

    @pytest.mark.asyncio
    async def test_handle_settings_callback_language(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_settings_callback method with language callback.

        :param handler: SettingsHandler instance
        :param mock_update_with_callback: Mock Update object with callback
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update_with_callback.callback_query.data = "settings_language"

        with patch(
            "src.bot.handlers.settings_handler.generate_message_change_language"
        ) as mock_generate_msg, patch(
            "src.bot.handlers.settings_handler.InlineKeyboardButton"
        ) as mock_button, patch(
            "src.bot.handlers.settings_handler.InlineKeyboardMarkup"
        ) as mock_markup:

            mock_generate_msg.return_value = "Change language message"
            mock_button.return_value = MagicMock()
            mock_markup.return_value = MagicMock()

            # Execute
            await handler.handle_settings_callback(
                mock_update_with_callback, mock_context
            )

            # Assert
            mock_update_with_callback.callback_query.answer.assert_called_once()
            mock_generate_msg.assert_called_once_with(
                user_info=mock_update_with_callback.effective_user
            )

    @pytest.mark.asyncio
    async def test_handle_settings_callback_life_expectancy(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_settings_callback method with life_expectancy callback.

        :param handler: SettingsHandler instance
        :param mock_update_with_callback: Mock Update object with callback
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update_with_callback.callback_query.data = "settings_life_expectancy"

        with patch(
            "src.bot.handlers.settings_handler.generate_message_change_life_expectancy"
        ) as mock_generate_msg:
            mock_generate_msg.return_value = "Change life expectancy message"

            # Execute
            await handler.handle_settings_callback(
                mock_update_with_callback, mock_context
            )

            # Assert
            mock_update_with_callback.callback_query.answer.assert_called_once()
            mock_generate_msg.assert_called_once_with(
                user_info=mock_update_with_callback.effective_user
            )
            assert mock_context.user_data["waiting_for"] == "settings_life_expectancy"

    @pytest.mark.asyncio
    async def test_handle_settings_callback_unknown(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_settings_callback method with unknown callback.

        :param handler: SettingsHandler instance
        :param mock_update_with_callback: Mock Update object with callback
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update_with_callback.callback_query.data = "unknown_setting"

        # Execute
        await handler.handle_settings_callback(mock_update_with_callback, mock_context)

        # Assert
        mock_update_with_callback.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_settings_callback_exception(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_settings_callback method with exception.

        :param handler: SettingsHandler instance
        :param mock_update_with_callback: Mock Update object with callback
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update_with_callback.callback_query.data = "settings_birth_date"
        mock_update_with_callback.callback_query.answer.side_effect = Exception(
            "Test error"
        )

        with patch(
            "src.bot.handlers.settings_handler.generate_message_settings_error"
        ) as mock_generate_error:
            mock_generate_error.return_value = "Settings error message"

            # Execute
            await handler.handle_settings_callback(
                mock_update_with_callback, mock_context
            )

            # Assert
            mock_generate_error.assert_called_once_with(
                user_info=mock_update_with_callback.effective_user
            )

    @pytest.mark.asyncio
    async def test_handle_language_callback_success(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_language_callback method successful language change.

        :param handler: SettingsHandler instance
        :param mock_update_with_callback: Mock Update object with callback
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update_with_callback.callback_query.data = "language_ru"

        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.settings_handler.get_localized_language_name"
        ) as mock_get_lang_name, patch(
            "src.bot.handlers.settings_handler.update_user_schedule"
        ) as mock_update_schedule, patch(
            "src.bot.handlers.settings_handler.generate_message_language_updated"
        ) as mock_generate_msg:

            mock_get_lang_name.return_value = "Русский"
            mock_generate_msg.return_value = "Language updated!"

            # Execute
            await handler.handle_language_callback(
                mock_update_with_callback, mock_context
            )

            # Assert
            mock_update_with_callback.callback_query.answer.assert_called_once()
            mock_user_service.update_user_settings.assert_called_once_with(
                telegram_id=TEST_USER_ID, language=SupportedLanguage.RU.value
            )
            mock_update_schedule.assert_called_once_with(user_id=TEST_USER_ID)
            mock_generate_msg.assert_called_once_with(
                user_info=mock_update_with_callback.effective_user,
                new_language="Русский",
            )

    @pytest.mark.asyncio
    async def test_handle_language_callback_invalid_language(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_language_callback method with invalid language.

        :param handler: SettingsHandler instance
        :param mock_update_with_callback: Mock Update object with callback
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update_with_callback.callback_query.data = "language_invalid"

        with patch(
            "src.bot.handlers.settings_handler.generate_message_settings_error"
        ) as mock_generate_error:
            mock_generate_error.return_value = "Settings error message"

            # Execute
            await handler.handle_language_callback(
                mock_update_with_callback, mock_context
            )

            # Assert
            mock_update_with_callback.callback_query.answer.assert_called_once()
            mock_generate_error.assert_called_once_with(
                user_info=mock_update_with_callback.effective_user
            )

    @pytest.mark.asyncio
    async def test_handle_language_callback_database_error(
        self,
        handler: SettingsHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_language_callback method with database error.

        :param handler: SettingsHandler instance
        :param mock_update_with_callback: Mock Update object with callback
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update_with_callback.callback_query.data = "language_en"

        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.settings_handler.get_localized_language_name"
        ) as mock_get_lang_name, patch(
            "src.bot.handlers.settings_handler.generate_message_settings_error"
        ) as mock_generate_error:

            mock_get_lang_name.return_value = "English"
            mock_user_service.update_user_settings.side_effect = UserNotFoundError(
                "User not found"
            )
            mock_generate_error.return_value = "Settings error message"

            # Execute
            await handler.handle_language_callback(
                mock_update_with_callback, mock_context
            )

            # Assert
            mock_update_with_callback.callback_query.answer.assert_called_once()
            mock_generate_error.assert_called_once_with(
                user_info=mock_update_with_callback.effective_user
            )

    @pytest.mark.asyncio
    async def test_handle_settings_input_birth_date(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_settings_input method with birth date input.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update.message.text = TEST_BIRTH_DATE
        mock_context.user_data = {"waiting_for": "settings_birth_date"}

        with patch.object(handler, "handle_birth_date_input") as mock_handle_birth_date:
            # Execute
            await handler.handle_settings_input(mock_update, mock_context)

            # Assert
            mock_handle_birth_date.assert_called_once_with(
                update=mock_update, context=mock_context, message_text=TEST_BIRTH_DATE
            )

    @pytest.mark.asyncio
    async def test_handle_settings_input_life_expectancy(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_settings_input method with life expectancy input.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update.message.text = str(DEFAULT_LIFE_EXPECTANCY)
        mock_context.user_data = {"waiting_for": "settings_life_expectancy"}

        with patch.object(
            handler, "handle_life_expectancy_input"
        ) as mock_handle_life_expectancy:
            # Execute
            await handler.handle_settings_input(mock_update, mock_context)

            # Assert
            mock_handle_life_expectancy.assert_called_once_with(
                update=mock_update,
                context=mock_context,
                message_text=str(DEFAULT_LIFE_EXPECTANCY),
            )

    @pytest.mark.asyncio
    async def test_handle_settings_input_not_waiting(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_settings_input method when not waiting for input.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update.message.text = "Some text"
        mock_context.user_data = {}

        with patch.object(
            handler, "handle_birth_date_input"
        ) as mock_handle_birth_date, patch.object(
            handler, "handle_life_expectancy_input"
        ) as mock_handle_life_expectancy:

            # Execute
            await handler.handle_settings_input(mock_update, mock_context)

            # Assert - no methods should be called
            mock_handle_birth_date.assert_not_called()
            mock_handle_life_expectancy.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_settings_input_exception(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_settings_input method with exception.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_update.message.text = TEST_BIRTH_DATE
        mock_context.user_data = {"waiting_for": "settings_birth_date"}

        with patch.object(handler, "handle_birth_date_input") as mock_handle_birth_date:
            mock_handle_birth_date.side_effect = Exception("Test error")

            # Execute
            await handler.handle_settings_input(mock_update, mock_context)

            # Assert - error message should be sent
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_success(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_birth_date_input method with valid birth date.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        test_birth_date = date(1990, 3, 15)
        mock_context.user_data = {"waiting_for": "settings_birth_date"}

        mock_updated_profile = MagicMock()
        mock_calculator = MagicMock()
        mock_calculator.calculate_age.return_value = 33

        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.settings_handler.LifeCalculatorEngine"
        ) as mock_calc_class, patch(
            "src.bot.handlers.settings_handler.generate_message_birth_date_updated"
        ) as mock_generate_msg, patch(
            "src.bot.handlers.settings_handler.datetime"
        ) as mock_datetime:

            mock_datetime.strptime.return_value.date.return_value = test_birth_date
            mock_user_service.get_user_profile.return_value = mock_updated_profile
            mock_calc_class.return_value = mock_calculator
            mock_generate_msg.return_value = "Birth date updated!"

            # Execute
            await handler.handle_birth_date_input(
                mock_update, mock_context, TEST_BIRTH_DATE
            )

            # Assert
            mock_user_service.update_user_settings.assert_called_once_with(
                telegram_id=TEST_USER_ID, birth_date=test_birth_date
            )
            mock_update.message.reply_text.assert_called_once()
            assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_future_date(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_birth_date_input method with future birth date.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        future_date = date(2025, 1, 1)

        with patch(
            "src.bot.handlers.settings_handler.generate_message_birth_date_future_error"
        ) as mock_generate_error, patch(
            "src.bot.handlers.settings_handler.datetime"
        ) as mock_datetime, patch(
            "src.bot.handlers.settings_handler.date"
        ) as mock_date:

            mock_datetime.strptime.return_value.date.return_value = future_date
            mock_date.today.return_value = date(2024, 1, 1)
            mock_generate_error.return_value = "Future date error!"

            # Execute
            await handler.handle_birth_date_input(
                mock_update, mock_context, "01.01.2025"
            )

            # Assert
            mock_generate_error.assert_called_once_with(
                user_info=mock_update.effective_user
            )
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_old_date(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_birth_date_input method with too old birth date.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        old_date = date(1800, 1, 1)

        with patch(
            "src.bot.handlers.settings_handler.generate_message_birth_date_old_error"
        ) as mock_generate_error, patch(
            "src.bot.handlers.settings_handler.datetime"
        ) as mock_datetime, patch(
            "src.bot.handlers.settings_handler.MIN_BIRTH_YEAR", MIN_BIRTH_YEAR
        ):

            mock_datetime.strptime.return_value.date.return_value = old_date
            mock_generate_error.return_value = "Old date error!"

            # Execute
            await handler.handle_birth_date_input(
                mock_update, mock_context, "01.01.1800"
            )

            # Assert
            mock_generate_error.assert_called_once_with(
                user_info=mock_update.effective_user
            )
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_database_error(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_birth_date_input method with database error.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        test_birth_date = date(1990, 3, 15)

        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.settings_handler.generate_message_settings_error"
        ) as mock_generate_error, patch(
            "src.bot.handlers.settings_handler.datetime"
        ) as mock_datetime:

            mock_datetime.strptime.return_value.date.return_value = test_birth_date
            mock_user_service.update_user_settings.side_effect = UserNotFoundError(
                "User not found"
            )
            mock_generate_error.return_value = "Settings error!"

            # Execute
            await handler.handle_birth_date_input(
                mock_update, mock_context, TEST_BIRTH_DATE
            )

            # Assert
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_format_error(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_birth_date_input method with invalid date format.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE

        with patch(
            "src.bot.handlers.settings_handler.generate_message_birth_date_format_error"
        ) as mock_generate_error, patch(
            "src.bot.handlers.settings_handler.datetime"
        ) as mock_datetime:

            mock_datetime.strptime.side_effect = ValueError("Invalid date format")
            mock_generate_error.return_value = "Format error!"

            # Execute
            await handler.handle_birth_date_input(
                mock_update, mock_context, "invalid-date"
            )

            # Assert
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_success(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_life_expectancy_input method with valid input.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE
        mock_context.user_data = {"waiting_for": "settings_life_expectancy"}

        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.settings_handler.generate_message_life_expectancy_updated"
        ) as mock_generate_msg:

            mock_generate_msg.return_value = "Life expectancy updated!"

            await handler.handle_life_expectancy_input(
                mock_update, mock_context, str(DEFAULT_LIFE_EXPECTANCY)
            )

            mock_user_service.update_user_settings.assert_called_once_with(
                telegram_id=TEST_USER_ID, life_expectancy=DEFAULT_LIFE_EXPECTANCY
            )
            mock_update.message.reply_text.assert_called_once()
            assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_invalid_range(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_life_expectancy_input method with invalid range.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE

        with patch(
            "src.bot.handlers.settings_handler.generate_message_invalid_life_expectancy"
        ) as mock_generate_error, patch(
            "src.bot.handlers.settings_handler.MIN_LIFE_EXPECTANCY", MIN_LIFE_EXPECTANCY
        ), patch(
            "src.bot.handlers.settings_handler.MAX_LIFE_EXPECTANCY", MAX_LIFE_EXPECTANCY
        ):

            mock_generate_error.return_value = "Invalid life expectancy!"

            # Execute - test with too low value
            await handler.handle_life_expectancy_input(mock_update, mock_context, "30")

            # Assert
            mock_generate_error.assert_called_once_with(
                user_info=mock_update.effective_user
            )
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_database_error(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_life_expectancy_input method with database error.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE

        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.settings_handler.generate_message_settings_error"
        ) as mock_generate_error:

            mock_user_service.update_user_settings.side_effect = (
                UserSettingsUpdateError("Update failed")
            )
            mock_generate_error.return_value = "Settings error!"

            await handler.handle_life_expectancy_input(
                mock_update, mock_context, str(DEFAULT_LIFE_EXPECTANCY)
            )

            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_format_error(
        self,
        handler: SettingsHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_life_expectancy_input method with invalid format.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = TEST_LANGUAGE

        with patch(
            "src.bot.handlers.settings_handler.generate_message_invalid_life_expectancy"
        ) as mock_generate_error:
            mock_generate_error.return_value = "Invalid format!"

            # Execute
            await handler.handle_life_expectancy_input(
                mock_update, mock_context, "not-a-number"
            )

            # Assert
            mock_update.message.reply_text.assert_called_once()
