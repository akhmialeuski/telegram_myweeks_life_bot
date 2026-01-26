"""Tests for core messages module."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from src.core.dtos import UserSubscriptionDTO
from src.core.messages import (
    ErrorMessages,
    RegistrationMessages,
    SubscriptionMessages,
)
from src.enums import SubscriptionType


class TestRegistrationMessages:
    """Test suite for RegistrationMessages class."""

    @pytest.fixture
    def mock_i18n(self) -> MagicMock:
        """Create mock i18n service.

        :returns: Mock i18n service
        :rtype: MagicMock
        """
        mock = MagicMock()
        mock.translate.return_value = "Success message"
        return mock

    def test_success_message(self, mock_i18n: MagicMock) -> None:
        """Test registration success message generation.

        :param mock_i18n: Mock i18n service
        :type mock_i18n: MagicMock
        :returns: None
        :rtype: None
        """
        messages = RegistrationMessages(i18n=mock_i18n)

        result = messages.success(
            birth_date="1990-01-01",
            age="35",
            weeks_lived="1820",
            remaining_weeks="2340",
            life_percentage="43.8%",
        )

        assert result == "Success message"
        mock_i18n.translate.assert_called_once()
        call_args = mock_i18n.translate.call_args
        assert call_args.kwargs["birth_date"] == "1990-01-01"
        assert call_args.kwargs["age"] == "35"


class TestErrorMessages:
    """Test suite for ErrorMessages class."""

    @pytest.fixture
    def mock_i18n(self) -> MagicMock:
        """Create mock i18n service.

        :returns: Mock i18n service
        :rtype: MagicMock
        """
        mock = MagicMock()
        mock.translate.return_value = "Error message"
        return mock

    def test_not_registered_message(self, mock_i18n: MagicMock) -> None:
        """Test not registered error message generation.

        :param mock_i18n: Mock i18n service
        :type mock_i18n: MagicMock
        :returns: None
        :rtype: None
        """
        messages = ErrorMessages(i18n=mock_i18n)

        result = messages.not_registered()

        assert result == "Error message"
        mock_i18n.translate.assert_called_once()


class TestSubscriptionMessages:
    """Test suite for SubscriptionMessages class."""

    @pytest.fixture
    def mock_i18n(self) -> MagicMock:
        """Create mock i18n service.

        :returns: Mock i18n service
        :rtype: MagicMock
        """
        mock = MagicMock()
        mock.translate.return_value = "Subscription message"
        return mock

    def test_status_active_with_expiry(self, mock_i18n: MagicMock) -> None:
        """Test active subscription status message with expiry date.

        when expires_at is set.

        :param mock_i18n: Mock i18n service
        :type mock_i18n: MagicMock
        :returns: None
        :rtype: None
        """
        messages = SubscriptionMessages(i18n=mock_i18n)

        subscription = UserSubscriptionDTO(
            subscription_type=SubscriptionType.PREMIUM,
            is_active=True,
            expires_at=datetime(2025, 12, 31, tzinfo=UTC),
        )

        result = messages.status_active(subscription=subscription)

        assert result == "Subscription message"
        mock_i18n.translate.assert_called_once()
        call_args = mock_i18n.translate.call_args
        assert call_args.kwargs["expiry_date"] == "2025-12-31"
        assert call_args.kwargs["plan_name"] == "Premium"

    def test_status_active_no_expiry(self, mock_i18n: MagicMock) -> None:
        """Test active subscription status message without expiry date.

        when expires_at is None.

        :param mock_i18n: Mock i18n service
        :type mock_i18n: MagicMock
        :returns: None
        :rtype: None
        """
        messages = SubscriptionMessages(i18n=mock_i18n)

        subscription = UserSubscriptionDTO(
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
            expires_at=None,
        )

        result = messages.status_active(subscription=subscription)

        assert result == "Subscription message"
        call_args = mock_i18n.translate.call_args
        assert call_args.kwargs["expiry_date"] == "N/A"
        assert call_args.kwargs["plan_name"] == "Basic"

    def test_status_inactive(self, mock_i18n: MagicMock) -> None:
        """Test inactive subscription status message.

        :param mock_i18n: Mock i18n service
        :type mock_i18n: MagicMock
        :returns: None
        :rtype: None
        """
        messages = SubscriptionMessages(i18n=mock_i18n)

        result = messages.status_inactive()

        assert result == "Subscription message"
        mock_i18n.translate.assert_called_once()
