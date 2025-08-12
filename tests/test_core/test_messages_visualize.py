"""Tests for VisualizeMessages."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.core.message_context import use_message_context
from src.core.messages import VisualizeMessages


@patch("src.services.container.ServiceContainer")
def test_visualize_messages_success(mock_service_container: Mock) -> None:
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
    builder.get.return_value = "Visualization message"

    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=True):
        assert VisualizeMessages().generate(user) == "Visualization message"


@patch("src.services.container.ServiceContainer")
def test_visualize_messages_user_not_found(mock_service_container: Mock) -> None:
    usvc = Mock()
    usvc.get_user_profile.return_value = None
    mock_service_container.return_value.get_user_service.return_value = usvc

    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=True):
        with pytest.raises(ValueError):
            VisualizeMessages().generate(user)
