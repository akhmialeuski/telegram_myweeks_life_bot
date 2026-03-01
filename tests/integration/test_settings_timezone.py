"""Integration tests for timezone support.

This module provides comprehensive E2E testing for timezone functionality,
covering registration defaults, handler flows, scheduler application,
and output verification across all supported languages.

Test Groups:
    - TestTimezoneRegistrationDefaults: Default timezone on registration
    - TestTimezoneHandlerPremiumUser: Premium user timezone changes
    - TestTimezoneHandlerTrialUser: Trial user timezone access
    - TestTimezoneHandlerBasicUser: Basic user access control
    - TestTimezoneSchedulerApplication: Scheduler receives correct trigger
    - TestTimezoneOutputAllLanguages: Output verification per language
"""

from datetime import time as datetime_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.constants import DEFAULT_TIMEZONE_MAPPING, FALLBACK_TIMEZONE
from src.bot.conversations.persistence import STATE_ID_KEY, STATE_KEY, TIMESTAMP_KEY
from src.bot.conversations.states import ConversationState
from src.bot.event_listeners import register_event_listeners
from src.bot.handlers.settings.dispatcher import SettingsDispatcher
from src.bot.handlers.settings.timezone_handler import TimezoneHandler
from src.bot.handlers.start_handler import StartHandler
from src.bot.notification_schedule import WEEKDAY_MAP
from src.constants import DEFAULT_TIMEZONE
from src.enums import NotificationFrequency, SupportedLanguage, WeekDay
from src.services.container import ServiceContainer
from tests.constants import (
    CALLBACK_TIMEZONE_MINSK,
    CALLBACK_TIMEZONE_MOSCOW,
    CALLBACK_TIMEZONE_NEW_YORK,
    CALLBACK_TIMEZONE_OTHER,
    CALLBACK_TIMEZONE_UTC,
    CALLBACK_TIMEZONE_WARSAW,
    TEST_STATE_ID,
    TEST_STATE_TIMESTAMP,
    TIMEZONE_AMERICA_NEW_YORK,
    TIMEZONE_EUROPE_LONDON,
    TIMEZONE_EUROPE_MINSK,
    TIMEZONE_EUROPE_MOSCOW,
    TIMEZONE_EUROPE_WARSAW,
    TIMEZONE_INVALID,
)
from tests.integration.conftest import (
    TEST_USER_ID,
    get_reply_text,
    make_premium_user,
    make_registered_user,
    make_trial_user,
    set_message_text,
    setup_timezone_callback,
)


def setup_awaiting_timezone_state(mock_context: MagicMock) -> None:
    """Set mock_context.user_data to AWAITING_SETTINGS_TIMEZONE state.

    :param mock_context: Mock Telegram Context object
    :type mock_context: MagicMock
    :returns: None
    """
    mock_context.user_data = {
        STATE_KEY: ConversationState.AWAITING_SETTINGS_TIMEZONE.value,
        TIMESTAMP_KEY: TEST_STATE_TIMESTAMP,
        STATE_ID_KEY: TEST_STATE_ID,
    }


def get_expected_timezone_for_language(language: SupportedLanguage) -> str:
    """Get expected default timezone for a language.

    :param language: Supported language enum
    :type language: SupportedLanguage
    :returns: IANA timezone string
    :rtype: str
    """
    return DEFAULT_TIMEZONE_MAPPING.get(language, FALLBACK_TIMEZONE)


@pytest.mark.integration
@pytest.mark.asyncio
class TestTimezoneRegistrationDefaults:
    """Tests for default timezone on user registration."""

    @pytest.fixture
    def handler(self, test_service_container: ServiceContainer) -> StartHandler:
        return StartHandler(services=test_service_container)

    @pytest.mark.parametrize("language", list(SupportedLanguage))
    async def test_registration_sets_default_timezone_by_language(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
        language: SupportedLanguage,
    ) -> None:
        """Test that registration sets default timezone from user language.

        Preconditions:
            - User is not registered
            - User language_code matches parametrized language

        Test Steps:
            1. Set AWAITING_START_BIRTH_DATE state
            2. User sends valid birth date
            3. Handler processes registration

        Post-conditions:
            - profile.settings.timezone == DEFAULT_TIMEZONE_MAPPING[language]

        :param handler: StartHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :param language: Parametrized SupportedLanguage
        :returns: None
        """
        mock_telegram_user.language_code = language.value
        mock_context.user_data = {
            STATE_KEY: ConversationState.AWAITING_START_BIRTH_DATE.value,
            TIMESTAMP_KEY: TEST_STATE_TIMESTAMP,
            STATE_ID_KEY: TEST_STATE_ID,
        }
        set_message_text(mock_update=mock_update, text="01.01.1995")

        await handler.handle_birth_date_input(update=mock_update, context=mock_context)

        profile = await test_service_container.user_service.get_user_profile(
            TEST_USER_ID
        )
        assert profile is not None
        expected_tz = get_expected_timezone_for_language(language)
        assert profile.settings.timezone == expected_tz


