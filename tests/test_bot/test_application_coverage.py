"""Coverage tests for LifeWeeksBot application.

This module contains tests specifically targeted at increasing code coverage
for edge cases and error handling in src/bot/application.py.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.bot.application import LifeWeeksBot
from src.bot.constants import COMMAND_UNKNOWN
from src.bot.plugins.loader import HandlerConfig


class TestLifeWeeksBotCoverage:
    """Tests for edge cases in LifeWeeksBot."""

    def test_register_handler_from_config_exception(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ):
        """Test exception handling in _register_handler_from_config."""
        config = HandlerConfig(
            module="test_module", class_name="TestHandler", command="test"
        )
        bot._plugin_loader = MagicMock()
        bot._plugin_loader.load_handler_class.side_effect = Exception("Load failed")

        bot._register_handler_from_config(config)

        mock_application_logger.error.assert_called_with(
            "Failed to register handler 'test': Load failed"
        )

    def test_register_unknown_handler_fallback_present(
        self, bot: LifeWeeksBot, mock_app: MagicMock
    ):
        """Test _register_unknown_handler_fallback when handler exists."""
        bot._app = mock_app
        mock_handler = MagicMock()
        bot._handler_instances[COMMAND_UNKNOWN] = mock_handler

        bot._register_unknown_handler_fallback()

        mock_app.add_handler.assert_called()

    @pytest.mark.asyncio
    async def test_handle_no_waiting_state_exception(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ):
        """Test exception handling in _handle_no_waiting_state."""
        update = Mock()
        context = Mock()
        mock_handler = MagicMock()
        mock_handler.handle = AsyncMock(side_effect=Exception("Handle failed"))
        bot._handler_instances[COMMAND_UNKNOWN] = mock_handler

        await bot._handle_no_waiting_state(update, context)

        mock_application_logger.error.assert_called()
        assert (
            "Error in unknown handler" in mock_application_logger.error.call_args[0][0]
        )

    @pytest.mark.asyncio
    async def test_try_text_input_handler_exception(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ):
        """Test exception handling in _try_text_input_handler."""
        update = Mock()
        context = Mock()
        target_command = "test_cmd"
        mock_handler = AsyncMock(side_effect=Exception("Input failed"))
        bot._text_input_handlers[target_command] = mock_handler

        result = await bot._try_text_input_handler(update, context, target_command)

        assert result is True
        mock_application_logger.error.assert_called()
        assert (
            "Error in text input handler"
            in mock_application_logger.error.call_args[0][0]
        )

    @pytest.mark.asyncio
    async def test_try_unknown_handler_fallback_exception(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ):
        """Test exception handling in _try_unknown_handler_fallback."""
        update = Mock()
        context = Mock()
        waiting_for = "some_state"
        mock_handler = MagicMock()
        mock_handler.handle = AsyncMock(side_effect=Exception("Fallback failed"))
        bot._handler_instances[COMMAND_UNKNOWN] = mock_handler

        result = await bot._try_unknown_handler_fallback(update, context, waiting_for)

        assert result is True
        mock_application_logger.error.assert_called()
        assert (
            "Error in unknown handler fallback"
            in mock_application_logger.error.call_args[0][0]
        )

    @pytest.mark.asyncio
    async def test_send_error_message_exception(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ):
        """Test exception handling in _send_error_message."""
        update = Mock()
        update.effective_chat.id = 123
        context = Mock()
        context.bot.send_message = AsyncMock(side_effect=Exception("Send failed"))

        await bot._send_error_message(update, context)

        mock_application_logger.error.assert_called()
        assert (
            "Failed to send error message"
            in mock_application_logger.error.call_args[0][0]
        )

    def test_setup_scheduler_exception(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ):
        """Test exception handling in _setup_scheduler."""
        with patch("multiprocessing.Queue", side_effect=Exception("Queue failed")):
            bot._setup_scheduler()

        mock_application_logger.error.assert_called()
        assert (
            "Failed to set up scheduler"
            in mock_application_logger.error.call_args[0][0]
        )

    @pytest.mark.asyncio
    async def test_post_init_scheduler_start_unhealthy(
        self, bot: LifeWeeksBot, mock_application_logger: MagicMock
    ):
        """Test _post_init_scheduler_start when worker is unhealthy."""
        mock_client = AsyncMock()
        mock_client.health_check.return_value = False
        bot._scheduler_client = mock_client
        mock_app = MagicMock()

        await bot._post_init_scheduler_start(mock_app)

        mock_application_logger.warning.assert_called_with(
            "Scheduler worker health check failed"
        )
