"""Extra coverage tests for SettingsMessages edge branches."""

from __future__ import annotations

from unittest.mock import Mock, patch

from src.core._messages.settings import SettingsMessages
from src.core.message_context import use_message_context


def _make_user() -> Mock:
    user = Mock()
    user.id = 1
    user.language_code = "en"
    user.first_name = "Test"
    return user


@patch("src.services.container.ServiceContainer")
def test_change_language_button_fallback(mock_container: Mock) -> None:
    """If primary builder.get returns a non-string/sentinel, fallback path is used."""

    # Builder returns sentinel first to trigger fallback path in change_language
    builder = Mock()
    builder.get.side_effect = ["settings.change_language", "Change Language"]
    mock_container.return_value.get_message_builder.return_value = builder
    # Provide a mock profile so ensure_profile succeeds
    mock_profile = Mock(
        settings=Mock(language="en", birth_date=None, life_expectancy=70)
    )
    mock_container.return_value.get_user_service.return_value.get_user_profile.return_value = (
        mock_profile
    )

    user = _make_user()
    # fetch_profile=True so profile is set in context
    with use_message_context(user_info=user, fetch_profile=True):
        assert SettingsMessages().change_language(user) == "Change Language"


@patch("src.services.container.ServiceContainer")
def test_buttons_happy_path(mock_container: Mock) -> None:
    """Cover happy path in buttons where all texts are valid strings."""

    builder = Mock()
    builder.get.side_effect = ["Birth", "Lang", "Life"]
    mock_container.return_value.get_message_builder.return_value = builder
    mock_container.return_value.get_user_service.return_value.get_user_profile.return_value = (
        None
    )

    user = _make_user()
    with use_message_context(user_info=user, fetch_profile=False):
        buttons = SettingsMessages().buttons(user)
        assert buttons[0][0]["text"] == "Birth"
        assert buttons[1][0]["text"] == "Lang"
        assert buttons[2][0]["text"] == "Life"


@patch("src.services.container.ServiceContainer")
def test_buttons_exception_fallback(mock_container: Mock) -> None:
    """Cover exception path in buttons try/except when builder.get raises."""

    builder = Mock()
    # First call raises, then provide 3 texts
    builder.get.side_effect = [Exception("boom"), "Birth", "Lang", "Life"]
    mock_container.return_value.get_message_builder.return_value = builder
    mock_container.return_value.get_user_service.return_value.get_user_profile.return_value = (
        None
    )

    user = _make_user()
    with use_message_context(user_info=user, fetch_profile=False):
        buttons = SettingsMessages().buttons(user)
        assert buttons[0][0]["text"] == "Birth"
        assert buttons[1][0]["text"] == "Lang"
        assert buttons[2][0]["text"] == "Life"
