"""Unit tests for bot application.

Tests all functionality of the LifeWeeksBot application class
with proper mocking, edge cases, and error handling coverage.
"""

from unittest.mock import Mock, patch

import pytest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
)

from src.bot.application import COMMAND_HANDLERS, LifeWeeksBot
from src.bot.handlers import (
    WAITING_USER_INPUT,
    command_cancel,
    command_help,
    command_settings,
    command_subscription,
    command_subscription_callback,
    command_visualize,
    command_weeks,
)


class TestCommandHandlers:
    """Test suite for COMMAND_HANDLERS mapping."""

    def test_command_handlers_mapping(self):
        """Test that COMMAND_HANDLERS contains all expected commands.

        :returns: None
        """
        expected_commands = {
            "weeks": command_weeks,
            "visualize": command_visualize,
            "help": command_help,
            "cancel": command_cancel,
            "settings": command_settings,
            "subscription": command_subscription,
        }

        assert COMMAND_HANDLERS == expected_commands

    def test_command_handlers_types(self):
        """Test that all command handlers are callable.

        :returns: None
        """
        for command, handler in COMMAND_HANDLERS.items():
            assert callable(handler), f"Handler for {command} is not callable"

    def test_command_handlers_completeness(self):
        """Test that all required commands are present.

        :returns: None
        """
        required_commands = [
            "weeks",
            "visualize",
            "help",
            "cancel",
            "settings",
            "subscription",
        ]

        for command in required_commands:
            assert (
                command in COMMAND_HANDLERS
            ), f"Command {command} missing from COMMAND_HANDLERS"


