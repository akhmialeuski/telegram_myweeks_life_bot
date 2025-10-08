"""Test module for user subscription schema classes.

This module contains tests for all user subscription-related schema classes,
ensuring proper validation and serialization behavior.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.database.schemas.user_subscription import (
    UserSubscriptionBase,
    UserSubscriptionCreate,
    UserSubscriptionInDB,
    UserSubscriptionResponse,
    UserSubscriptionUpdate,
)

# Test constants
TELEGRAM_ID = 123456789
IS_ACTIVE = True
EXPIRES_AT = datetime(2024, 12, 31, 23, 59, 59)
CREATED_AT = datetime(2023, 1, 1, 12, 0, 0)


class TestUserSubscriptionBase:
    """Test class for UserSubscriptionBase schema.

    This class contains all tests for the UserSubscriptionBase schema,
    including validation and field assignment.
    """

    def test_user_subscription_base_creation_with_required_fields(self) -> None:
        """Test UserSubscriptionBase creation with only required fields.

        This test verifies that UserSubscriptionBase can be created with
        only the telegram_id field (required field).

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionBase(telegram_id=TELEGRAM_ID)

        assert subscription.telegram_id == TELEGRAM_ID
        assert subscription.is_active is True  # Default value
        assert subscription.expires_at is None

    def test_user_subscription_base_creation_with_all_fields(self) -> None:
        """Test UserSubscriptionBase creation with all fields provided.

        This test verifies that UserSubscriptionBase can be created with
        all fields and they are properly assigned.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionBase(
            telegram_id=TELEGRAM_ID,
            is_active=IS_ACTIVE,
            expires_at=EXPIRES_AT,
        )

        assert subscription.telegram_id == TELEGRAM_ID
        assert subscription.is_active == IS_ACTIVE
        assert subscription.expires_at == EXPIRES_AT

    def test_user_subscription_base_telegram_id_required(self) -> None:
        """Test that telegram_id is required for UserSubscriptionBase.

        This test verifies that UserSubscriptionBase raises ValidationError
        when telegram_id is not provided.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserSubscriptionBase()

    def test_user_subscription_base_telegram_id_validation(self) -> None:
        """Test telegram_id field validation.

        This test verifies that telegram_id must be an integer.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserSubscriptionBase(telegram_id="not_an_int")

        with pytest.raises(ValidationError):
            UserSubscriptionBase(telegram_id=None)

    def test_user_subscription_base_is_active_validation(self) -> None:
        """Test is_active field validation.

        This test verifies that is_active must be a boolean.

        :returns: None
        :rtype: None
        """
        # Valid boolean should work
        subscription = UserSubscriptionBase(
            telegram_id=TELEGRAM_ID,
            is_active=False,
        )
        assert subscription.is_active is False

        # Invalid type should raise error
        with pytest.raises(ValidationError):
            UserSubscriptionBase(
                telegram_id=TELEGRAM_ID,
                is_active="not_a_bool",
            )

    def test_user_subscription_base_expires_at_validation(self) -> None:
        """Test expires_at field validation.

        This test verifies that expires_at must be a datetime object when provided.

        :returns: None
        :rtype: None
        """
        # Valid datetime should work
        subscription = UserSubscriptionBase(
            telegram_id=TELEGRAM_ID,
            expires_at=EXPIRES_AT,
        )
        assert subscription.expires_at == EXPIRES_AT

        # Invalid datetime should raise error
        with pytest.raises(ValidationError):
            UserSubscriptionBase(
                telegram_id=TELEGRAM_ID,
                expires_at="not_a_datetime",
            )

    def test_user_subscription_base_default_is_active(self) -> None:
        """Test that is_active has default value True.

        This test verifies that is_active field defaults to True
        when not explicitly provided.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionBase(telegram_id=TELEGRAM_ID)
        assert subscription.is_active is True

    def test_user_subscription_base_expires_at_none(self) -> None:
        """Test that expires_at can be None.

        This test verifies that expires_at field can be None
        for subscriptions without expiration.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionBase(
            telegram_id=TELEGRAM_ID,
            expires_at=None,
        )
        assert subscription.expires_at is None


class TestUserSubscriptionCreate:
    """Test class for UserSubscriptionCreate schema.

    This class contains all tests for the UserSubscriptionCreate schema,
    which inherits from UserSubscriptionBase.
    """

    def test_user_subscription_create_inherits_from_base(self) -> None:
        """Test that UserSubscriptionCreate inherits from UserSubscriptionBase.

        This test verifies that UserSubscriptionCreate is a subclass of UserSubscriptionBase
        and inherits all its functionality.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionCreate(telegram_id=TELEGRAM_ID)

        assert isinstance(subscription, UserSubscriptionBase)
        assert subscription.telegram_id == TELEGRAM_ID

    def test_user_subscription_create_with_all_fields(self) -> None:
        """Test UserSubscriptionCreate with all fields.

        This test verifies that UserSubscriptionCreate works with all available fields.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionCreate(
            telegram_id=TELEGRAM_ID,
            is_active=IS_ACTIVE,
            expires_at=EXPIRES_AT,
        )

        assert subscription.telegram_id == TELEGRAM_ID
        assert subscription.is_active == IS_ACTIVE
        assert subscription.expires_at == EXPIRES_AT


class TestUserSubscriptionUpdate:
    """Test class for UserSubscriptionUpdate schema.

    This class contains all tests for the UserSubscriptionUpdate schema,
    which is used for updating user subscription data.
    """

    def test_user_subscription_update_all_fields_optional(self) -> None:
        """Test that all fields in UserSubscriptionUpdate are optional.

        This test verifies that UserSubscriptionUpdate can be created
        without any fields (all are optional for updates).

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionUpdate()

        assert not hasattr(
            subscription, "telegram_id"
        )  # Not included in UserSubscriptionUpdate
        assert subscription.is_active is None
        assert subscription.expires_at is None

    def test_user_subscription_update_with_some_fields(self) -> None:
        """Test UserSubscriptionUpdate with some fields provided.

        This test verifies that UserSubscriptionUpdate can be created with
        only some fields for partial updates.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionUpdate(
            is_active=False,
        )

        assert subscription.is_active is False
        assert subscription.expires_at is None

    def test_user_subscription_update_with_all_fields(self) -> None:
        """Test UserSubscriptionUpdate with all fields provided.

        This test verifies that UserSubscriptionUpdate can be created with
        all available fields.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionUpdate(
            is_active=IS_ACTIVE,
            expires_at=EXPIRES_AT,
        )

        assert subscription.is_active == IS_ACTIVE
        assert subscription.expires_at == EXPIRES_AT

    def test_user_subscription_update_expires_at_none(self) -> None:
        """Test UserSubscriptionUpdate with expires_at set to None.

        This test verifies that UserSubscriptionUpdate can handle
        expires_at being explicitly set to None.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionUpdate(
            is_active=True,
            expires_at=None,
        )

        assert subscription.is_active is True
        assert subscription.expires_at is None


class TestUserSubscriptionInDB:
    """Test class for UserSubscriptionInDB schema.

    This class contains all tests for the UserSubscriptionInDB schema,
    which represents user subscription data as stored in the database.
    """

    def test_user_subscription_in_db_creation_with_required_fields(self) -> None:
        """Test UserSubscriptionInDB creation with required fields.

        This test verifies that UserSubscriptionInDB can be created with
        telegram_id, id, and created_at fields.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionInDB(
            id=1,
            telegram_id=TELEGRAM_ID,
            created_at=CREATED_AT,
        )

        assert subscription.id == 1
        assert subscription.telegram_id == TELEGRAM_ID
        assert subscription.created_at == CREATED_AT
        assert subscription.is_active is True  # Default value
        assert subscription.expires_at is None

    def test_user_subscription_in_db_creation_with_all_fields(self) -> None:
        """Test UserSubscriptionInDB creation with all fields.

        This test verifies that UserSubscriptionInDB can be created with
        all fields including database-specific ones.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionInDB(
            id=1,
            telegram_id=TELEGRAM_ID,
            is_active=IS_ACTIVE,
            expires_at=EXPIRES_AT,
            created_at=CREATED_AT,
        )

        assert subscription.id == 1
        assert subscription.telegram_id == TELEGRAM_ID
        assert subscription.is_active == IS_ACTIVE
        assert subscription.expires_at == EXPIRES_AT
        assert subscription.created_at == CREATED_AT

    def test_user_subscription_in_db_id_required(self) -> None:
        """Test that id is required for UserSubscriptionInDB.

        This test verifies that UserSubscriptionInDB raises ValidationError
        when id is not provided.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserSubscriptionInDB(
                telegram_id=TELEGRAM_ID,
                created_at=CREATED_AT,
            )

    def test_user_subscription_in_db_created_at_required(self) -> None:
        """Test that created_at is required for UserSubscriptionInDB.

        This test verifies that UserSubscriptionInDB raises ValidationError
        when created_at is not provided.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserSubscriptionInDB(
                id=1,
                telegram_id=TELEGRAM_ID,
            )

    def test_user_subscription_in_db_id_validation(self) -> None:
        """Test id field validation.

        This test verifies that id must be an integer.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserSubscriptionInDB(
                id="not_an_int",
                telegram_id=TELEGRAM_ID,
                created_at=CREATED_AT,
            )

    def test_user_subscription_in_db_created_at_validation(self) -> None:
        """Test created_at field validation.

        This test verifies that created_at must be a datetime object.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserSubscriptionInDB(
                id=1,
                telegram_id=TELEGRAM_ID,
                created_at="not_a_datetime",
            )

    def test_user_subscription_in_db_inherits_from_base(self) -> None:
        """Test that UserSubscriptionInDB inherits from UserSubscriptionBase.

        This test verifies that UserSubscriptionInDB is a subclass of UserSubscriptionBase
        and inherits all its functionality.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionInDB(
            id=1,
            telegram_id=TELEGRAM_ID,
            created_at=CREATED_AT,
        )

        assert isinstance(subscription, UserSubscriptionBase)


