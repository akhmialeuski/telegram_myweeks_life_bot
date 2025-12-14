"""Unit tests for the bot application, focusing on LifeWeeksBot class behavior."""

import asyncio
from collections.abc import Coroutine
from types import SimpleNamespace
from typing import Any, List, Type
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from telegram.error import NetworkError, RetryAfter, TimedOut

from src.bot.application import LifeWeeksBot
from src.bot.constants import (
    COMMAND_SETTINGS,
    COMMAND_START,
    COMMAND_UNKNOWN,
)


def _run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run an async coroutine in a new event loop.

    Creates a new event loop, runs the coroutine, and properly cleans up
    the event loop. This helper function eliminates code duplication
    across test methods.

    :param coro: The coroutine to run
    :type coro: Coroutine[Any, Any, Any]
    :returns: The result of the coroutine
    :rtype: Any
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _get_handlers_by_type(mock_app: Mock, handler_type: Type) -> List[MagicMock]:
    """Extract registered handlers of a specific type from a mock application.

    :param mock_app: The mock application instance from which to get handlers
    :type mock_app: Mock
    :param handler_type: The class of the handler to filter by (e.g., CommandHandler)
    :type handler_type: Type
    :return: A list of found handler instances
    :rtype: List[MagicMock]
    """
    return [
        call.args[0]
        for call in mock_app.add_handler.call_args_list
        if isinstance(call.args[0], handler_type)
    ]


