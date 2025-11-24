"""Unit tests for the bot application, focusing on LifeWeeksBot class behavior."""

import asyncio
from types import SimpleNamespace
from typing import List, Type
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from telegram.error import NetworkError, RetryAfter, TimedOut
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

from src.bot.application import HANDLERS, LifeWeeksBot
from src.bot.constants import (
    COMMAND_CANCEL,
    COMMAND_HELP,
    COMMAND_SETTINGS,
    COMMAND_START,
    COMMAND_SUBSCRIPTION,
    COMMAND_UNKNOWN,
    COMMAND_VISUALIZE,
    COMMAND_WEEKS,
)


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


class TestHandlers:
    """Tests for the HANDLERS constant mapping."""

    def test_handlers_mapping_contains_all_commands(self) -> None:
        """Verify that the HANDLERS dictionary contains all expected command keys.

        :returns: None
        :rtype: None
        """
        expected_commands = [
            COMMAND_START,
            COMMAND_WEEKS,
            COMMAND_SETTINGS,
            COMMAND_VISUALIZE,
            COMMAND_HELP,
            COMMAND_SUBSCRIPTION,
            COMMAND_CANCEL,
            COMMAND_UNKNOWN,
        ]
        for command in expected_commands:
            assert command in HANDLERS, f"Command '{command}' is missing from HANDLERS"

    def test_handlers_have_correct_structure(self) -> None:
        """Ensure every handler configuration in HANDLERS has the required keys.

        :returns: None
        :rtype: None
        """
        for command, config in HANDLERS.items():
            assert "class" in config, f"Handler for '{command}' is missing 'class'"
            assert (
                "callbacks" in config
            ), f"Handler for '{command}' is missing 'callbacks'"

    def test_text_input_handlers_have_waiting_states(self) -> None:
        """Verify handlers with 'text_input' also have 'waiting_states' defined.

        :returns: None
        :rtype: None
        """
        for command, config in HANDLERS.items():
            if "text_input" in config:
                assert (
                    "waiting_states" in config
                ), f"Handler '{command}' with 'text_input' is missing 'waiting_states'"
                assert isinstance(
                    config["waiting_states"], list
                ), f"Handler '{command}' waiting_states should be a list"


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
        with patch.object(bot, "_register_handlers") as mock_register, patch.object(
            bot, "_setup_scheduler"
        ) as mock_setup_scheduler:
            bot.setup()
            mock_register.assert_called_once()
            mock_setup_scheduler.assert_called_once()

        assert bot._app is mock_application_builder
        mock_application_logger.info.assert_any_call("Setting up bot application")

    def test_register_handlers_registers_all_types(
        self, bot: LifeWeeksBot, mock_app: MagicMock
    ) -> None:
        """Ensure _register_handlers registers command, callback, and message handlers.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :returns: None
        :rtype: None
        """
        bot._app = mock_app
        bot._register_handlers()
        command_handlers = _get_handlers_by_type(bot._app, CommandHandler)
        callback_handlers = _get_handlers_by_type(bot._app, CallbackQueryHandler)
        message_handlers = _get_handlers_by_type(bot._app, MessageHandler)
        assert len(command_handlers) > 0
        assert len(callback_handlers) > 0
        assert len(message_handlers) > 0

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
        with patch.object(bot, "_register_handlers"), patch.object(
            bot, "_setup_scheduler"
        ):
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
            "Failed to set up weekly notification scheduler: Test error"
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

    def test_start_runs_polling_and_scheduler(
        self,
        bot: LifeWeeksBot,
        mock_start_scheduler: MagicMock,
        mock_app: MagicMock,
        mock_scheduler: MagicMock,
    ) -> None:
        """Ensure start() runs polling and starts the scheduler if it exists.

        :param bot: The bot instance
        :type bot: LifeWeeksBot
        :param mock_start_scheduler: Mocked start_scheduler function
        :type mock_start_scheduler: MagicMock
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_scheduler: Mocked scheduler instance
        :type mock_scheduler: MagicMock
        :returns: None
        :rtype: None
        """
        bot._app = mock_app
        bot._scheduler = mock_scheduler
        bot.start()
        bot._app.run_polling.assert_called_once()
        mock_start_scheduler.assert_called_once_with(mock_scheduler)

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
        bot._waiting_states = {
            "start_state": COMMAND_START,
            "settings_state": COMMAND_SETTINGS,
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

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            update1 = Mock()
            context1 = SimpleNamespace(user_data={"waiting_for": "start_state"})
            loop.run_until_complete(bot._universal_text_handler(update1, context1))
            start_handler.handle_birth_date_input.assert_called_once()
            unknown_handler.handle.assert_not_called()
            update2 = Mock()
            context2 = SimpleNamespace(user_data={"waiting_for": "settings_state"})
            loop.run_until_complete(bot._universal_text_handler(update2, context2))
            unknown_handler.handle.assert_called_once()
            unknown_handler.handle.reset_mock()
            update3 = Mock()
            context3 = SimpleNamespace(user_data={})
            loop.run_until_complete(bot._universal_text_handler(update3, context3))
            unknown_handler.handle.assert_called_once()
        finally:
            loop.close()

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
        bot._app = mock_app
        with patch("src.bot.application.HANDLERS", mock_handlers), patch.object(
            bot, "_universal_text_handler"
        ):
            bot._register_handlers()
        message_handlers = _get_handlers_by_type(bot._app, MessageHandler)
        registered_callbacks = [h.callback for h in message_handlers]
        assert mock_handlers["test_cmd"]["class"]().handle in registered_callbacks

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
        with patch.object(bot, "_register_handlers"), patch.object(
            bot, "_setup_scheduler"
        ):
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

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot._error_handler(update, context))
            mock_application_logger.warning.assert_called_once()
            assert "Network error occurred" in str(
                mock_application_logger.warning.call_args
            )
        finally:
            loop.close()

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

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot._error_handler(update, context))
            mock_application_logger.warning.assert_called_once()
            assert "Rate limit exceeded" in str(
                mock_application_logger.warning.call_args
            )
            assert "60" in str(mock_application_logger.warning.call_args)
        finally:
            loop.close()

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

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot._error_handler(update, context))
            mock_application_logger.warning.assert_called_once()
            assert "Request timeout occurred" in str(
                mock_application_logger.warning.call_args
            )
        finally:
            loop.close()

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

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot._error_handler(update, context))
            mock_application_logger.error.assert_called_once()
            assert "Unhandled exception occurred" in str(
                mock_application_logger.error.call_args
            )
        finally:
            loop.close()

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

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot._error_handler(mock_update, context))
            mock_bot.send_message.assert_called_once_with(
                chat_id=12345,
                text=(
                    "Sorry, an unexpected error occurred. "
                    "Please try again later or use /help for assistance."
                ),
            )
        finally:
            loop.close()

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

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot._error_handler(mock_update, context))
            # Should log error about failed message send
            error_calls = [
                call
                for call in mock_application_logger.error.call_args_list
                if "Failed to send error notification" in str(call)
            ]
            assert len(error_calls) > 0
        finally:
            loop.close()

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

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot._error_handler(update, context))
            # Should log error but not try to send message
            mock_application_logger.error.assert_called_once()
        finally:
            loop.close()

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

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot._error_handler(mock_update, context))
            # Should log error but not try to send message
            mock_application_logger.error.assert_called_once()
        finally:
            loop.close()