@pytest.mark.integration
@pytest.mark.asyncio
class TestTimezoneHandlerPremiumUser:
    """Tests for Premium user timezone handler flows."""

    @pytest.fixture
    def handler(self, test_service_container: ServiceContainer) -> TimezoneHandler:
        return TimezoneHandler(services=test_service_container)

    @pytest.mark.parametrize("language", list(SupportedLanguage))
    async def test_premium_callback_shows_timezone_menu(
        self,
        handler: TimezoneHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
        language: SupportedLanguage,
    ) -> None:
        """Test Premium user sees timezone selection menu on callback.

        :param handler: TimezoneHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :param language: Parametrized SupportedLanguage
        :returns: None
        """
        await make_premium_user(test_service_container, mock_telegram_user)
        await test_service_container.user_service.update_user_settings(
            telegram_id=TEST_USER_ID, language=language.value
        )
        setup_timezone_callback(mock_update)
        mock_update.effective_user = mock_telegram_user

        await handler.handle_callback(update=mock_update, context=mock_context)

        mock_update.callback_query.edit_message_text.assert_called_once()
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert call_kwargs["text"], "Message text must be non-empty"
        assert call_kwargs.get("reply_markup") is not None

    @pytest.mark.parametrize(
        "callback_data,expected_tz",
        [
            (CALLBACK_TIMEZONE_UTC, "UTC"),
            (CALLBACK_TIMEZONE_MOSCOW, TIMEZONE_EUROPE_MOSCOW),
            (CALLBACK_TIMEZONE_WARSAW, TIMEZONE_EUROPE_WARSAW),
            (CALLBACK_TIMEZONE_MINSK, TIMEZONE_EUROPE_MINSK),
            (CALLBACK_TIMEZONE_NEW_YORK, TIMEZONE_AMERICA_NEW_YORK),
        ],
    )
    async def test_premium_select_from_keyboard_updates_timezone(
        self,
        handler: TimezoneHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
        callback_data: str,
        expected_tz: str,
    ) -> None:
        """Test Premium user selecting timezone from keyboard updates DB.

        :param handler: TimezoneHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :param callback_data: Callback data string
        :param expected_tz: Expected timezone value
        :returns: None
        """
        await make_premium_user(test_service_container, mock_telegram_user)
        setup_timezone_callback(mock_update, callback_data=callback_data)
        mock_update.effective_user = mock_telegram_user

        await handler.handle_selection_callback(
            update=mock_update, context=mock_context
        )

        profile = await test_service_container.user_service.get_user_profile(
            TEST_USER_ID
        )
        assert profile is not None
        assert profile.settings.timezone == expected_tz

    @pytest.mark.parametrize("language", list(SupportedLanguage))
    async def test_premium_manual_input_valid_iana_success(
        self,
        handler: TimezoneHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
        language: SupportedLanguage,
    ) -> None:
        """Test Premium user manual IANA timezone input succeeds.

        :param handler: TimezoneHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :param language: Parametrized SupportedLanguage
        :returns: None
        """
        await make_premium_user(test_service_container, mock_telegram_user)
        await test_service_container.user_service.update_user_settings(
            telegram_id=TEST_USER_ID, language=language.value
        )
        setup_awaiting_timezone_state(mock_context)
        set_message_text(mock_update=mock_update, text=TIMEZONE_EUROPE_LONDON)

        await handler.handle_input(update=mock_update, context=mock_context)

        profile = await test_service_container.user_service.get_user_profile(
            TEST_USER_ID
        )
        assert profile is not None
        assert profile.settings.timezone == TIMEZONE_EUROPE_LONDON

    @pytest.mark.parametrize("language", list(SupportedLanguage))
    async def test_premium_manual_input_invalid_iana_keeps_state(
        self,
        handler: TimezoneHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
        language: SupportedLanguage,
    ) -> None:
        """Test Premium user invalid IANA input keeps awaiting state.

        :param handler: TimezoneHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :param language: Parametrized SupportedLanguage
        :returns: None
        """
        await make_premium_user(test_service_container, mock_telegram_user)
        await test_service_container.user_service.update_user_settings(
            telegram_id=TEST_USER_ID, language=language.value
        )
        setup_awaiting_timezone_state(mock_context)
        set_message_text(mock_update=mock_update, text=TIMEZONE_INVALID)

        await handler.handle_input(update=mock_update, context=mock_context)

        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert len(reply_text) > 0
        assert (
            mock_context.user_data.get(STATE_KEY)
            == ConversationState.AWAITING_SETTINGS_TIMEZONE.value
        )

    @pytest.mark.parametrize("language", list(SupportedLanguage))
    async def test_premium_select_other_prompts_manual_input(
        self,
        handler: TimezoneHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
        language: SupportedLanguage,
    ) -> None:
        """Test Premium user selecting Other prompts for manual input.

        :param handler: TimezoneHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :param language: Parametrized SupportedLanguage
        :returns: None
        """
        await make_premium_user(test_service_container, mock_telegram_user)
        await test_service_container.user_service.update_user_settings(
            telegram_id=TEST_USER_ID, language=language.value
        )
        setup_timezone_callback(mock_update, callback_data=CALLBACK_TIMEZONE_OTHER)
        mock_update.effective_user = mock_telegram_user

        result = await handler.handle_selection_callback(
            update=mock_update, context=mock_context
        )

        assert result == ConversationState.AWAITING_SETTINGS_TIMEZONE.value
        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        assert call_kwargs["text"], "Manual input prompt must be shown"


