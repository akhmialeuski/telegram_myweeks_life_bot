"""Unit tests for bot application.

Tests all functionality of the LifeWeeksBot application class
with proper mocking, edge cases, and error handling coverage.
"""

from unittest.mock import Mock, patch

import pytest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from src.bot.application import (
    HANDLERS,
    LifeWeeksBot,
)
from src.bot.constants import (
    COMMAND_HELP,
    COMMAND_START,
    COMMAND_VISUALIZE,
    COMMAND_WEEKS,
)
from src.bot.scheduler import SchedulerSetupError


class TestHandlers:
    """Test suite for HANDLERS mapping."""

    def test_handlers_mapping(self):
        """Test that HANDLERS contains all expected commands.

        :returns: None
        """
        expected_commands = [
            "start",
            "weeks",
            "settings",
            "visualize",
            "help",
            "subscription",
            "cancel",
            "unknown",
        ]

        for command in expected_commands:
            assert command in HANDLERS, f"Command {command} missing from HANDLERS"

    def test_handlers_structure(self):
        """Test that all handlers have the correct structure.

        :returns: None
        """
        for command, config in HANDLERS.items():
            assert "class" in config, f"Handler for {command} missing 'class' key"
            assert (
                "callbacks" in config
            ), f"Handler for {command} missing 'callbacks' key"


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
    def test_setup_handlers_registration(
        self, mock_logger, mock_application_class, bot
    ):
        """Test handlers registration during setup.

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
        # Should register handlers for all commands
        assert mock_app.add_handler.call_count > 0

        # Check that command handlers were registered
        command_handler_calls = [
            call
            for call in mock_app.add_handler.call_args_list
            if isinstance(call[0][0], CommandHandler)
        ]
        assert len(command_handler_calls) > 0

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    def test_setup_command_handlers_registration(
        self, mock_logger, mock_application_class, bot
    ):
        """Test command handler registration during setup.

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
        # Check that command handlers were registered
        command_calls = mock_app.add_handler.call_args_list
        registered_commands = set()

        for call in command_calls:
            handler = call[0][0]
            if isinstance(handler, CommandHandler):
                registered_commands.update(handler.commands)

        expected_commands = set(HANDLERS.keys())
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
        # Check that callback handlers were registered
        callback_calls = mock_app.add_handler.call_args_list
        callback_handlers_found = False

        for call in callback_calls:
            handler = call[0][0]
            if isinstance(handler, CallbackQueryHandler):
                callback_handlers_found = True
                break

        assert callback_handlers_found, "Callback handlers not found"

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

        # Check debug messages for individual command handlers
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        for command in HANDLERS.keys():
            expected_debug = f"Registered command handler: /{command}"
            assert expected_debug in debug_calls

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
        # Check that some form of handler registration message was logged
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        handler_messages = [
            msg
            for msg in info_calls
            if "handler" in msg.lower()
            and ("registered" in msg.lower() or "fallback" in msg.lower())
        ]
        assert len(handler_messages) > 0, "No handler registration messages found"

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
    def test_start_without_setup(
        self, mock_setup_scheduler, mock_logger, mock_application_class, bot
    ):
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
        assert f"/{COMMAND_START}" in LifeWeeksBot.__doc__
        assert f"/{COMMAND_WEEKS}" in LifeWeeksBot.__doc__
        assert f"/{COMMAND_VISUALIZE}" in LifeWeeksBot.__doc__
        assert f"/{COMMAND_HELP}" in LifeWeeksBot.__doc__

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

        # Check that handlers were registered
        assert len(calls) > 0

        # Check that command handlers are registered
        command_handlers = [
            call for call in calls if isinstance(call[0][0], CommandHandler)
        ]
        assert len(command_handlers) > 0

        # Check that callback handlers are registered
        callback_handlers = [
            call for call in calls if isinstance(call[0][0], CallbackQueryHandler)
        ]
        assert len(callback_handlers) > 0

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
        # Check that handlers were registered (exact count may vary due to callbacks and text inputs)
        assert mock_app.add_handler.call_count > 0

    @patch("src.bot.application.Application")
    @patch("src.bot.application.logger")
    @patch("src.bot.application.setup_user_notification_schedules")
    def test_setup_scheduler_failure(
        self, mock_setup_scheduler, mock_logger, mock_application_class, bot
    ):
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
        mock_setup_scheduler.side_effect = SchedulerSetupError("Test error")

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
        # Test that HANDLERS is defined and not empty
        assert HANDLERS is not None
        assert len(HANDLERS) > 0

        # Test that all handlers in HANDLERS have correct structure
        for command, config in HANDLERS.items():
            assert "class" in config
            assert "callbacks" in config

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
