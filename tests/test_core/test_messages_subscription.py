"""Tests for SubscriptionMessages."""

from __future__ import annotations

from unittest.mock import Mock, patch

from src.core.message_context import use_message_context
from src.core.messages import SubscriptionMessages


@patch("src.core._messages.subscription.get_subscription_addition_message")
@patch("src.services.container.ServiceContainer")
def test_subscription_current(mock_service_container: Mock, mock_sub: Mock) -> None:
    profile = Mock()
    profile.subscription = Mock(subscription_type=Mock(value="premium"))
    usvc = Mock(get_user_profile=Mock(return_value=profile))
    mock_service_container.return_value.get_user_service.return_value = usvc
    builder = Mock()
    mock_service_container.return_value.get_message_builder.return_value = builder
    builder.get.return_value = "Subscription info"
    mock_sub.return_value = "desc"

    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=True):
        assert SubscriptionMessages().current(user) == "Subscription info"


@patch("src.services.container.ServiceContainer")
def test_subscription_invalid_type(mock_service_container: Mock) -> None:
    builder = Mock(get=Mock(return_value="Invalid"))
    mock_service_container.return_value.get_message_builder.return_value = builder
    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert SubscriptionMessages().invalid_type() == "Invalid"


@patch("src.services.container.ServiceContainer")
def test_subscription_profile_error(mock_service_container: Mock) -> None:
    builder = Mock(get=Mock(return_value="Error"))
    mock_service_container.return_value.get_message_builder.return_value = builder
    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert SubscriptionMessages().profile_error() == "Error"


@patch("src.services.container.ServiceContainer")
def test_subscription_already_active(mock_service_container: Mock) -> None:
    builder = Mock(get=Mock(return_value="Already"))
    mock_service_container.return_value.get_message_builder.return_value = builder
    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert SubscriptionMessages().already_active("premium") == "Already"


@patch("src.core._messages.subscription.get_subscription_addition_message")
@patch("src.services.container.ServiceContainer")
def test_subscription_change_success(
    mock_service_container: Mock, mock_sub: Mock
) -> None:
    builder = Mock(get=Mock(return_value="Change success"))
    mock_service_container.return_value.get_message_builder.return_value = builder
    mock_sub.return_value = "desc"
    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert (
            SubscriptionMessages().change_success(user, "premium") == "Change success"
        )


@patch("src.services.container.ServiceContainer")
def test_subscription_change_failed(mock_service_container: Mock) -> None:
    builder = Mock(get=Mock(return_value="Change failed"))
    mock_service_container.return_value.get_message_builder.return_value = builder
    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert SubscriptionMessages().change_failed() == "Change failed"


@patch("src.services.container.ServiceContainer")
def test_subscription_change_error(mock_service_container: Mock) -> None:
    builder = Mock(get=Mock(return_value="Change error"))
    mock_service_container.return_value.get_message_builder.return_value = builder
    user = Mock(id=1)
    with use_message_context(user_info=user, fetch_profile=False):
        assert SubscriptionMessages().change_error() == "Change error"