class TestUserSubscriptionResponse:
    """Test class for UserSubscriptionResponse schema.

    This class contains all tests for the UserSubscriptionResponse schema,
    which is used for API responses.
    """

    def test_user_subscription_response_inherits_from_in_db(self) -> None:
        """Test that UserSubscriptionResponse inherits from UserSubscriptionInDB.

        This test verifies that UserSubscriptionResponse is a subclass of UserSubscriptionInDB
        and inherits all its functionality.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionResponse(
            id=1,
            telegram_id=TELEGRAM_ID,
            created_at=CREATED_AT,
        )

        assert isinstance(subscription, UserSubscriptionInDB)
        assert isinstance(subscription, UserSubscriptionBase)
        assert subscription.id == 1
        assert subscription.telegram_id == TELEGRAM_ID
        assert subscription.created_at == CREATED_AT

    def test_user_subscription_response_with_all_fields(self) -> None:
        """Test UserSubscriptionResponse with all fields.

        This test verifies that UserSubscriptionResponse works with all available fields.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionResponse(
            id=1,
            telegram_id=TELEGRAM_ID,
            is_active=IS_ACTIVE,
            expires_at=EXPIRES_AT,
            created_at=CREATED_AT,
        )

        assert subscription.id == 1
        assert subscription.telegram_id == TELEGRAM_ID
        assert subscription.is_active == IS_ACTIVE
        assert subscription.expires_at == EXPIRES_AT
        assert subscription.created_at == CREATED_AT