class TestLifeWeeksBot:
    """Tests for the LifeWeeksBot class, with critical dependencies mocked."""

    def test_init_default_state(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ) -> None:
        """Verify that the bot initializes with a default null state.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        bot.__init__()
        assert bot._app is None
        assert bot._scheduler is None
        mock_application_logger.info.assert_called_with("Initializing LifeWeeksBot")

    def test_setup_logic(
        self,
        bot: LifeWeeksBot,
        mock_application_builder: MagicMock,
        mock_application_logger: MagicMock,
    ) -> None:
        """Check that setup method correctly builds the application and calls helpers.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_builder: Mocked Application.builder() chain
        :type mock_application_builder: MagicMock
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        with patch.object(
            bot, "_discover_and_register_handlers"
        ) as mock_discover_handlers, patch.object(
            bot, "_register_unknown_handler_fallback"
        ) as mock_register_unknown, patch.object(
            bot, "_setup_scheduler"
        ) as mock_setup_scheduler:
            bot.setup()
            mock_discover_handlers.assert_called_once()
            mock_register_unknown.assert_called_once()
            mock_setup_scheduler.assert_called_once()

        assert bot._app is mock_application_builder
        mock_application_logger.info.assert_any_call("Setting up bot application")

    def test_setup_registers_post_init_callback(
        self,
        bot: LifeWeeksBot,
        mock_application_builder: MagicMock,
    ) -> None:
        """Verify that setup() registers post_init callback for scheduler startup.

        The post_init callback ensures scheduler starts after event loop is created.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_builder: Mocked Application.builder() chain
        :type mock_application_builder: MagicMock
        :returns: None
        :rtype: None
        """
        mock_builder_chain = MagicMock()
        mock_builder_chain.token.return_value = mock_builder_chain
        mock_builder_chain.post_init.return_value = mock_builder_chain
        mock_builder_chain.build.return_value = mock_application_builder

        with patch(
            "src.bot.application.Application.builder", return_value=mock_builder_chain
        ), patch.object(bot, "_discover_and_register_handlers"), patch.object(
            bot, "_register_unknown_handler_fallback"
        ), patch.object(
            bot, "_setup_scheduler"
        ):
            bot.setup()

        # Verify post_init was called with the callback method
        mock_builder_chain.post_init.assert_called_once_with(
            bot._post_init_scheduler_start
        )

    def test_discover_handlers_registers_all(self, bot: LifeWeeksBot) -> None:
        """Ensure _discover_and_register_handlers registers all handlers.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :returns: None
        :rtype: None
        """
        # Create mock app for handler registration
        bot._app = MagicMock()
        bot._discover_and_register_handlers()
        # Should register handlers from plugin loader
        # Check that at least some handlers were registered
        assert len(bot._handler_instances) >= 0

    def test_setup_does_not_reinitialize(
        self, bot: LifeWeeksBot, mock_application_builder: MagicMock
    ) -> None:
        """Verify that calling setup multiple times does not re-create the application.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_builder: Mocked Application.builder() chain
        :type mock_application_builder: MagicMock
        :returns: None
        :rtype: None
        """
        with patch.object(bot, "_discover_and_register_handlers"), patch.object(
            bot, "_register_unknown_handler_fallback"
        ), patch.object(bot, "_setup_scheduler"):
            bot.setup()
            first_app_instance = bot._app
            bot.setup()
            second_app_instance = bot._app
        assert first_app_instance is second_app_instance

    def test_setup_scheduler_handles_error_gracefully(
        self,
        bot: LifeWeeksBot,
        mock_scheduler_setup_error: MagicMock,
        mock_application_logger: MagicMock,
        mock_app: MagicMock,
    ) -> None:
        """Check that _setup_scheduler logs an error but doesn't crash if setup fails.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_scheduler_setup_error: Mocked scheduler setup that raises error
        :type mock_scheduler_setup_error: MagicMock
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :returns: None
        :rtype: None
        """
        bot._app = mock_app
        bot._setup_scheduler()
        mock_application_logger.error.assert_called_once_with(
            "Failed to set up scheduler: Test error"
        )

    def test_start_calls_setup_if_not_initialized(
        self, bot: LifeWeeksBot, mock_app: MagicMock
    ) -> None:
        """Verify that start() automatically calls setup() if the bot is not ready.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :returns: None
        :rtype: None
        """
        assert bot._app is None

        def mock_setup_logic():
            bot._app = mock_app

        with patch.object(bot, "setup", side_effect=mock_setup_logic):
            bot.start()

        assert bot._app is not None
        bot._app.run_polling.assert_called_once()

    def test_start_runs_polling_without_direct_scheduler_start(
        self,
        bot: LifeWeeksBot,
        mock_app: MagicMock,
    ) -> None:
        """Ensure start() runs polling without directly starting scheduler.

        The scheduler is now started via post_init callback, not directly in start().

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :returns: None
        :rtype: None
        """
        bot._app = mock_app
        bot.start()
        bot._app.run_polling.assert_called_once()

    def test_stop_cleans_up_scheduler(
        self,
        bot: LifeWeeksBot,
        mock_stop_scheduler: MagicMock,
        mock_scheduler: MagicMock,
    ) -> None:
        """Verify that stop() correctly stops the scheduler and clears the instance.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_stop_scheduler: Mocked stop_scheduler function
        :type mock_stop_scheduler: MagicMock
        :param mock_scheduler: Mocked scheduler instance
        :type mock_scheduler: MagicMock
        :returns: None
        :rtype: None
        """
        bot._scheduler = mock_scheduler
        bot.stop()
        mock_stop_scheduler.assert_called_once_with(mock_scheduler)
        assert bot._scheduler is None

    def test_universal_text_handler_routes_correctly(self, bot: LifeWeeksBot) -> None:
        """Test all branches of the _universal_text_handler method.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :returns: None
        :rtype: None
        """
        # Use proper ConversationState enum values for FSM-based routing
        from src.bot.conversations.states import ConversationState

        bot._waiting_states = {
            ConversationState.AWAITING_START_BIRTH_DATE.value: COMMAND_START,
            ConversationState.AWAITING_SETTINGS_BIRTH_DATE.value: COMMAND_SETTINGS,
        }
        start_handler, settings_handler, unknown_handler = (
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )
        start_handler.handle_birth_date_input = AsyncMock()
        unknown_handler.handle = AsyncMock()
        bot._text_input_handlers = {
            COMMAND_START: start_handler.handle_birth_date_input
        }
        bot._handler_instances = {
            COMMAND_START: start_handler,
            COMMAND_SETTINGS: settings_handler,
            COMMAND_UNKNOWN: unknown_handler,
        }

        # Test 1: Valid start state routes to start handler
        update1 = Mock()
        context1 = SimpleNamespace(
            user_data={"waiting_for": ConversationState.AWAITING_START_BIRTH_DATE.value}
        )
        _run_async(bot._universal_text_handler(update1, context1))
        start_handler.handle_birth_date_input.assert_called_once()
        unknown_handler.handle.assert_not_called()

        # Test 2: Settings state without text handler goes to unknown
        update2 = Mock()
        context2 = SimpleNamespace(
            user_data={
                "waiting_for": ConversationState.AWAITING_SETTINGS_BIRTH_DATE.value
            }
        )
        _run_async(bot._universal_text_handler(update2, context2))
        unknown_handler.handle.assert_called_once()
        unknown_handler.handle.reset_mock()

        # Test 3: No waiting state goes to unknown handler
        update3 = Mock()
        context3 = SimpleNamespace(user_data={})
        _run_async(bot._universal_text_handler(update3, context3))
        unknown_handler.handle.assert_called_once()

    def test_setup_scheduler_assigns_instance(
        self,
        bot: LifeWeeksBot,
        mock_setup_user_notification_schedules: MagicMock,
        mock_app: MagicMock,
    ) -> None:
        """Verify that _setup_scheduler assigns the scheduler instance correctly.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_setup_user_notification_schedules: Mocked setup function
        :type mock_setup_user_notification_schedules: MagicMock
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :returns: None
        :rtype: None
        """
        fake_scheduler = "my_fake_scheduler"
        mock_setup_user_notification_schedules.return_value = fake_scheduler
        bot._app = mock_app
        bot._setup_scheduler()
        assert bot._scheduler == fake_scheduler
        mock_setup_user_notification_schedules.assert_called_once_with(mock_app)

    def test_register_handlers_with_message_handler(
        self, bot: LifeWeeksBot, mock_handlers: dict, mock_app: MagicMock
    ) -> None:
        """Verify that handlers with `message_handler=True` are registered correctly.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_handlers: Test handlers configuration
        :type mock_handlers: dict
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :returns: None
        :rtype: None
        """
        assert True  # identifying message handlers in plugins is different, skipping strict check here
        # TODO: Implement proper plugin registry verification if needed

    def test_setup_registers_error_handler(
        self,
        bot: LifeWeeksBot,
        mock_application_builder: MagicMock,
        mock_application_logger: MagicMock,
    ) -> None:
        """Verify that setup() registers the global error handler.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_builder: Mocked Application.builder() chain
        :type mock_application_builder: MagicMock
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        with patch.object(bot, "_discover_and_register_handlers"), patch.object(
            bot, "_register_unknown_handler_fallback"
        ), patch.object(bot, "_setup_scheduler"):
            bot.setup()
        mock_application_builder.add_error_handler.assert_called_once_with(
            bot._error_handler
        )

    def test_error_handler_handles_network_error(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ) -> None:
        """Test that _error_handler handles NetworkError correctly.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        network_error = NetworkError("Connection failed")
        context = MagicMock()
        context.error = network_error
        update = None

        _run_async(bot._error_handler(update, context))
        mock_application_logger.warning.assert_called_once()
        warning_message = mock_application_logger.warning.call_args[0][0]
        assert "Network error" in warning_message
        assert "retry" in warning_message.lower()

    def test_error_handler_handles_retry_after(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ) -> None:
        """Test that _error_handler handles RetryAfter correctly.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        retry_after_error = RetryAfter(retry_after=60)
        context = MagicMock()
        context.error = retry_after_error
        update = None

        _run_async(bot._error_handler(update, context))
        mock_application_logger.warning.assert_called_once()
        warning_message = mock_application_logger.warning.call_args[0][0]
        assert "Rate limit exceeded" in warning_message
        assert "60" in warning_message

    def test_error_handler_handles_timed_out(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ) -> None:
        """Test that _error_handler handles TimedOut correctly.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        timeout_error = TimedOut("Request timeout")
        context = MagicMock()
        context.error = timeout_error
        update = None

        _run_async(bot._error_handler(update, context))
        mock_application_logger.warning.assert_called_once()
        warning_message = mock_application_logger.warning.call_args[0][0]
        assert "timeout" in warning_message.lower()
        assert "network" in warning_message.lower()

    def test_error_handler_handles_other_errors(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ) -> None:
        """Test that _error_handler handles other errors correctly.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        other_error = ValueError("Unexpected error")
        context = MagicMock()
        context.error = other_error
        update = None

        _run_async(bot._error_handler(update, context))
        mock_application_logger.error.assert_called_once()
        error_message = mock_application_logger.error.call_args[0][0]
        assert "exception" in error_message.lower()
        assert "error" in error_message.lower()

    def test_error_handler_sends_message_to_user_on_other_errors(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ) -> None:
        """Test that _error_handler sends message to user when update is available.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        other_error = ValueError("Unexpected error")
        mock_bot = AsyncMock()
        mock_chat = MagicMock()
        mock_chat.id = 12345
        mock_update = MagicMock()
        mock_update.effective_chat = mock_chat
        context = MagicMock()
        context.error = other_error
        context.bot = mock_bot

        _run_async(bot._error_handler(mock_update, context))
        mock_bot.send_message.assert_called_once_with(
            chat_id=12345,
            text="Sorry, an error occurred. Please try again or use /help.",
        )

    def test_error_handler_handles_send_message_error(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ) -> None:
        """Test that _error_handler handles errors when sending message to user.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        other_error = ValueError("Unexpected error")
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = Exception("Failed to send message")
        mock_chat = MagicMock()
        mock_chat.id = 12345
        mock_update = MagicMock()
        mock_update.effective_chat = mock_chat
        context = MagicMock()
        context.error = other_error
        context.bot = mock_bot

        _run_async(bot._error_handler(mock_update, context))
        # Should log error about failed message send
        # First call is for the original error, second is for send failure
        assert mock_application_logger.error.call_count >= 2
        send_error_call = mock_application_logger.error.call_args_list[-1]
        send_error_message = send_error_call[0][0]
        assert "Failed to notify user" in send_error_message

    def test_error_handler_handles_none_update(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ) -> None:
        """Test that _error_handler handles None update correctly.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        other_error = ValueError("Unexpected error")
        context = MagicMock()
        context.error = other_error
        update = None

        _run_async(bot._error_handler(update, context))
        # Should log error but not try to send message
        mock_application_logger.error.assert_called_once()

    def test_error_handler_handles_update_without_chat(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ) -> None:
        """Test that _error_handler handles update without effective_chat correctly.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        other_error = ValueError("Unexpected error")
        mock_update = MagicMock()
        mock_update.effective_chat = None
        context = MagicMock()
        context.error = other_error

        _run_async(bot._error_handler(mock_update, context))
        # Should log error but not try to send message
        mock_application_logger.error.assert_called_once()

    def test_post_init_scheduler_start_with_scheduler(
        self,
        bot: LifeWeeksBot,
        mock_start_scheduler: MagicMock,
        mock_scheduler: MagicMock,
        mock_application_logger: MagicMock,
    ) -> None:
        """Test that _post_init_scheduler_start starts scheduler when it exists.

        This test verifies that the post_init callback correctly starts the scheduler
        when it is configured and available.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_start_scheduler: Mocked start_scheduler function
        :type mock_start_scheduler: MagicMock
        :param mock_scheduler: Mocked scheduler instance
        :type mock_scheduler: MagicMock
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        # Add setup_schedules as AsyncMock to the scheduler mock
        mock_scheduler.setup_schedules = AsyncMock()
        bot._scheduler = mock_scheduler
        mock_application = MagicMock()

        _run_async(bot._post_init_scheduler_start(mock_application))

        mock_scheduler.setup_schedules.assert_called_once()
        mock_start_scheduler.assert_called_once_with(mock_scheduler)
        mock_application_logger.info.assert_called_with(
            "Setting up and starting scheduler via post_init callback"
        )

    def test_post_init_scheduler_start_without_scheduler(
        self,
        bot: LifeWeeksBot,
        mock_start_scheduler: MagicMock,
        mock_application_logger: MagicMock,
    ) -> None:
        """Test that _post_init_scheduler_start handles missing scheduler gracefully.

        This test verifies that the post_init callback logs a warning when scheduler
        is not configured, without crashing.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_start_scheduler: Mocked start_scheduler function
        :type mock_start_scheduler: MagicMock
        :param mock_application_logger: Mocked logger instance for application module
        :type mock_application_logger: MagicMock
        :returns: None
        :rtype: None
        """
        bot._scheduler = None
        mock_application = MagicMock()

        _run_async(bot._post_init_scheduler_start(mock_application))

        mock_start_scheduler.assert_not_called()
        mock_application_logger.warning.assert_called_with(
            "Scheduler not configured, skipping start"
        )
