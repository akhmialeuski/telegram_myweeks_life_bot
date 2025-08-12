"""Tests for RegistrationMessages."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.core.message_context import use_message_context
from src.core.messages import RegistrationMessages


@patch("src.services.container.ServiceContainer")
def test_registration_success(mock_service_container: Mock) -> None:
    usvc = Mock()
    profile = Mock()
    usvc.get_user_profile.return_value = profile
    mock_service_container.return_value.get_user_service.return_value = usvc

    engine_inst = Mock()
    engine_inst.get_life_statistics.return_value = {
        "age": 33,
        "weeks_lived": 1720,
        "remaining_weeks": 2448,
        "life_percentage": 0.412,
    }
    engine_cls = Mock(return_value=engine_inst)
    mock_service_container.return_value.get_life_calculator.return_value = engine_cls

    builder = Mock()
    mock_service_container.return_value.get_message_builder.return_value = builder
    builder.get.return_value = "Registration success message"

    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=True):
        assert (
            RegistrationMessages().success(user, "1990-01-01")
            == "Registration success message"
        )


@patch("src.services.container.ServiceContainer")
def test_registration_success_user_not_found(mock_service_container: Mock) -> None:
    usvc = Mock()
    usvc.get_user_profile.return_value = None
    mock_service_container.return_value.get_user_service.return_value = usvc

    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=True):
        with pytest.raises(ValueError):
            RegistrationMessages().success(user, "1990-01-01")


@patch("src.services.container.ServiceContainer")
def test_registration_error(mock_service_container: Mock) -> None:
    builder = Mock()
    mock_service_container.return_value.get_message_builder.return_value = builder
    builder.get.return_value = "Registration failed"

    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert RegistrationMessages().error(user) == "Registration failed"
