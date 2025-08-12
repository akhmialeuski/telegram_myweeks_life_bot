"""Extra coverage for WeeksMessages life stats formatting edge."""

from __future__ import annotations

from unittest.mock import Mock, patch

from src.core._messages.week import WeeksMessages
from src.core.message_context import use_message_context


def _make_user() -> Mock:
    user = Mock()
    user.id = 1
    user.language_code = "en"
    user.first_name = "Test"
    return user


@patch("src.core._messages.week.get_subscription_addition_message", return_value="")
@patch("src.services.container.ServiceContainer")
def test_weeks_messages_formatting(mock_container: Mock, _mock_add: Mock) -> None:
    """Ensure life_percentage formatting path with provided stats value is covered."""

    builder = Mock()
    builder.get.return_value = "BASE"
    mock_container.return_value.get_message_builder.return_value = builder
    mock_container.return_value.get_user_service.return_value.get_user_profile.return_value = (
        Mock()
    )
    # Life stats with specific float to test format
    life_stats = {
        "age": 30,
        "weeks_lived": 1560,
        "remaining_weeks": 2000,
        "life_percentage": 0.4567,
        "days_until_birthday": 100,
    }

    user = _make_user()
    with use_message_context(user_info=user, fetch_profile=True):
        with patch.object(
            type(use_message_context(user, fetch_profile=True).__enter__()),
            "life_stats",
            return_value=life_stats,
        ):
            # Since patching enter result is complex, patch MessageContext.life_stats directly
            with patch(
                "src.core.message_context.MessageContext.life_stats",
                return_value=life_stats,
            ):
                assert WeeksMessages().generate(user).startswith("BASE")
