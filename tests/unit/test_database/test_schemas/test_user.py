"""Test module for user schema classes.

This module contains tests for all user-related schema classes,
ensuring proper validation and serialization behavior.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.database.schemas.user import (
    UserBase,
    UserCreate,
    UserInDB,
    UserResponse,
    UserUpdate,
)

# Test constants
TELEGRAM_ID = 123456789
USERNAME = "testuser"
FIRST_NAME = "Test"
LAST_NAME = "User"
CREATED_AT = datetime(2023, 1, 1, 12, 0, 0)


class TestUserBase:
    """Test class for UserBase schema.

    This class contains all tests for the UserBase schema,
    including validation and field assignment.
    """

    def test_user_base_creation_with_required_fields(self) -> None:
        """Test UserBase creation with only required fields.

        This test verifies that UserBase can be created with
        only the telegram_id field (required field).

        :returns: None
        :rtype: None
        """
        user = UserBase(telegram_id=TELEGRAM_ID)

        assert user.telegram_id == TELEGRAM_ID
        assert user.username is None
        assert user.first_name is None
        assert user.last_name is None

    def test_user_base_creation_with_all_fields(self) -> None:
        """Test UserBase creation with all fields provided.

        This test verifies that UserBase can be created with
        all fields and they are properly assigned.

        :returns: None
        :rtype: None
        """
        user = UserBase(
            telegram_id=TELEGRAM_ID,
            username=USERNAME,
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
        )

        assert user.telegram_id == TELEGRAM_ID
        assert user.username == USERNAME
        assert user.first_name == FIRST_NAME
        assert user.last_name == LAST_NAME

    def test_user_base_telegram_id_required(self) -> None:
        """Test that telegram_id is required for UserBase.

        This test verifies that UserBase raises ValidationError
        when telegram_id is not provided.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserBase()

    def test_user_base_telegram_id_validation(self) -> None:
        """Test telegram_id field validation.

        This test verifies that telegram_id must be an integer.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserBase(telegram_id="not_an_int")

        with pytest.raises(ValidationError):
            UserBase(telegram_id=None)

    def test_user_base_optional_fields_none(self) -> None:
        """Test that optional fields can be None.

        This test verifies that username, first_name, and last_name
        can be explicitly set to None.

        :returns: None
        :rtype: None
        """
        user = UserBase(
            telegram_id=TELEGRAM_ID,
            username=None,
            first_name=None,
            last_name=None,
        )

        assert user.telegram_id == TELEGRAM_ID
        assert user.username is None
        assert user.first_name is None
        assert user.last_name is None


class TestUserCreate:
    """Test class for UserCreate schema.

    This class contains all tests for the UserCreate schema,
    which inherits from UserBase.
    """

    def test_user_create_inherits_from_user_base(self) -> None:
        """Test that UserCreate inherits from UserBase.

        This test verifies that UserCreate is a subclass of UserBase
        and inherits all its functionality.

        :returns: None
        :rtype: None
        """
        user = UserCreate(telegram_id=TELEGRAM_ID)

        assert isinstance(user, UserBase)
        assert user.telegram_id == TELEGRAM_ID

    def test_user_create_with_all_fields(self) -> None:
        """Test UserCreate with all fields.

        This test verifies that UserCreate works with all available fields.

        :returns: None
        :rtype: None
        """
        user = UserCreate(
            telegram_id=TELEGRAM_ID,
            username=USERNAME,
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
        )

        assert user.telegram_id == TELEGRAM_ID
        assert user.username == USERNAME
        assert user.first_name == FIRST_NAME
        assert user.last_name == LAST_NAME


class TestUserUpdate:
    """Test class for UserUpdate schema.

    This class contains all tests for the UserUpdate schema,
    which is used for updating user data.
    """

    def test_user_update_all_fields_optional(self) -> None:
        """Test that all fields in UserUpdate are optional.

        This test verifies that UserUpdate can be created
        without any fields (all are optional for updates).

        :returns: None
        :rtype: None
        """
        user = UserUpdate()

        assert not hasattr(user, "telegram_id")  # Not included in UserUpdate
        assert user.username is None
        assert user.first_name is None
        assert user.last_name is None

    def test_user_update_with_some_fields(self) -> None:
        """Test UserUpdate with some fields provided.

        This test verifies that UserUpdate can be created with
        only some fields for partial updates.

        :returns: None
        :rtype: None
        """
        user = UserUpdate(
            username="new_username",
            first_name="New Name",
        )

        assert user.username == "new_username"
        assert user.first_name == "New Name"
        assert user.last_name is None

    def test_user_update_with_all_fields(self) -> None:
        """Test UserUpdate with all fields provided.

        This test verifies that UserUpdate can be created with
        all available fields.

        :returns: None
        :rtype: None
        """
        user = UserUpdate(
            username=USERNAME,
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
        )

        assert user.username == USERNAME
        assert user.first_name == FIRST_NAME
        assert user.last_name == LAST_NAME


class TestUserInDB:
    """Test class for UserInDB schema.

    This class contains all tests for the UserInDB schema,
    which represents user data as stored in the database.
    """

    def test_user_in_db_creation_with_required_fields(self) -> None:
        """Test UserInDB creation with required fields.

        This test verifies that UserInDB can be created with
        telegram_id and created_at fields.

        :returns: None
        :rtype: None
        """
        user = UserInDB(
            telegram_id=TELEGRAM_ID,
            created_at=CREATED_AT,
        )

        assert user.telegram_id == TELEGRAM_ID
        assert user.created_at == CREATED_AT
        assert user.username is None
        assert user.first_name is None
        assert user.last_name is None
        assert user.settings is None
        assert user.subscription is None

    def test_user_in_db_creation_with_all_fields(self) -> None:
        """Test UserInDB creation with all fields.

        This test verifies that UserInDB can be created with
        all fields including relationships.

        :returns: None
        :rtype: None
        """
        user = UserInDB(
            telegram_id=TELEGRAM_ID,
            username=USERNAME,
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
            created_at=CREATED_AT,
            settings=None,  # Would be UserSettingsResponse object
            subscription=None,  # Would be UserSubscriptionResponse object
        )

        assert user.telegram_id == TELEGRAM_ID
        assert user.username == USERNAME
        assert user.first_name == FIRST_NAME
        assert user.last_name == LAST_NAME
        assert user.created_at == CREATED_AT
        assert user.settings is None
        assert user.subscription is None

    def test_user_in_db_created_at_required(self) -> None:
        """Test that created_at is required for UserInDB.

        This test verifies that UserInDB raises ValidationError
        when created_at is not provided.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserInDB(telegram_id=TELEGRAM_ID)

    def test_user_in_db_created_at_validation(self) -> None:
        """Test created_at field validation.

        This test verifies that created_at must be a datetime object.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserInDB(
                telegram_id=TELEGRAM_ID,
                created_at="not_a_datetime",
            )

    def test_user_in_db_inherits_from_user_base(self) -> None:
        """Test that UserInDB inherits from UserBase.

        This test verifies that UserInDB is a subclass of UserBase
        and inherits all its functionality.

        :returns: None
        :rtype: None
        """
        user = UserInDB(
            telegram_id=TELEGRAM_ID,
            created_at=CREATED_AT,
        )

        assert isinstance(user, UserBase)


class TestUserResponse:
    """Test class for UserResponse schema.

    This class contains all tests for the UserResponse schema,
    which is used for API responses.
    """

    def test_user_response_inherits_from_user_in_db(self) -> None:
        """Test that UserResponse inherits from UserInDB.

        This test verifies that UserResponse is a subclass of UserInDB
        and inherits all its functionality.

        :returns: None
        :rtype: None
        """
        user = UserResponse(
            telegram_id=TELEGRAM_ID,
            created_at=CREATED_AT,
        )

        assert isinstance(user, UserInDB)
        assert isinstance(user, UserBase)
        assert user.telegram_id == TELEGRAM_ID
        assert user.created_at == CREATED_AT

    def test_user_response_with_all_fields(self) -> None:
        """Test UserResponse with all fields.

        This test verifies that UserResponse works with all available fields.

        :returns: None
        :rtype: None
        """
        user = UserResponse(
            telegram_id=TELEGRAM_ID,
            username=USERNAME,
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
            created_at=CREATED_AT,
            settings=None,
            subscription=None,
        )

        assert user.telegram_id == TELEGRAM_ID
        assert user.username == USERNAME
        assert user.first_name == FIRST_NAME
        assert user.last_name == LAST_NAME
        assert user.created_at == CREATED_AT
        assert user.settings is None
        assert user.subscription is None


class TestUserSchemaIntegration:
    """Test class for user schema integration tests.

    This class contains integration tests for all user schemas,
    testing JSON serialization and cross-schema compatibility.
    """

    def test_user_schema_json_serialization(self) -> None:
        """Test JSON serialization of user schemas.

        This test verifies that user schemas can be properly
        serialized to and from JSON.

        :returns: None
        :rtype: None
        """
        user_data = {
            "telegram_id": TELEGRAM_ID,
            "username": USERNAME,
            "first_name": FIRST_NAME,
            "last_name": LAST_NAME,
            "created_at": CREATED_AT.isoformat(),
        }

        # Test UserInDB deserialization
        user_in_db = UserInDB.model_validate(user_data)
        assert user_in_db.telegram_id == TELEGRAM_ID
        assert user_in_db.created_at == CREATED_AT

        # Test serialization
        serialized = user_in_db.model_dump(mode="json")
        assert serialized["created_at"] == CREATED_AT.isoformat()

    def test_user_base_to_user_create_compatibility(self) -> None:
        """Test compatibility between UserBase and UserCreate.

        This test verifies that data from UserBase can be used
        to create UserCreate instances.

        :returns: None
        :rtype: None
        """
        base_data = {
            "telegram_id": TELEGRAM_ID,
            "username": USERNAME,
            "first_name": FIRST_NAME,
            "last_name": LAST_NAME,
        }

        user_base = UserBase(**base_data)
        user_create = UserCreate(**user_base.model_dump())

        assert user_create.telegram_id == user_base.telegram_id
        assert user_create.username == user_base.username
        assert user_create.first_name == user_base.first_name
        assert user_create.last_name == user_base.last_name

    def test_user_update_partial_data(self) -> None:
        """Test UserUpdate with partial data.

        This test verifies that UserUpdate can handle partial
        updates with only some fields provided.

        :returns: None
        :rtype: None
        """
        partial_data = {
            "username": "updated_username",
        }

        user_update = UserUpdate(**partial_data)
        assert user_update.username == "updated_username"
        assert user_update.first_name is None
        assert user_update.last_name is None