@pytest.mark.integration
@pytest.mark.asyncio
class TestTimezoneHandlerTrialUser:
    """Tests for Trial user timezone access (same as Premium)."""

    @pytest.fixture
    def handler(self, test_service_container: ServiceContainer) -> TimezoneHandler:
        return TimezoneHandler(services=test_service_container)

    async def test_trial_user_can_change_timezone(
        self,
        handler: TimezoneHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test Trial user can change timezone via keyboard selection.

        :param handler: TimezoneHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :returns: None
        """
        await make_trial_user(test_service_container, mock_telegram_user)
        setup_timezone_callback(mock_update, callback_data=CALLBACK_TIMEZONE_MOSCOW)
        mock_update.effective_user = mock_telegram_user

        await handler.handle_selection_callback(
            update=mock_update, context=mock_context
        )

        profile = await test_service_container.user_service.get_user_profile(
            TEST_USER_ID
        )
        assert profile is not None
        assert profile.settings.timezone == TIMEZONE_EUROPE_MOSCOW


@pytest.mark.integration
@pytest.mark.asyncio
class TestTimezoneHandlerBasicUser:
    """Tests for Basic user access control (no timezone button)."""

    async def test_basic_user_settings_menu_no_timezone_button(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
    ) -> None:
        """Test Basic user does not see timezone button in settings menu.

        :param test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :returns: None
        """
        await make_registered_user(test_service_container, mock_telegram_user)
        dispatcher = SettingsDispatcher(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/settings")

        await dispatcher.handle(update=mock_update, context=mock_context)

        reply_markup = mock_update.message.reply_text.call_args.kwargs.get(
            "reply_markup"
        )
        assert reply_markup is not None
        callback_datas = []
        for row in reply_markup.inline_keyboard:
            for btn in row:
                if hasattr(btn, "callback_data") and btn.callback_data:
                    callback_datas.append(btn.callback_data)
        assert "settings_timezone" not in callback_datas


@pytest.mark.integration
@pytest.mark.asyncio
class TestTimezoneSchedulerApplication:
    """Tests for scheduler receiving correct trigger on timezone change."""

    @pytest.fixture
    def handler(self, test_service_container: ServiceContainer) -> TimezoneHandler:
        return TimezoneHandler(services=test_service_container)

    async def test_timezone_change_publishes_event_and_scheduler_receives_correct_trigger(
        self,
        handler: TimezoneHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test timezone change triggers scheduler with correct timezone.

        Preconditions:
            - Premium user with DAILY schedule, 10:00, timezone UTC

        Test Steps:
            1. User selects Europe/Moscow via callback
            2. Event published, handle_user_settings_changed runs
            3. Scheduler receives schedule_job with trigger.timezone

        Post-conditions:
            - schedule_job called with trigger.timezone == Europe/Moscow

        :param handler: TimezoneHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :returns: None
        """
        register_event_listeners(test_service_container)
        user_service = test_service_container.user_service
        await make_premium_user(test_service_container, mock_telegram_user)
        await user_service.update_user_settings(
            telegram_id=TEST_USER_ID,
            notification_frequency=NotificationFrequency.DAILY,
            notifications_time=datetime_time(10, 0),
            timezone=DEFAULT_TIMEZONE,
        )

        scheduler_client = AsyncMock()
        scheduler_client.schedule_job.return_value = True

        container_for_listener = MagicMock()
        container_for_listener.get_scheduler_client.return_value = scheduler_client
        container_for_listener.get_user_service.return_value = user_service

        setup_timezone_callback(mock_update, callback_data=CALLBACK_TIMEZONE_MOSCOW)
        mock_update.effective_user = mock_telegram_user

        with patch(
            target="src.bot.event_listeners.ServiceContainer",
            return_value=container_for_listener,
        ):
            await handler.handle_selection_callback(
                update=mock_update, context=mock_context
            )

        scheduler_client.schedule_job.assert_awaited_once()
        call_kwargs = scheduler_client.schedule_job.call_args.kwargs
        trigger = call_kwargs["trigger"]
        assert trigger.timezone == TIMEZONE_EUROPE_MOSCOW
        assert trigger.hour == 10
        assert trigger.minute == 0

    async def test_timezone_change_reschedules_with_correct_time(
        self,
        handler: TimezoneHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test timezone change preserves schedule time (weekly Friday 14:30).

        :param handler: TimezoneHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :returns: None
        """
        register_event_listeners(test_service_container)
        user_service = test_service_container.user_service
        await make_premium_user(test_service_container, mock_telegram_user)
        await user_service.update_user_settings(
            telegram_id=TEST_USER_ID,
            notification_frequency=NotificationFrequency.WEEKLY,
            notifications_day=WeekDay.FRIDAY,
            notifications_time=datetime_time(14, 30),
            timezone=TIMEZONE_EUROPE_WARSAW,
        )

        scheduler_client = AsyncMock()
        scheduler_client.schedule_job.return_value = True

        container_for_listener = MagicMock()
        container_for_listener.get_scheduler_client.return_value = scheduler_client
        container_for_listener.get_user_service.return_value = user_service

        setup_timezone_callback(mock_update, callback_data=CALLBACK_TIMEZONE_MOSCOW)
        mock_update.effective_user = mock_telegram_user

        with patch(
            target="src.bot.event_listeners.ServiceContainer",
            return_value=container_for_listener,
        ):
            await handler.handle_selection_callback(
                update=mock_update, context=mock_context
            )

        scheduler_client.schedule_job.assert_awaited_once()
        call_kwargs = scheduler_client.schedule_job.call_args.kwargs
        trigger = call_kwargs["trigger"]
        assert trigger.timezone == TIMEZONE_EUROPE_MOSCOW
        assert trigger.hour == 14
        assert trigger.minute == 30
        assert trigger.day_of_week == WEEKDAY_MAP[WeekDay.FRIDAY]


@pytest.mark.integration
@pytest.mark.asyncio
class TestTimezoneOutputAllLanguages:
    """Tests for timezone output verification across all languages."""

    @pytest.fixture
    def handler(self, test_service_container: ServiceContainer) -> TimezoneHandler:
        return TimezoneHandler(services=test_service_container)

    @pytest.mark.parametrize("language", list(SupportedLanguage))
    async def test_timezone_success_message_in_all_languages(
        self,
        handler: TimezoneHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
        language: SupportedLanguage,
    ) -> None:
        """Test timezone success message contains new timezone in all languages.

        :param handler: TimezoneHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :param language: Parametrized SupportedLanguage
        :returns: None
        """
        await make_premium_user(test_service_container, mock_telegram_user)
        await test_service_container.user_service.update_user_settings(
            telegram_id=TEST_USER_ID, language=language.value
        )
        setup_timezone_callback(mock_update, callback_data=CALLBACK_TIMEZONE_MOSCOW)
        mock_update.effective_user = mock_telegram_user

        await handler.handle_selection_callback(
            update=mock_update, context=mock_context
        )

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        text = call_kwargs["text"]
        assert TIMEZONE_EUROPE_MOSCOW in text
        assert text  # Non-empty response

    @pytest.mark.parametrize("language", list(SupportedLanguage))
    async def test_timezone_invalid_message_in_all_languages(
        self,
        handler: TimezoneHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
        test_service_container: ServiceContainer,
        language: SupportedLanguage,
    ) -> None:
        """Test invalid timezone error message in all languages.

        :param handler: TimezoneHandler instance
        :param mock_update: Mock Telegram Update
        :param mock_context: Mock Telegram Context
        :param mock_telegram_user: Mock Telegram User
        :param test_service_container: ServiceContainer
        :param language: Parametrized SupportedLanguage
        :returns: None
        """
        await make_premium_user(test_service_container, mock_telegram_user)
        await test_service_container.user_service.update_user_settings(
            telegram_id=TEST_USER_ID, language=language.value
        )
        setup_awaiting_timezone_state(mock_context)
        set_message_text(mock_update=mock_update, text=TIMEZONE_INVALID)

        await handler.handle_input(update=mock_update, context=mock_context)

        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert len(reply_text) > 0
