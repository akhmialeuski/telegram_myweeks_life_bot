"""Extra coverage for SystemMessages methods."""

from __future__ import annotations

from unittest.mock import Mock, patch

from src.core._messages.system import SystemMessages
from src.core.message_context import use_message_context


def _make_user() -> Mock:
    user = Mock()
    user.id = 1
    user.language_code = "en"
    user.first_name = "Test"
    return user


@patch("src.services.container.ServiceContainer")
def test_system_messages_all(mock_container: Mock) -> None:
    builder = Mock()
    builder.get.side_effect = [
        "HELP",
        "UNKNOWN",
        "WELCOME_EXISTING",
        "WELCOME_NEW",
    ]
    mock_container.return_value.get_message_builder.return_value = builder
    mock_container.return_value.get_user_service.return_value.get_user_profile.return_value = (
        None
    )

    user = _make_user()
    with use_message_context(user_info=user, fetch_profile=False):
        assert SystemMessages().help(user) == "HELP"
        assert SystemMessages().unknown(user) == "UNKNOWN"
        assert SystemMessages().welcome_existing(user) == "WELCOME_EXISTING"
        assert SystemMessages().welcome_new(user) == "WELCOME_NEW"
