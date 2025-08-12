"""Tests for SystemMessages."""

from __future__ import annotations

from unittest.mock import Mock, patch

from src.core.message_context import use_message_context
from src.core.messages import SystemMessages


@patch("src.services.container.ServiceContainer")
def test_system_messages_help(mock_service_container: Mock) -> None:
    builder = Mock()
    mock_service_container.return_value.get_message_builder.return_value = builder
    builder.get.return_value = "Available commands"

    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert SystemMessages().help(user) == "Available commands"


@patch("src.services.container.ServiceContainer")
def test_system_messages_unknown(mock_service_container: Mock) -> None:
    builder = Mock()
    mock_service_container.return_value.get_message_builder.return_value = builder
    builder.get.return_value = "Unknown command"

    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert SystemMessages().unknown(user) == "Unknown command"
