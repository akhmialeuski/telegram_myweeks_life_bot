"""Unit tests for UserSubscription model.

Tests all functionality of the UserSubscription model using pytest
with proper edge case coverage.
"""

from datetime import UTC, datetime, timedelta

from src.core.enums import SubscriptionType
from src.database.models.user_subscription import (
    DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS,
    UserSubscription,
)


class TestUserSubscription:
    """Test suite for UserSubscription model."""

    def test_user_subscription_creation_basic(self):
        """Test basic UserSubscription creation.

        :returns: None
        """
        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
        )

        assert subscription.telegram_id == 123456789
        assert subscription.subscription_type == SubscriptionType.BASIC
        assert subscription.is_active is True

    def test_user_subscription_creation_with_all_fields(self):
        """Test UserSubscription creation with all fields specified.

        :returns: None
        """
        created_at = datetime.now(UTC)
        expires_at = created_at + timedelta(days=30)

        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.PREMIUM,
            is_active=False,
            created_at=created_at,
            expires_at=expires_at,
        )

        assert subscription.telegram_id == 123456789
        assert subscription.subscription_type == SubscriptionType.PREMIUM
        assert subscription.is_active is False
        assert subscription.created_at == created_at
        assert subscription.expires_at == expires_at

    def test_subscription_type_enum_values(self):
        """Test all SubscriptionType enum values work correctly.

        :returns: None
        """
        for sub_type in SubscriptionType:
            subscription = UserSubscription(
                telegram_id=123456789, subscription_type=sub_type, is_active=True
            )
            assert subscription.subscription_type == sub_type

    def test_subscription_type_basic(self):
        """Test BASIC subscription type.

        :returns: None
        """
        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
        )

        assert subscription.subscription_type == SubscriptionType.BASIC
        # The enum uses lowercase values
        assert subscription.subscription_type.value == "basic"

    def test_subscription_type_premium(self):
        """Test PREMIUM subscription type.

        :returns: None
        """
        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.PREMIUM,
            is_active=True,
        )

        assert subscription.subscription_type == SubscriptionType.PREMIUM
        # The enum uses lowercase values
        assert subscription.subscription_type.value == "premium"

    def test_user_subscription_is_active_boolean(self):
        """Test is_active field accepts boolean values.

        :returns: None
        """
        # Test True
        subscription_active = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
        )
        assert subscription_active.is_active is True

        # Test False
        subscription_inactive = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=False,
        )
        assert subscription_inactive.is_active is False

    def test_user_subscription_default_expiration_constant(self):
        """Test DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS constant.

        :returns: None
        """
        assert isinstance(DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS, int)
        assert DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS > 0
        # The actual value is 36500 (100 years for free users)
        assert DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS == 36500

    def test_user_subscription_expiration_calculation(self):
        """Test subscription expiration calculation using constant.

        :returns: None
        """
        created_at = datetime.now(UTC)
        expires_at = created_at + timedelta(days=DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS)

        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
            created_at=created_at,
            expires_at=expires_at,
        )

        # Check that expiration is calculated correctly
        expected_expiration = created_at + timedelta(
            days=DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS
        )
        assert subscription.expires_at == expected_expiration

    def test_user_subscription_repr(self):
        """Test UserSubscription string representation.

        :returns: None
        """
        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.PREMIUM,
            is_active=True,
        )

        repr_str = repr(subscription)
        # The model uses default SQLAlchemy repr, so just check it's a string
        assert isinstance(repr_str, str)
        assert len(repr_str) > 0

    def test_user_subscription_str(self):
        """Test UserSubscription string conversion.

        :returns: None
        """
        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
        )

        str_repr = str(subscription)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    def test_user_subscription_equality(self):
        """Test UserSubscription equality comparison.

        :returns: None
        """
        subscription1 = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
        )

        subscription2 = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
        )

        subscription3 = UserSubscription(
            telegram_id=987654321,  # Different telegram_id
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
        )

        # Same subscriptions should be equal by telegram_id
        assert subscription1.telegram_id == subscription2.telegram_id
        # Different telegram_id should not be equal
        assert subscription1.telegram_id != subscription3.telegram_id

    def test_subscription_type_enum_has_expected_values(self):
        """Test SubscriptionType enum has all expected values.

        :returns: None
        """
        # The actual enum includes TRIAL as well
        expected_types = {"basic", "premium", "trial"}
        actual_types = {sub_type.value for sub_type in SubscriptionType}
        assert actual_types == expected_types

    def test_user_subscription_created_at_datetime(self):
        """Test created_at field accepts datetime values.

        :returns: None
        """
        created_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
            created_at=created_time,
        )

        assert subscription.created_at == created_time
        assert isinstance(subscription.created_at, datetime)

    def test_user_subscription_expires_at_datetime(self):
        """Test expires_at field accepts datetime values.

        :returns: None
        """
        expires_time = datetime(2024, 12, 31, 23, 59, 59, tzinfo=UTC)
        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.PREMIUM,
            is_active=True,
            expires_at=expires_time,
        )

        assert subscription.expires_at == expires_time
        assert isinstance(subscription.expires_at, datetime)

    def test_user_subscription_none_expires_at(self):
        """Test UserSubscription with None expires_at (permanent subscription).

        :returns: None
        """
        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.PREMIUM,
            is_active=True,
            expires_at=None,  # Permanent subscription
        )

        assert subscription.expires_at is None
        assert subscription.is_active is True

    def test_user_subscription_expired_subscription(self):
        """Test UserSubscription with past expiration date.

        :returns: None
        """
        past_time = datetime(2020, 1, 1, 0, 0, 0, tzinfo=UTC)
        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=False,  # Should be inactive if expired
            expires_at=past_time,
        )

        assert subscription.expires_at == past_time
        assert subscription.is_active is False

    def test_user_subscription_future_expiration(self):
        """Test UserSubscription with future expiration date.

        :returns: None
        """
        future_time = datetime(2030, 12, 31, 23, 59, 59, tzinfo=UTC)
        subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.PREMIUM,
            is_active=True,
            expires_at=future_time,
        )

        assert subscription.expires_at == future_time
        assert subscription.is_active is True

    def test_subscription_upgrade_scenario(self):
        """Test subscription upgrade scenario (BASIC to PREMIUM).

        :returns: None
        """
        # Original BASIC subscription
        basic_subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
        )

        # Upgraded PREMIUM subscription
        premium_subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.PREMIUM,
            is_active=True,
        )

        assert basic_subscription.telegram_id == premium_subscription.telegram_id
        assert (
            basic_subscription.subscription_type
            != premium_subscription.subscription_type
        )
        assert basic_subscription.subscription_type == SubscriptionType.BASIC
        assert premium_subscription.subscription_type == SubscriptionType.PREMIUM

    def test_user_subscription_with_different_telegram_ids(self):
        """Test UserSubscription instances with different telegram IDs.

        :returns: None
        """
        user1_subscription = UserSubscription(
            telegram_id=111111111,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
        )

        user2_subscription = UserSubscription(
            telegram_id=222222222,
            subscription_type=SubscriptionType.PREMIUM,
            is_active=True,
        )

        assert user1_subscription.telegram_id != user2_subscription.telegram_id
        assert (
            user1_subscription.subscription_type != user2_subscription.subscription_type
        )

    def test_subscription_type_is_valid(self):
        assert SubscriptionType.is_valid("basic") is True
        assert SubscriptionType.is_valid("premium") is True
        assert SubscriptionType.is_valid("trial") is True
        assert SubscriptionType.is_valid("notatype") is False
        assert SubscriptionType.is_valid(123) is False
