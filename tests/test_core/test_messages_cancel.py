"""Tests for CancelMessages."""

from __future__ import annotations

from unittest.mock import Mock, patch

from src.core.message_context import use_message_context
from src.core.messages import CancelMessages


@patch("src.services.container.ServiceContainer")
def test_cancel_success(mock_service_container: Mock) -> None:
    builder = Mock()
    mock_service_container.return_value.get_message_builder.return_value = builder
    builder.get.return_value = "Cancel success"

    user = Mock(id=1, first_name="Test")
    with use_message_context(user_info=user, fetch_profile=False):
        assert CancelMessages().success(user, "en") == "Cancel success"


@patch("src.services.container.ServiceContainer")
def test_cancel_error(mock_service_container: Mock) -> None:
    builder = Mock()
    mock_service_container.return_value.get_message_builder.return_value = builder
    builder.get.return_value = "Cancel error"

    user = Mock(id=1, first_name="Test")
    with use_message_context(user_info=user, fetch_profile=False):
        assert CancelMessages().error(user) == "Cancel error"
