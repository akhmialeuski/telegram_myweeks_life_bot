"""Integration tests for settings handlers.

This module provides comprehensive testing for the settings functionality,
covering the main menu dispatcher and individual setting handlers.

It verifies:
- Happy paths for all settings (Birth Date, Language, Life Expectancy)
- Error handling (Invalid formats, logic errors, database errors)
- State management (Setting and clearing conversation states)
- UI responses (Correct messages and markup)
- Access control and user specific content (Premium vs Basic)

Test Groups:
    - TestSettingsDispatcher: Main menu navigation
    - TestBirthDateHandler: Date input flow and validation
    - TestLanguageHandler: Language selection
    - TestLifeExpectancyHandler: Numeric input flow and validation
"""

import time
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.conversations.persistence import STATE_ID_KEY, STATE_KEY, TIMESTAMP_KEY
from src.bot.conversations.states import ConversationState
from src.bot.handlers.settings.birth_date_handler import BirthDateHandler
from src.bot.handlers.settings.dispatcher import SettingsDispatcher
from src.bot.handlers.settings.language_handler import LanguageHandler
from src.bot.handlers.settings.life_expectancy_handler import LifeExpectancyHandler
from src.bot.handlers.settings.notification_schedule_handler import NotificationScheduleHandler
from src.enums import NotificationFrequency, SubscriptionType, SupportedLanguage
from src.services.container import ServiceContainer
from tests.integration.conftest import (
    TEST_USER_ID,
    get_reply_text,
    set_message_text,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestSettingsDispatcher:
    """Tests for the main settings menu dispatcher."""

    async def test_settings_menu_basic_user_display(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
    ) -> None:
        """Test settings menu display for a user with Basic subscription.

        Preconditions:
            - User is registered
            - User has Basic subscription

        Test Steps:
            1. User sends /settings command
               Expected: Bot displays settings menu
               Response: Message with Basic subscription details

        Post-conditions:
            - Response contains "Basic Subscription"
            - User birth date is shown
            - Language is shown

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
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        handler = SettingsDispatcher(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/settings")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)

        assert "Basic Subscription" in reply_text
        assert "01.01.1990" in reply_text
        assert "English" in reply_text  # Default lang name
        assert "80 years" in reply_text  # Default expectancy

    async def test_settings_menu_premium_user_display(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
    ) -> None:
        """Test settings menu display for a user with Premium subscription.

        Preconditions:
            - User is registered
            - User has Premium subscription

        Test Steps:
            1. User sends /settings command
               Expected: Bot displays settings menu
               Response: Message with Premium subscription details

        Post-conditions:
            - Response contains "Premium Subscription"

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
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        # Upgrade to Premium
        await test_service_container.user_service.update_user_subscription(
            telegram_id=TEST_USER_ID, subscription_type=SubscriptionType.PREMIUM
        )

        handler = SettingsDispatcher(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/settings")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert "Premium Subscription" in reply_text


@pytest.mark.integration
@pytest.mark.asyncio
class TestBirthDateHandler:
    """Tests for birth date settings modifications including validation."""

    @pytest.fixture
    def handler(self, test_service_container: ServiceContainer) -> BirthDateHandler:
        return BirthDateHandler(services=test_service_container)

    async def test_callback_initiates_input_flow(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that clicking 'Birth Date' button prompts for input and sets state.

        Preconditions:
            - User is registered
            - User clicks 'Birth Date' in specific menu

        Test Steps:
            1. User clicks 'Birth Date' button
               Expected: Bot prompts for date input
               Response: Message asking for new birth date

        Post-conditions:
            - Conversation state is AWAITING_SETTINGS_BIRTH_DATE

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        mock_update.message = None
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = "settings_birth_date"

        async def _async_edit(*args, **kwargs):
            return None

        mock_update.callback_query.edit_message_text = MagicMock(
            side_effect=_async_edit
        )
        mock_update.callback_query.answer = AsyncMock()
        mock_update.effective_user = mock_telegram_user

        # --- ACT ---
        await handler.handle_callback(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.callback_query.edit_message_text.assert_called_once()
        args = mock_update.callback_query.edit_message_text.call_args
        assert "Enter new birth date" in args.kwargs["text"]

        # Should set waiting state (verify via context.user_data)
        assert (
            mock_context.user_data.get(STATE_KEY)
            == ConversationState.AWAITING_SETTINGS_BIRTH_DATE.value
        )

    async def test_input_valid_date_success(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that entering a valid date updates the profile and clears state.

        Preconditions:
            - User is registered
            - User is in AWAITING_SETTINGS_BIRTH_DATE state

        Test Steps:
            1. User inputs valid date "01.01.2000"
               Expected: Bot updates birth date
               Response: Success message

        Post-conditions:
            - Profile birth date updated to 2000-01-01
            - Conversation state cleared

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        # Manually set waiting state in context.user_data as persistence does
        mock_context.user_data = {
            STATE_KEY: ConversationState.AWAITING_SETTINGS_BIRTH_DATE.value,
            TIMESTAMP_KEY: time.time(),
            STATE_ID_KEY: str(uuid.uuid4()),
        }

        set_message_text(mock_update=mock_update, text="01.01.2000")

        # --- ACT ---
        await handler.handle_input(update=mock_update, context=mock_context)

        # --- ASSERT ---
        # 1. Profile updated
        profile = await test_service_container.user_service.get_user_profile(
            TEST_USER_ID
        )
        assert profile.settings.birth_date == date(2000, 1, 1)

        # 2. State cleared (checked via context.user_data)
        assert STATE_KEY not in mock_context.user_data

        # 3. Success message
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert "successfully updated" in reply_text

    async def test_input_invalid_format_error(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that invalid date format triggers error message and keeps state.

        Preconditions:
            - User is registered
            - User is in AWAITING_SETTINGS_BIRTH_DATE state

        Test Steps:
            1. User inputs invalid date "invalid-date"
               Expected: Bot shows error message
               Response: Error message "Invalid date format"

        Post-conditions:
            - Profile birth date NOT changed
            - Conversation state remains AWAITING_SETTINGS_BIRTH_DATE

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        mock_context.user_data = {
            STATE_KEY: ConversationState.AWAITING_SETTINGS_BIRTH_DATE.value,
            TIMESTAMP_KEY: time.time(),
            STATE_ID_KEY: str(uuid.uuid4()),
        }

        set_message_text(mock_update=mock_update, text="invalid-date")

        # --- ACT ---
        await handler.handle_input(update=mock_update, context=mock_context)

        # --- ASSERT ---
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert "Invalid date format" in reply_text

        # State should PRESERVE (via context.user_data)
        assert (
            mock_context.user_data.get(STATE_KEY)
            == ConversationState.AWAITING_SETTINGS_BIRTH_DATE.value
        )

    async def test_input_future_date_error(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that future date input is rejected.

        Preconditions:
            - User is registered
            - User is in AWAITING_SETTINGS_BIRTH_DATE state

        Test Steps:
            1. User inputs a future date
               Expected: Bot shows error message
               Response: Error message about future date

        Post-conditions:
            - Profile birth date NOT changed

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        mock_context.user_data = {
            STATE_KEY: ConversationState.AWAITING_SETTINGS_BIRTH_DATE.value,
            TIMESTAMP_KEY: time.time(),
            STATE_ID_KEY: str(uuid.uuid4()),
        }

        future_date = date.today() + timedelta(days=365)
        set_message_text(mock_update=mock_update, text=future_date.strftime("%d.%m.%Y"))

        # --- ACT ---
        await handler.handle_input(update=mock_update, context=mock_context)

        # --- ASSERT ---
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert "future" in reply_text.lower()

        # Verify db not changed
        profile = await test_service_container.user_service.get_user_profile(
            TEST_USER_ID
        )
        assert profile.settings.birth_date == date(1990, 1, 1)

    async def test_input_ignored_if_wrong_state(
        self,
        handler: BirthDateHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that input is ignored if user is not in AWAITING_SETTINGS_BIRTH_DATE state.

        Preconditions:
            - User is registered
            - User is NOT in AWAITING_SETTINGS_BIRTH_DATE state

        Test Steps:
            1. User inputs date "01.01.2000"
               Expected: Bot ignores input
               Response: None

        Post-conditions:
            - Profile birth date NOT changed

        :param handler: BirthDateHandler instance
        :type handler: BirthDateHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        # No state set

        set_message_text(mock_update=mock_update, text="01.01.2000")

        # --- ACT ---
        await handler.handle_input(update=mock_update, context=mock_context)

        # --- ASSERT ---
        # Should call _clear_waiting_state logic which ensures clean slate, but basically no update
        profile = await test_service_container.user_service.get_user_profile(
            TEST_USER_ID
        )
        assert profile.settings.birth_date == date(1990, 1, 1)

        # Should probably not reply or reply with generic handler if integrated,
        # but unit test of handle_input calls it directly.
        # The code checks `_is_valid_waiting_state`. If false, it logs warning and clears state.
        # It does NOT send a reply.
        mock_update.message.reply_text.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
class TestLanguageHandler:
    """Tests for language settings modifications."""

    @pytest.fixture
    def handler(self, test_service_container: ServiceContainer) -> LanguageHandler:
        return LanguageHandler(services=test_service_container)

    async def test_callback_shows_options(
        self,
        handler: LanguageHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that clicking 'Language' shows available language options.

        Preconditions:
            - User is registered
            - User selects 'Language' from settings menu

        Test Steps:
            1. User clicks 'Language' button
               Expected: Bot edits message to show language options
               Response: Language selection keyboard

        Post-conditions:
            - Message text updated
            - Specific keyboard is shown

        :param handler: LanguageHandler instance
        :type handler: LanguageHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        mock_update.message = None
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = "settings_language"

        async def _async_edit(*args, **kwargs):
            return None

        mock_update.callback_query.edit_message_text = MagicMock(
            side_effect=_async_edit
        )
        mock_update.callback_query.answer = AsyncMock()
        mock_update.effective_user = mock_telegram_user

        # --- ACT ---
        await handler.handle_callback(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.callback_query.edit_message_text.assert_called_once()
        args = mock_update.callback_query.edit_message_text.call_args
        assert args.kwargs.get("reply_markup") is not None
        assert "Select your preferred language" in args.kwargs["text"]

    async def test_selection_updates_language(
        self,
        handler: LanguageHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test selecting a valid language updates the profile.

        Preconditions:
            - User is registered
            - User is in language selection menu

        Test Steps:
            1. User selects 'Russian' language
               Expected: Profile language updates to 'ru'
               Response: Success message/menu refresh

        Post-conditions:
            - User profile settings.language is 'ru'

        :param handler: LanguageHandler instance
        :type handler: LanguageHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        mock_update.message = None
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = f"language_{SupportedLanguage.RU.value}"

        async def _async_edit(*args, **kwargs):
            return None

        mock_update.callback_query.edit_message_text = MagicMock(
            side_effect=_async_edit
        )
        mock_update.callback_query.answer = AsyncMock()
        mock_update.effective_user = mock_telegram_user

        # --- ACT ---
        await handler.handle_selection_callback(
            update=mock_update, context=mock_context
        )

        # --- ASSERT ---
        profile = await test_service_container.user_service.get_user_profile(
            TEST_USER_ID
        )
        assert profile.settings.language == SupportedLanguage.RU.value

        # Verify localized success message (Russian check might be tricky if translations not loaded,
        # but code attempts to use locale)
        mock_update.callback_query.edit_message_text.assert_called_once()

    async def test_selection_invalid_code_error(
        self,
        handler: LanguageHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that selecting an invalid language code shows error.

        Preconditions:
            - User is registered

        Test Steps:
            1. User sends callback with invalid language code
               Expected: Bot shows error message
               Response: Error notification

        Post-conditions:
            - Language is NOT changed

        :param handler: LanguageHandler instance
        :type handler: LanguageHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        mock_update.message = None
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = "language_INVALID"

        async def _async_edit(*args, **kwargs):
            return None

        mock_update.callback_query.edit_message_text = MagicMock(
            side_effect=_async_edit
        )
        mock_update.callback_query.answer = AsyncMock()
        mock_update.effective_user = mock_telegram_user

        # --- ACT ---
        await handler.handle_selection_callback(
            update=mock_update, context=mock_context
        )

        # --- ASSERT ---
        mock_update.callback_query.edit_message_text.assert_called_once()
        args = mock_update.callback_query.edit_message_text.call_args
        assert "error occurred" in args.kwargs["text"]

        # DB should not change
        profile = await test_service_container.user_service.get_user_profile(
            TEST_USER_ID
        )
        assert profile.settings.language is None  # Default


@pytest.mark.integration
@pytest.mark.asyncio
class TestLifeExpectancyHandler:
    """Tests for life expectancy settings modifications."""

    @pytest.fixture
    def handler(
        self, test_service_container: ServiceContainer
    ) -> LifeExpectancyHandler:
        return LifeExpectancyHandler(services=test_service_container)

    async def test_callback_initiates_input(
        self,
        handler: LifeExpectancyHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that clicking 'Life Expectancy' initiates input flow.

        Preconditions:
            - User is registered

        Test Steps:
            1. User clicks 'Life Expectancy' button
               Expected: Bot prompts for new value
               Response: Input prompt message

        Post-conditions:
            - User state set to AWAITING_SETTINGS_LIFE_EXPECTANCY

        :param handler: LifeExpectancyHandler instance
        :type handler: LifeExpectancyHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        mock_update.message = None
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = "settings_life_expectancy"

        async def _async_edit(*args, **kwargs):
            return None

        mock_update.callback_query.edit_message_text = MagicMock(
            side_effect=_async_edit
        )
        mock_update.callback_query.answer = AsyncMock()
        mock_update.effective_user = mock_telegram_user

        # --- ACT ---
        await handler.handle_callback(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.callback_query.edit_message_text.assert_called_once()

        assert (
            mock_context.user_data.get(STATE_KEY)
            == ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY.value
        )

    async def test_input_valid_value_success(
        self,
        handler: LifeExpectancyHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test valid numeric input updates the profile.

        Preconditions:
            - User is registered
            - User is in AWAITING_SETTINGS_LIFE_EXPECTANCY state

        Test Steps:
            1. User inputs "90"
               Expected: Profile updates
               Response: Success message

        Post-conditions:
            - Profile life expectancy updated to 90

        :param handler: LifeExpectancyHandler instance
        :type handler: LifeExpectancyHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        mock_context.user_data = {
            STATE_KEY: ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY.value,
            TIMESTAMP_KEY: time.time(),
            STATE_ID_KEY: str(uuid.uuid4()),
        }

        set_message_text(mock_update=mock_update, text="90")

        # --- ACT ---
        await handler.handle_input(update=mock_update, context=mock_context)

        # --- ASSERT ---
        profile = await test_service_container.user_service.get_user_profile(
            TEST_USER_ID
        )
        assert profile.settings.life_expectancy == 90

        reply_text = get_reply_text(mock_message=mock_update.message)
        assert "updated" in reply_text

    async def test_input_non_numeric_error(
        self,
        handler: LifeExpectancyHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that non-numeric input triggers error.

        Preconditions:
            - User is registered
            - User is in AWAITING_SETTINGS_LIFE_EXPECTANCY state

        Test Steps:
            1. User inputs "abc"
               Expected: Bot shows error message
               Response: Error message "Invalid life expectancy"

        Post-conditions:
            - User state remains AWAITING_SETTINGS_LIFE_EXPECTANCY

        :param handler: LifeExpectancyHandler instance
        :type handler: LifeExpectancyHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        mock_context.user_data = {
            STATE_KEY: ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY.value,
            TIMESTAMP_KEY: time.time(),
            STATE_ID_KEY: str(uuid.uuid4()),
        }

        set_message_text(mock_update=mock_update, text="abc")

        # --- ACT ---
        await handler.handle_input(update=mock_update, context=mock_context)

        # --- ASSERT ---
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert "Invalid life expectancy" in reply_text

        # State should be preserved
        assert (
            mock_context.user_data.get(STATE_KEY)
            == ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY.value
        )

    async def test_input_out_of_range_error(
        self,
        handler: LifeExpectancyHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that input outside valid range (50-120) is rejected.

        Preconditions:
            - User is registered
            - User is in AWAITING_SETTINGS_LIFE_EXPECTANCY state

        Test Steps:
            1. User inputs "150"
               Expected: Bot shows error message
               Response: Error message "Invalid life expectancy"

        Post-conditions:
            - User state remains AWAITING_SETTINGS_LIFE_EXPECTANCY

        :param handler: LifeExpectancyHandler instance
        :type handler: LifeExpectancyHandler
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :param test_service_container: Service container
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE ---
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        mock_context.user_data = {
            STATE_KEY: ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY.value,
            TIMESTAMP_KEY: time.time(),
            STATE_ID_KEY: str(uuid.uuid4()),
        }

        set_message_text(mock_update=mock_update, text="150")

        # --- ACT ---
        await handler.handle_input(update=mock_update, context=mock_context)

        # --- ASSERT ---
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert "Invalid life expectancy" in reply_text


@pytest.mark.integration
@pytest.mark.asyncio
class TestNotificationScheduleHandler:
    """Integration tests for premium notification schedule setting."""

    @pytest.fixture
    def handler(self, test_service_container: ServiceContainer) -> NotificationScheduleHandler:
        return NotificationScheduleHandler(services=test_service_container)

    async def test_premium_user_can_update_weekly_schedule(
        self,
        handler: NotificationScheduleHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        await test_service_container.user_service.update_user_subscription(
            telegram_id=TEST_USER_ID,
            subscription_type=SubscriptionType.PREMIUM,
        )

        mock_update.message = None
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = "settings_notification_schedule"
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()

        await handler.handle_callback(update=mock_update, context=mock_context)

        set_message_text(mock_update=mock_update, text="weekly friday 10:30")
        await handler.handle_input(update=mock_update, context=mock_context)

        profile = await test_service_container.user_service.get_user_profile(TEST_USER_ID)
        assert profile is not None
        assert profile.settings.notification_frequency == NotificationFrequency.WEEKLY
        assert str(profile.settings.notifications_day).lower().endswith("friday")
        assert profile.settings.notifications_time.hour == 10
        assert profile.settings.notifications_time.minute == 30

    async def test_basic_user_cannot_access_schedule_setting(
        self,
        handler: NotificationScheduleHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )

        mock_update.message = None
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = "settings_notification_schedule"
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()

        await handler.handle_callback(update=mock_update, context=mock_context)

        called_text = mock_update.callback_query.edit_message_text.call_args.kwargs["text"]
        assert "only for Premium" in called_text

    async def test_premium_invalid_schedule_input_returns_validation_error(
        self,
        handler: NotificationScheduleHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=date(1990, 1, 1),
        )
        await test_service_container.user_service.update_user_subscription(
            telegram_id=TEST_USER_ID,
            subscription_type=SubscriptionType.PREMIUM,
        )

        mock_update.message = None
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.data = "settings_notification_schedule"
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()

        await handler.handle_callback(update=mock_update, context=mock_context)

        set_message_text(mock_update=mock_update, text="monthly 35 22:00")
        await handler.handle_input(update=mock_update, context=mock_context)

        reply_text = get_reply_text(mock_message=mock_update.message)
        assert "Invalid format" in reply_text
