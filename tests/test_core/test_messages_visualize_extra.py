"""Extra coverage for VisualizeMessages."""

from __future__ import annotations

from unittest.mock import Mock, patch

from src.core._messages.visualize import VisualizeMessages
from src.core.message_context import use_message_context


def _make_user() -> Mock:
    user = Mock()
    user.id = 1
    user.language_code = "en"
    return user


@patch("src.services.container.ServiceContainer")
def test_visualize_messages_generate(mock_container: Mock) -> None:
    builder = Mock()
    builder.get.return_value = "VIZ"
    mock_container.return_value.get_message_builder.return_value = builder
    mock_container.return_value.get_user_service.return_value.get_user_profile.return_value = (
        Mock()
    )

    user = _make_user()
    with use_message_context(user_info=user, fetch_profile=True):
        with patch(
            "src.core.message_context.MessageContext.life_stats",
            return_value={
                "age": 30,
                "weeks_lived": 1000,
                "life_percentage": 0.25,
            },
        ):
            assert VisualizeMessages().generate(user) == "VIZ"
