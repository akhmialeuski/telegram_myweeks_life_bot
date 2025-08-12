"""Tests for WeeksMessages."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.core.message_context import use_message_context
from src.core.messages import WeeksMessages


@patch("src.core._messages.subscription.get_subscription_addition_message")
@patch("src.services.container.ServiceContainer")
def test_weeks_messages_success(
    mock_service_container: Mock, mock_sub_add: Mock
) -> None:
    usvc = Mock()
    profile = Mock()
    usvc.get_user_profile.return_value = profile
    mock_service_container.return_value.get_user_service.return_value = usvc

    engine_cls = Mock()
    engine_inst = Mock()
    engine_inst.get_life_statistics.return_value = {
        "age": 33,
        "weeks_lived": 1720,
        "remaining_weeks": 2448,
        "life_percentage": 0.412,
        "days_until_birthday": 45,
    }
    engine_cls.return_value = engine_inst
    mock_service_container.return_value.get_life_calculator.return_value = engine_cls

    builder = Mock()
    mock_service_container.return_value.get_message_builder.return_value = builder
    builder.get.return_value = "Your life statistics: 33 years old, 1720 weeks lived"
    mock_sub_add.return_value = ""

    user = Mock(id=1, first_name="Test")
    with use_message_context(user_info=user, fetch_profile=True):
        result = WeeksMessages().generate(user)

    assert result == "Your life statistics: 33 years old, 1720 weeks lived"
    builder.get.assert_called_once()


@patch("src.services.container.ServiceContainer")
def test_weeks_messages_user_not_found(mock_service_container: Mock) -> None:
    usvc = Mock()
    usvc.get_user_profile.return_value = None
    mock_service_container.return_value.get_user_service.return_value = usvc

    user = Mock(id=123)
    with use_message_context(user_info=user, fetch_profile=True):
        with pytest.raises(ValueError):
            WeeksMessages().generate(user)


@patch("src.core._messages.subscription.get_subscription_addition_message")
@patch("src.services.container.ServiceContainer")
def test_weeks_messages_missing_stats_key(
    mock_service_container: Mock, mock_sub_add: Mock
) -> None:
    usvc = Mock()
    profile = Mock()
    usvc.get_user_profile.return_value = profile
    mock_service_container.return_value.get_user_service.return_value = usvc

    engine_inst = Mock()
    engine_inst.get_life_statistics.return_value = {"age": 33}
    engine_cls = Mock(return_value=engine_inst)
    mock_service_container.return_value.get_life_calculator.return_value = engine_cls

    mock_sub_add.return_value = ""
    user = Mock(id=1)
    with pytest.raises(KeyError):
        with use_message_context(user_info=user, fetch_profile=True):
            WeeksMessages().generate(user)
