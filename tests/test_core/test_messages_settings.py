"""Tests for SettingsMessages."""

from __future__ import annotations

from datetime import date
from unittest.mock import Mock, patch

import pytest

from src.core.message_context import use_message_context
from src.core.messages import SettingsMessages


@patch("src.database.service.user_service")
@patch("src.services.container.ServiceContainer")
@patch("src.core._messages.base.get_localized_language_name")
def test_settings_basic(
    mock_get_lang: Mock,
    mock_service_container: Mock,
    mock_user_service: Mock,
) -> None:
    profile = Mock()
    profile.settings = Mock(
        birth_date=date(1990, 1, 1), life_expectancy=80, language="en"
    )
    mock_user_service.get_user_profile.return_value = profile
    mock_get_lang.return_value = "English"
    builder = Mock()
    mock_service_container.return_value.get_message_builder.return_value = builder
    builder.get.return_value = "Basic settings message"

    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert SettingsMessages().basic(user) == "Basic settings message"


@patch("src.database.service.user_service")
@patch("src.services.container.ServiceContainer")
@patch("src.core._messages.base.get_localized_language_name")
def test_settings_premium(
    mock_get_lang: Mock,
    mock_service_container: Mock,
    mock_user_service: Mock,
) -> None:
    profile = Mock()
    profile.settings = Mock(birth_date=None, life_expectancy=80, language="en")
    mock_user_service.get_user_profile.return_value = profile
    mock_get_lang.return_value = "English"
    builder = Mock()
    mock_service_container.return_value.get_message_builder.return_value = builder
    builder.get.return_value = "Premium settings message"

    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert SettingsMessages().premium(user) == "Premium settings message"


@patch("src.database.service.user_service")
def test_settings_basic_no_profile(mock_user_service: Mock) -> None:
    mock_user_service.get_user_profile.return_value = None
    user = Mock(id=1)
    with pytest.raises(ValueError):
        with use_message_context(user_info=user, fetch_profile=False):
            SettingsMessages().basic(user)


@patch("src.database.service.user_service")
def test_settings_change_language(mock_user_service: Mock) -> None:
    profile = Mock()
    profile.settings = Mock(language="en")
    mock_user_service.get_user_profile.return_value = profile
    builder = Mock()
    with patch("src.services.container.ServiceContainer") as sc:
        sc.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Change language message"
        user = Mock(id=1)
        with use_message_context(user_info=user, fetch_profile=False):
            assert SettingsMessages().change_language(user) == "Change language message"


@patch("src.database.service.user_service")
def test_settings_change_birth_date(mock_user_service: Mock) -> None:
    profile = Mock()
    profile.settings = Mock(birth_date=None)
    mock_user_service.get_user_profile.return_value = profile
    with patch("src.services.container.ServiceContainer") as sc:
        sc.return_value.get_message_builder.return_value = Mock(
            get=Mock(return_value="Change birth date message")
        )
        user = Mock(id=1)
        with use_message_context(user_info=user, fetch_profile=False):
            assert (
                SettingsMessages().change_birth_date(user)
                == "Change birth date message"
            )


@patch("src.database.service.user_service")
def test_settings_change_life_expectancy(mock_user_service: Mock) -> None:
    profile = Mock()
    profile.settings = Mock(life_expectancy=80)
    mock_user_service.get_user_profile.return_value = profile
    with patch("src.services.container.ServiceContainer") as sc:
        sc.return_value.get_message_builder.return_value = Mock(
            get=Mock(return_value="Change life expectancy message")
        )
        user = Mock(id=1)
        with use_message_context(user_info=user, fetch_profile=False):
            assert (
                SettingsMessages().change_life_expectancy(user)
                == "Change life expectancy message"
            )


def test_settings_updates_and_errors() -> None:
    with patch("src.services.container.ServiceContainer") as sc:
        builder = Mock()
        sc.return_value.get_message_builder.return_value = builder
        builder.get.side_effect = [
            "Birth date updated",
            "Language updated",
            "Life expectancy updated",
            "Invalid life expectancy",
            "Settings error",
        ]
        user = Mock(id=1)
        with use_message_context(user_info=user, fetch_profile=False):
            assert (
                SettingsMessages().birth_date_updated(user, date(2000, 1, 1), 24)
                == "Birth date updated"
            )
            assert SettingsMessages().language_updated(user, "en") == "Language updated"
            assert (
                SettingsMessages().life_expectancy_updated(user, 90)
                == "Life expectancy updated"
            )
            assert (
                SettingsMessages().invalid_life_expectancy(user)
                == "Invalid life expectancy"
            )
            assert SettingsMessages().settings_error(user) == "Settings error"


def test_settings_buttons() -> None:
    with patch("src.services.container.ServiceContainer") as sc:
        builder = Mock()
        sc.return_value.get_message_builder.return_value = builder
        builder.get.side_effect = [
            "📅 Change Birth Date",
            "🌍 Change Language",
            "⏰ Change Expected Life Expectancy",
        ]
        user = Mock(id=1)
        with use_message_context(user_info=user, fetch_profile=False):
            result = SettingsMessages().buttons(user)
    assert result == [
        [{"text": "📅 Change Birth Date", "callback_data": "settings_birth_date"}],
        [{"text": "🌍 Change Language", "callback_data": "settings_language"}],
        [
            {
                "text": "⏰ Change Expected Life Expectancy",
                "callback_data": "settings_life_expectancy",
            }
        ],
    ]


def test_settings_birth_date_errors() -> None:
    with patch("src.services.container.ServiceContainer") as sc:
        builder = Mock()
        sc.return_value.get_message_builder.return_value = builder
        builder.get.side_effect = [
            "Future",
            "Old",
            "Format",
        ]
        user = Mock(id=1)
        with use_message_context(user_info=user, fetch_profile=False):
            assert SettingsMessages().birth_date_future_error(user) == "Future"
            assert SettingsMessages().birth_date_old_error(user) == "Old"
            assert SettingsMessages().birth_date_format_error(user) == "Format"