class TestUserSubscriptionSchemaIntegration:
    """Test class for user subscription schema integration tests.

    This class contains integration tests for all user subscription schemas,
    testing JSON serialization and cross-schema compatibility.
    """

    def test_user_subscription_schema_json_serialization(self) -> None:
        """Test JSON serialization of user subscription schemas.

        This test verifies that user subscription schemas can be properly
        serialized to and from JSON.

        :returns: None
        :rtype: None
        """
        subscription_data = {
            "id": 1,
            "telegram_id": TELEGRAM_ID,
            "is_active": IS_ACTIVE,
            "expires_at": EXPIRES_AT.isoformat(),
            "created_at": CREATED_AT.isoformat(),
        }

        # Test UserSubscriptionInDB deserialization
        subscription_in_db = UserSubscriptionInDB.model_validate(subscription_data)
        assert subscription_in_db.telegram_id == TELEGRAM_ID
        assert subscription_in_db.is_active == IS_ACTIVE
        assert subscription_in_db.expires_at == EXPIRES_AT
        assert subscription_in_db.created_at == CREATED_AT

        # Test serialization
        serialized = subscription_in_db.model_dump(mode="json")
        assert serialized["expires_at"] == EXPIRES_AT.isoformat()
        assert serialized["created_at"] == CREATED_AT.isoformat()

    def test_user_subscription_base_to_create_compatibility(self) -> None:
        """Test compatibility between UserSubscriptionBase and UserSubscriptionCreate.

        This test verifies that data from UserSubscriptionBase can be used
        to create UserSubscriptionCreate instances.

        :returns: None
        :rtype: None
        """
        base_data = {
            "telegram_id": TELEGRAM_ID,
            "is_active": IS_ACTIVE,
            "expires_at": EXPIRES_AT,
        }

        subscription_base = UserSubscriptionBase(**base_data)
        subscription_create = UserSubscriptionCreate(**subscription_base.model_dump())

        assert subscription_create.telegram_id == subscription_base.telegram_id
        assert subscription_create.is_active == subscription_base.is_active
        assert subscription_create.expires_at == subscription_base.expires_at

    def test_user_subscription_update_partial_data(self) -> None:
        """Test UserSubscriptionUpdate with partial data.

        This test verifies that UserSubscriptionUpdate can handle partial
        updates with only some fields provided.

        :returns: None
        :rtype: None
        """
        partial_data = {
            "is_active": False,
        }

        subscription_update = UserSubscriptionUpdate(**partial_data)
        assert subscription_update.is_active is False
        assert subscription_update.expires_at is None

    def test_user_subscription_schema_datetime_handling(self) -> None:
        """Test datetime handling in user subscription schemas.

        This test verifies that datetime fields are properly handled
        in serialization and deserialization.

        :returns: None
        :rtype: None
        """
        subscription = UserSubscriptionInDB(
            id=1,
            telegram_id=TELEGRAM_ID,
            is_active=True,
            expires_at=EXPIRES_AT,
            created_at=CREATED_AT,
        )

        # Test JSON serialization preserves datetime format
        json_data = subscription.model_dump(mode="json")
        assert json_data["expires_at"] == EXPIRES_AT.isoformat()
        assert json_data["created_at"] == CREATED_AT.isoformat()

        # Test JSON deserialization restores datetime objects
        restored = UserSubscriptionInDB.model_validate(json_data)
        assert restored.expires_at == EXPIRES_AT
        assert restored.created_at == CREATED_AT