class TestLifeWeeksBot:
    """Test suite for LifeWeeksBot class."""

    @pytest.fixture
    def bot(self):
        """Create LifeWeeksBot instance for testing.

        :returns: LifeWeeksBot instance
        :rtype: LifeWeeksBot
        """
        return LifeWeeksBot()

    @pytest.fixture
    def mock_application(self):
        """Create mock Application instance.

        :returns: Mock Application instance
        :rtype: Mock
        """
        app = Mock(spec=Application)
        app.add_handler = Mock()
        app.run_polling = Mock()
        return app

    def test_init_default_state(self, bot):
        """Test bot initialization with default state.

        :param bot: LifeWeeksBot instance
        :returns: None
        """
        assert bot._app is None

    @patch("src.bot.application.logger")
    def test_init_logging(self, mock_logger):
        """Test bot initialization logging.

        :param mock_logger: Mock logger
        :returns: None
        """
        LifeWeeksBot()

        mock_logger.info.assert_called_once_with("Initializing LifeWeeksBot")

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    def test_setup_success(self, mock_logger, mock_application_class, bot):
        """Test successful bot setup.

        :param mock_logger: Mock logger
        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.setup()

        # Assert
        assert bot._app is mock_app
        # Check that setup logging was called
        setup_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Setting up bot application" in str(call)
        ]
        assert len(setup_calls) > 0

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    def test_setup_conversation_handler_registration(
        self, mock_logger, mock_application_class, bot
    ):
        """Test conversation handler registration during setup.

        :param mock_logger: Mock logger
        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.setup()

        # Assert
        # Should register conversation handler first
        first_call = mock_app.add_handler.call_args_list[0]
        assert isinstance(first_call[0][0], ConversationHandler)

        # Check conversation handler configuration
        conv_handler = first_call[0][0]
        assert len(conv_handler.entry_points) == 1
        assert isinstance(conv_handler.entry_points[0], CommandHandler)
        assert conv_handler.entry_points[0].commands == {"start"}

        # Check states configuration
        assert WAITING_USER_INPUT in conv_handler.states
        assert len(conv_handler.states[WAITING_USER_INPUT]) == 1

        # Check fallbacks
        assert len(conv_handler.fallbacks) == 1
        assert isinstance(conv_handler.fallbacks[0], CommandHandler)
        assert conv_handler.fallbacks[0].commands == {"cancel"}

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    def test_setup_command_handlers_registration(
        self, mock_logger, mock_application_class, bot
    ):
        """Test command handlers registration during setup.

        :param mock_logger: Mock logger
        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.setup()

        # Assert
        # Should register conversation handler + command handlers + callback handlers + settings text handler + unknown message handler
        expected_handlers = (
            1 + len(COMMAND_HANDLERS) + 3 + 1 + 1
        )  # conv + commands + 3 callback handlers + settings text + unknown
        assert mock_app.add_handler.call_count == expected_handlers

        # Check that all command handlers are registered
        command_calls = mock_app.add_handler.call_args_list[
            1:-5
        ]  # Skip conv handler, callback handlers, settings text handler, and unknown message handler
        registered_commands = set()

        for call in command_calls:
            handler = call[0][0]
            assert isinstance(handler, CommandHandler)
            registered_commands.update(handler.commands)

        expected_commands = set(COMMAND_HANDLERS.keys())
        assert registered_commands == expected_commands

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    def test_setup_callback_handler_registration(
        self, mock_logger, mock_application_class, bot
    ):
        """Test callback query handler registration during setup.

        :param mock_logger: Mock logger
        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.setup()

        # Assert
        # Check that subscription callback handler is registered
        callback_calls = mock_app.add_handler.call_args_list
        subscription_handler_found = False

        for call in callback_calls:
            handler = call[0][0]
            if (
                isinstance(handler, CallbackQueryHandler)
                and handler.callback == command_subscription_callback
            ):
                assert handler.pattern.pattern == "^subscription_"
                subscription_handler_found = True
                break

        assert subscription_handler_found, "Subscription callback handler not found"

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    def test_setup_logging_messages(self, mock_logger, mock_application_class, bot):
        """Test setup logging messages.

        :param mock_logger: Mock logger
        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.setup()

        # Assert
        expected_info_calls = [
            "Setting up bot application",
        ]

        # Check that all expected info messages were logged
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        for expected_msg in expected_info_calls:
            assert expected_msg in info_calls

        # Check debug messages for individual command handlers and callback handler
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        for command in COMMAND_HANDLERS.keys():
            expected_debug = f"Registered command handler: /{command}"
            assert expected_debug in debug_calls

        # Check callback handler debug message
        assert "Registered callback query handler for subscription" in debug_calls

        # Check unknown message handler debug message
        assert "Registered handler for unknown messages" in debug_calls

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    def test_setup_final_log_message(self, mock_logger, mock_application_class, bot):
        """Test final setup log message contains all commands.

        :param mock_logger: Mock logger
        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.setup()

        # Assert
        final_log_call = mock_logger.info.call_args_list[-1]
        final_message = final_log_call[0][0]

        # Should contain /start and all commands from COMMAND_HANDLERS
        assert "/start" in final_message
        for command in COMMAND_HANDLERS.keys():
            assert f"/{command}" in final_message

    @patch("src.bot.application.Application")
    def test_setup_multiple_calls(self, mock_application_class, bot):
        """Test multiple setup calls don't create multiple applications.

        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.setup()
        first_app = bot._app

        bot.setup()
        second_app = bot._app

        # Assert
        assert first_app is second_app
        # Builder should be called only once since setup checks if _app already exists
        assert mock_application_class.builder.call_count == 1

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    @patch("src.bot.application.setup_user_notification_schedules")
    def test_start_without_setup(self, mock_setup_scheduler, mock_logger, mock_application_class, bot):
        """Test start method calls setup if not already done.

        :param mock_setup_scheduler: Mock setup_user_notification_schedules function
        :param mock_logger: Mock logger
        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_app.run_polling = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )
        mock_setup_scheduler.return_value = True

        # Execute
        bot.start()

        # Assert
        assert bot._app is mock_app
        mock_app.run_polling.assert_called_once()
        start_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Starting Life Weeks Bot" in str(call)
        ]
        assert len(start_calls) > 0

    @patch("src.bot.application.logger")
    def test_start_with_existing_setup(self, mock_logger, bot):
        """Test start method with pre-existing setup.

        :param mock_logger: Mock logger
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.run_polling = Mock()
        bot._app = mock_app

        # Execute
        bot.start()

        # Assert
        mock_app.run_polling.assert_called_once()
        start_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Starting Life Weeks Bot" in str(call)
        ]
        assert len(start_calls) > 0

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    def test_start_logging(self, mock_logger, mock_application_class, bot):
        """Test start method logging.

        :param mock_logger: Mock logger
        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_app.run_polling = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.start()

        # Assert
        # Should log both setup and start messages
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert "Starting Life Weeks Bot" in info_calls

    @patch("src.bot.application.TOKEN", "test_token")
    @patch("src.bot.application.Application")
    def test_setup_uses_correct_token(self, mock_application_class, bot):
        """Test setup uses correct token from config.

        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_builder = Mock()
        mock_token_builder = Mock()
        mock_app = Mock(spec=Application)

        mock_application_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_token_builder
        mock_token_builder.build.return_value = mock_app

        # Execute
        bot.setup()

        # Assert
        mock_builder.token.assert_called_once_with("test_token")

    def test_bot_docstring_and_attributes(self, bot):
        """Test bot class docstring and attributes.

        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Test docstring exists and contains expected information
        assert LifeWeeksBot.__doc__ is not None
        assert (
            "Telegram bot for tracking and visualizing life weeks"
            in LifeWeeksBot.__doc__
        )
        assert "/start" in LifeWeeksBot.__doc__
        assert "/weeks" in LifeWeeksBot.__doc__
        assert "/visualize" in LifeWeeksBot.__doc__
        assert "/help" in LifeWeeksBot.__doc__

        # Test instance attributes
        assert hasattr(bot, "_app")

    @patch("src.bot.application.Application")
    def test_setup_error_handling(self, mock_application_class, bot):
        """Test setup error handling when Application creation fails.

        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_application_class.builder.side_effect = Exception(
            "Application creation failed"
        )

        # Execute & Assert
        with pytest.raises(Exception, match="Application creation failed"):
            bot.setup()

    @patch("src.bot.application.Application")
    def test_setup_handler_registration_order(self, mock_application_class, bot):
        """Test that handlers are registered in correct order.

        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.setup()

        # Assert
        calls = mock_app.add_handler.call_args_list

        # Last should be unknown message handler
        assert isinstance(calls[-1][0][0], MessageHandler)
        # Second to last should be settings text handler
        assert isinstance(calls[-2][0][0], MessageHandler)
        # First should be conversation handler
        assert isinstance(calls[0][0][0], ConversationHandler)
        # Middle should be command handlers
        for i in range(1, len(COMMAND_HANDLERS) + 1):
            assert isinstance(calls[i][0][0], CommandHandler)

        # Check that callback handlers are registered
        callback_handlers = [
            call for call in calls if isinstance(call[0][0], CallbackQueryHandler)
        ]
        assert len(callback_handlers) >= 3  # subscription, settings, language

    @patch("src.bot.application.Application")
    def test_setup_all_handlers_registered(self, mock_application_class, bot):
        """Test that all required handlers are registered.

        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.setup()

        # Assert
        total_expected_handlers = (
            1  # ConversationHandler for /start
            + len(COMMAND_HANDLERS)  # Command handlers
            + 3  # CallbackQueryHandler for subscription, settings, language
            + 1  # MessageHandler for settings text input
            + 1  # MessageHandler for unknown messages
        )

        assert mock_app.add_handler.call_count == total_expected_handlers

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    @patch("src.bot.application.setup_user_notification_schedules")
    def test_setup_scheduler_failure(self, mock_setup_scheduler, mock_logger, mock_application_class, bot):
        """Test setup when scheduler setup fails.

        :param mock_setup_scheduler: Mock setup_user_notification_schedules function
        :param mock_logger: Mock logger
        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )
        mock_setup_scheduler.return_value = False

        # Execute
        bot.setup()

        # Assert
        assert bot._app is mock_app
        mock_setup_scheduler.assert_called_once_with(mock_app)
        error_calls = [
            call
            for call in mock_logger.error.call_args_list
            if "Failed to set up weekly notification scheduler" in str(call)
        ]
        assert len(error_calls) > 0

    @patch("src.bot.application.logger")
    @patch("src.bot.application.stop_scheduler")
    def test_stop_method(self, mock_stop_scheduler, mock_logger, bot):
        """Test stop method functionality.

        :param mock_stop_scheduler: Mock stop_scheduler function
        :param mock_logger: Mock logger
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup - create a mock scheduler
        mock_scheduler = Mock()
        bot._scheduler = mock_scheduler

        # Execute
        bot.stop()

        # Assert
        mock_stop_scheduler.assert_called_once_with(mock_scheduler)
        assert bot._scheduler is None
        stop_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Life Weeks Bot stopped" in str(call)
        ]
        assert len(stop_calls) > 0

    @patch("src.bot.application.logger")
    @patch("src.bot.application.stop_scheduler")
    def test_stop_method_no_scheduler(self, mock_stop_scheduler, mock_logger, bot):
        """Test stop method when no scheduler is set.

        :param mock_stop_scheduler: Mock stop_scheduler function
        :param mock_logger: Mock logger
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup - no scheduler
        bot._scheduler = None

        # Execute
        bot.stop()

        # Assert
        mock_stop_scheduler.assert_not_called()
        assert bot._scheduler is None
        stop_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Life Weeks Bot stopped" in str(call)
        ]
        assert len(stop_calls) > 0

    def test_bot_class_constants(self):
        """Test bot class and module constants.

        :returns: None
        """
        # Test that COMMAND_HANDLERS is defined and not empty
        assert COMMAND_HANDLERS is not None
        assert len(COMMAND_HANDLERS) > 0

        # Test that all handlers in COMMAND_HANDLERS are imported correctly
        for command, handler in COMMAND_HANDLERS.items():
            assert callable(handler)
            assert hasattr(handler, "__name__")

    @patch("src.bot.application.Application")
    def test_integration_setup_and_start(self, mock_application_class, bot):
        """Test integration of setup and start methods.

        :param mock_application_class: Mock Application class
        :param bot: LifeWeeksBot instance
        :returns: None
        """
        # Setup
        mock_app = Mock(spec=Application)
        mock_app.add_handler = Mock()
        mock_app.run_polling = Mock()
        mock_application_class.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Execute
        bot.setup()
        bot.start()

        # Assert
        assert bot._app is mock_app
        mock_app.run_polling.assert_called_once()

        # Verify all handlers were registered
        assert mock_app.add_handler.call_count > 0
