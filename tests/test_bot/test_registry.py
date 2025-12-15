"""Unit tests for HandlerRegistry.

Tests registration and retrieval of handlers, waiting states, and text input handlers.
"""

from unittest.mock import MagicMock

import pytest

from src.bot.registry import HandlerRegistry


class TestHandlerRegistry:
    """Test suite for HandlerRegistry class."""

    @pytest.fixture
    def registry(self) -> HandlerRegistry:
        """Create HandlerRegistry instance for testing.

        :returns: HandlerRegistry instance
        :rtype: HandlerRegistry
        """
        return HandlerRegistry()

    def test_initial_state(self, registry: HandlerRegistry):
        """Test initial empty state of registry."""
        assert registry.get_all_handlers() == {}
        assert registry.get_all_waiting_states() == {}

    def test_register_basic_handler(self, registry: HandlerRegistry):
        """Test registering a simple command handler."""
        handler = MagicMock()
        registry.register(command="start", handler=handler)

        assert registry.get_handler("start") == handler
        assert registry.get_text_input_handler("start") is None
        assert not registry.has_waiting_state("some_state")

    def test_register_full(self, registry: HandlerRegistry):
        """Test registering handler with text input and waiting states."""
        handler = MagicMock()
        text_handler = MagicMock()
        states = ["state1", "state2"]

        registry.register(
            command="settings",
            handler=handler,
            text_input_method=text_handler,
            waiting_states=states,
        )

        # Verify handler
        assert registry.get_handler("settings") == handler

        # Verify text input handler
        assert registry.get_text_input_handler("settings") == text_handler

        # Verify waiting states
        assert registry.has_waiting_state("state1")
        assert registry.has_waiting_state("state2")
        assert registry.get_command_for_state("state1") == "settings"
        assert registry.get_command_for_state("state2") == "settings"

    def test_get_handler_not_found(self, registry: HandlerRegistry):
        """Test get_handler returns None for unknown command."""
        assert registry.get_handler("unknown") is None

    def test_get_text_input_handler_not_found(self, registry: HandlerRegistry):
        """Test get_text_input_handler returns None if not registered."""
        # Register handler without text input
        registry.register("cmd", MagicMock())
        assert registry.get_text_input_handler("cmd") is None
        assert registry.get_text_input_handler("unknown") is None

    def test_get_command_for_state_not_found(self, registry: HandlerRegistry):
        """Test get_command_for_state returns None for unknown state."""
        assert registry.get_command_for_state("unknown_state") is None

    def test_has_waiting_state_false(self, registry: HandlerRegistry):
        """Test has_waiting_state returns False for unknown state."""
        assert not registry.has_waiting_state("unknown_state")

    def test_get_all_methods_return_copies(self, registry: HandlerRegistry):
        """Test get_all_* methods return copies to prevent mutation."""
        registry.register("cmd", MagicMock())

        handlers = registry.get_all_handlers()
        states = registry.get_all_waiting_states()

        # Modify returned dicts
        handlers["new"] = "fake"
        states["new"] = "fake"

        # Verify internal state not changed
        assert "new" not in registry.get_all_handlers()
        assert "new" not in registry.get_all_waiting_states()

    def test_clear(self, registry: HandlerRegistry):
        """Test clearing the registry."""
        registry.register(
            command="cmd",
            handler=MagicMock(),
            text_input_method=MagicMock(),
            waiting_states=["state1"],
        )

        assert registry.get_handler("cmd") is not None

        registry.clear()

        assert registry.get_handler("cmd") is None
        assert registry.get_text_input_handler("cmd") is None
        assert not registry.has_waiting_state("state1")
        assert registry.get_all_handlers() == {}
