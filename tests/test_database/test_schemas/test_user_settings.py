"""Test module for user settings schema classes.

This module contains tests for all user settings-related schema classes,
ensuring proper validation and serialization behavior.
"""

from datetime import date, datetime, time

import pytest
from pydantic import ValidationError

from src.core.enums import WeekDay
from src.database.schemas.user_settings import (
    UserSettingsBase,
    UserSettingsCreate,
    UserSettingsInDB,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from tests.conftest import (
    DEFAULT_LIFE_EXPECTANCY,
    TEST_BIRTH_DAY,
    TEST_BIRTH_MONTH,
    TEST_BIRTH_YEAR,
    TEST_USER_ID,
)

# Test constants
TELEGRAM_ID = TEST_USER_ID
BIRTH_DATE = date(TEST_BIRTH_YEAR, TEST_BIRTH_MONTH, TEST_BIRTH_DAY)
NOTIFICATIONS_DAY = WeekDay.MONDAY
LIFE_EXPECTANCY = DEFAULT_LIFE_EXPECTANCY
TIMEZONE = "Europe/Warsaw"
NOTIFICATIONS = True
NOTIFICATIONS_TIME = time(9, 30, 0)
UPDATED_AT = datetime(2023, 1, 1, 12, 0, 0)


class TestUserSettingsBase:
    """Test class for UserSettingsBase schema.

    This class contains all tests for the UserSettingsBase schema,
    including validation and field assignment.
    """

    def test_user_settings_base_creation_with_required_fields(self) -> None:
        """Test UserSettingsBase creation with only required fields.

        This test verifies that UserSettingsBase can be created with
        only the telegram_id field (required field).

        :returns: None
        :rtype: None
        """
        settings = UserSettingsBase(telegram_id=TELEGRAM_ID)

        assert settings.telegram_id == TELEGRAM_ID
        assert settings.birth_date is None
        assert settings.notifications_day is None
        assert settings.life_expectancy is None
        assert settings.timezone is None
        assert settings.notifications is True  # Default value
        assert settings.notifications_time is None

    def test_user_settings_base_creation_with_all_fields(self) -> None:
        """Test UserSettingsBase creation with all fields provided.

        This test verifies that UserSettingsBase can be created with
        all fields and they are properly assigned.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsBase(
            telegram_id=TELEGRAM_ID,
            birth_date=BIRTH_DATE,
            notifications_day=NOTIFICATIONS_DAY,
            life_expectancy=LIFE_EXPECTANCY,
            timezone=TIMEZONE,
            notifications=NOTIFICATIONS,
            notifications_time=NOTIFICATIONS_TIME,
        )

        assert settings.telegram_id == TELEGRAM_ID
        assert settings.birth_date == BIRTH_DATE
        assert settings.notifications_day == NOTIFICATIONS_DAY
        assert settings.life_expectancy == LIFE_EXPECTANCY
        assert settings.timezone == TIMEZONE
        assert settings.notifications == NOTIFICATIONS
        assert settings.notifications_time == NOTIFICATIONS_TIME

    def test_user_settings_base_telegram_id_required(self) -> None:
        """Test that telegram_id is required for UserSettingsBase.

        This test verifies that UserSettingsBase raises ValidationError
        when telegram_id is not provided.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserSettingsBase()

    def test_user_settings_base_telegram_id_validation(self) -> None:
        """Test telegram_id field validation.

        This test verifies that telegram_id must be an integer.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserSettingsBase(telegram_id="not_an_int")

        with pytest.raises(ValidationError):
            UserSettingsBase(telegram_id=None)

    def test_user_settings_base_birth_date_validation(self) -> None:
        """Test birth_date field validation.

        This test verifies that birth_date must be a date object when provided.

        :returns: None
        :rtype: None
        """
        # Valid date should work
        settings = UserSettingsBase(
            telegram_id=TELEGRAM_ID,
            birth_date=BIRTH_DATE,
        )
        assert settings.birth_date == BIRTH_DATE

        # Invalid date should raise error
        with pytest.raises(ValidationError):
            UserSettingsBase(
                telegram_id=TELEGRAM_ID,
                birth_date="not_a_date",
            )

    def test_user_settings_base_life_expectancy_validation(self) -> None:
        """Test life_expectancy field validation.

        This test verifies that life_expectancy must be an integer when provided.

        :returns: None
        :rtype: None
        """
        # Valid integer should work
        settings = UserSettingsBase(
            telegram_id=TELEGRAM_ID,
            life_expectancy=85,
        )
        assert settings.life_expectancy == 85

        # Invalid type should raise error
        with pytest.raises(ValidationError):
            UserSettingsBase(
                telegram_id=TELEGRAM_ID,
                life_expectancy="not_an_int",
            )

    def test_user_settings_base_notifications_validation(self) -> None:
        """Test notifications field validation.

        This test verifies that notifications must be a boolean.

        :returns: None
        :rtype: None
        """
        # Valid boolean should work
        settings = UserSettingsBase(
            telegram_id=TELEGRAM_ID,
            notifications=False,
        )
        assert settings.notifications is False

        # Invalid type should raise error
        with pytest.raises(ValidationError):
            UserSettingsBase(
                telegram_id=TELEGRAM_ID,
                notifications="not_a_bool",
            )

    def test_user_settings_base_notifications_time_validation(self) -> None:
        """Test notifications_time field validation.

        This test verifies that notifications_time must be a time object when provided.

        :returns: None
        :rtype: None
        """
        # Valid time should work
        settings = UserSettingsBase(
            telegram_id=TELEGRAM_ID,
            notifications_time=NOTIFICATIONS_TIME,
        )
        assert settings.notifications_time == NOTIFICATIONS_TIME

        # Invalid time should raise error
        with pytest.raises(ValidationError):
            UserSettingsBase(
                telegram_id=TELEGRAM_ID,
                notifications_time="not_a_time",
            )

    def test_user_settings_base_default_notifications(self) -> None:
        """Test that notifications has default value True.

        This test verifies that notifications field defaults to True
        when not explicitly provided.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsBase(telegram_id=TELEGRAM_ID)
        assert settings.notifications is True


class TestUserSettingsCreate:
    """Test class for UserSettingsCreate schema.

    This class contains all tests for the UserSettingsCreate schema,
    which inherits from UserSettingsBase.
    """

    def test_user_settings_create_inherits_from_base(self) -> None:
        """Test that UserSettingsCreate inherits from UserSettingsBase.

        This test verifies that UserSettingsCreate is a subclass of UserSettingsBase
        and inherits all its functionality.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsCreate(telegram_id=TELEGRAM_ID)

        assert isinstance(settings, UserSettingsBase)
        assert settings.telegram_id == TELEGRAM_ID

    def test_user_settings_create_with_all_fields(self) -> None:
        """Test UserSettingsCreate with all fields.

        This test verifies that UserSettingsCreate works with all available fields.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsCreate(
            telegram_id=TELEGRAM_ID,
            birth_date=BIRTH_DATE,
            notifications_day=NOTIFICATIONS_DAY,
            life_expectancy=LIFE_EXPECTANCY,
            timezone=TIMEZONE,
            notifications=NOTIFICATIONS,
            notifications_time=NOTIFICATIONS_TIME,
        )

        assert settings.telegram_id == TELEGRAM_ID
        assert settings.birth_date == BIRTH_DATE
        assert settings.notifications_day == NOTIFICATIONS_DAY
        assert settings.life_expectancy == LIFE_EXPECTANCY
        assert settings.timezone == TIMEZONE
        assert settings.notifications == NOTIFICATIONS
        assert settings.notifications_time == NOTIFICATIONS_TIME


class TestUserSettingsUpdate:
    """Test class for UserSettingsUpdate schema.

    This class contains all tests for the UserSettingsUpdate schema,
    which is used for updating user settings data.
    """

    def test_user_settings_update_all_fields_optional(self) -> None:
        """Test that all fields in UserSettingsUpdate are optional.

        This test verifies that UserSettingsUpdate can be created
        without any fields (all are optional for updates).

        :returns: None
        :rtype: None
        """
        settings = UserSettingsUpdate()

        assert not hasattr(
            settings, "telegram_id"
        )  # Not included in UserSettingsUpdate
        assert settings.birth_date is None
        assert settings.notifications_day is None
        assert settings.life_expectancy is None
        assert settings.timezone is None
        assert settings.notifications is None
        assert settings.notifications_time is None

    def test_user_settings_update_with_some_fields(self) -> None:
        """Test UserSettingsUpdate with some fields provided.

        This test verifies that UserSettingsUpdate can be created with
        only some fields for partial updates.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsUpdate(
            birth_date=BIRTH_DATE,
            life_expectancy=LIFE_EXPECTANCY,
        )

        assert settings.birth_date == BIRTH_DATE
        assert settings.life_expectancy == LIFE_EXPECTANCY
        assert settings.notifications_day is None
        assert settings.timezone is None
        assert settings.notifications is None
        assert settings.notifications_time is None

    def test_user_settings_update_with_all_fields(self) -> None:
        """Test UserSettingsUpdate with all fields provided.

        This test verifies that UserSettingsUpdate can be created with
        all available fields.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsUpdate(
            birth_date=BIRTH_DATE,
            notifications_day=NOTIFICATIONS_DAY,
            life_expectancy=LIFE_EXPECTANCY,
            timezone=TIMEZONE,
            notifications=NOTIFICATIONS,
            notifications_time=NOTIFICATIONS_TIME,
        )

        assert settings.birth_date == BIRTH_DATE
        assert settings.notifications_day == NOTIFICATIONS_DAY
        assert settings.life_expectancy == LIFE_EXPECTANCY
        assert settings.timezone == TIMEZONE
        assert settings.notifications == NOTIFICATIONS
        assert settings.notifications_time == NOTIFICATIONS_TIME


class TestUserSettingsInDB:
    """Test class for UserSettingsInDB schema.

    This class contains all tests for the UserSettingsInDB schema,
    which represents user settings data as stored in the database.
    """

    def test_user_settings_in_db_creation_with_required_fields(self) -> None:
        """Test UserSettingsInDB creation with required fields.

        This test verifies that UserSettingsInDB can be created with
        telegram_id, id, and updated_at fields.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsInDB(
            id=1,
            telegram_id=TELEGRAM_ID,
            updated_at=UPDATED_AT,
        )

        assert settings.id == 1
        assert settings.telegram_id == TELEGRAM_ID
        assert settings.updated_at == UPDATED_AT
        assert settings.birth_date is None
        assert settings.notifications_day is None
        assert settings.life_expectancy is None
        assert settings.timezone is None
        assert settings.notifications is True  # Default value
        assert settings.notifications_time is None

    def test_user_settings_in_db_creation_with_all_fields(self) -> None:
        """Test UserSettingsInDB creation with all fields.

        This test verifies that UserSettingsInDB can be created with
        all fields including database-specific ones.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsInDB(
            id=1,
            telegram_id=TELEGRAM_ID,
            birth_date=BIRTH_DATE,
            notifications_day=NOTIFICATIONS_DAY,
            life_expectancy=LIFE_EXPECTANCY,
            timezone=TIMEZONE,
            notifications=NOTIFICATIONS,
            notifications_time=NOTIFICATIONS_TIME,
            updated_at=UPDATED_AT,
        )

        assert settings.id == 1
        assert settings.telegram_id == TELEGRAM_ID
        assert settings.birth_date == BIRTH_DATE
        assert settings.notifications_day == NOTIFICATIONS_DAY
        assert settings.life_expectancy == LIFE_EXPECTANCY
        assert settings.timezone == TIMEZONE
        assert settings.notifications == NOTIFICATIONS
        assert settings.notifications_time == NOTIFICATIONS_TIME
        assert settings.updated_at == UPDATED_AT

    def test_user_settings_in_db_id_required(self) -> None:
        """Test that id is required for UserSettingsInDB.

        This test verifies that UserSettingsInDB raises ValidationError
        when id is not provided.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserSettingsInDB(
                telegram_id=TELEGRAM_ID,
                updated_at=UPDATED_AT,
            )

    def test_user_settings_in_db_updated_at_required(self) -> None:
        """Test that updated_at is required for UserSettingsInDB.

        This test verifies that UserSettingsInDB raises ValidationError
        when updated_at is not provided.

        :returns: None
        :rtype: None
        """
        with pytest.raises(ValidationError):
            UserSettingsInDB(
                id=1,
                telegram_id=TELEGRAM_ID,
            )

    def test_user_settings_in_db_inherits_from_base(self) -> None:
        """Test that UserSettingsInDB inherits from UserSettingsBase.

        This test verifies that UserSettingsInDB is a subclass of UserSettingsBase
        and inherits all its functionality.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsInDB(
            id=1,
            telegram_id=TELEGRAM_ID,
            updated_at=UPDATED_AT,
        )

        assert isinstance(settings, UserSettingsBase)


class TestUserSettingsResponse:
    """Test class for UserSettingsResponse schema.

    This class contains all tests for the UserSettingsResponse schema,
    which is used for API responses.
    """

    def test_user_settings_response_inherits_from_in_db(self) -> None:
        """Test that UserSettingsResponse inherits from UserSettingsInDB.

        This test verifies that UserSettingsResponse is a subclass of UserSettingsInDB
        and inherits all its functionality.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsResponse(
            id=1,
            telegram_id=TELEGRAM_ID,
            updated_at=UPDATED_AT,
        )

        assert isinstance(settings, UserSettingsInDB)
        assert isinstance(settings, UserSettingsBase)
        assert settings.id == 1
        assert settings.telegram_id == TELEGRAM_ID
        assert settings.updated_at == UPDATED_AT

    def test_user_settings_response_with_all_fields(self) -> None:
        """Test UserSettingsResponse with all fields.

        This test verifies that UserSettingsResponse works with all available fields.

        :returns: None
        :rtype: None
        """
        settings = UserSettingsResponse(
            id=1,
            telegram_id=TELEGRAM_ID,
            birth_date=BIRTH_DATE,
            notifications_day=NOTIFICATIONS_DAY,
            life_expectancy=LIFE_EXPECTANCY,
            timezone=TIMEZONE,
            notifications=NOTIFICATIONS,
            notifications_time=NOTIFICATIONS_TIME,
            updated_at=UPDATED_AT,
        )

        assert settings.id == 1
        assert settings.telegram_id == TELEGRAM_ID
        assert settings.birth_date == BIRTH_DATE
        assert settings.notifications_day == NOTIFICATIONS_DAY
        assert settings.life_expectancy == LIFE_EXPECTANCY
        assert settings.timezone == TIMEZONE
        assert settings.notifications == NOTIFICATIONS
        assert settings.notifications_time == NOTIFICATIONS_TIME
        assert settings.updated_at == UPDATED_AT


class TestUserSettingsSchemaIntegration:
    """Test class for user settings schema integration tests.

    This class contains integration tests for all user settings schemas,
    testing JSON serialization and cross-schema compatibility.
    """

    def test_user_settings_schema_json_serialization(self) -> None:
        """Test JSON serialization of user settings schemas.

        This test verifies that user settings schemas can be properly
        serialized to and from JSON.

        :returns: None
        :rtype: None
        """
        settings_data = {
            "id": 1,
            "telegram_id": TELEGRAM_ID,
            "birth_date": BIRTH_DATE.isoformat(),
            "notifications_day": NOTIFICATIONS_DAY,
            "life_expectancy": LIFE_EXPECTANCY,
            "timezone": TIMEZONE,
            "notifications": NOTIFICATIONS,
            "notifications_time": NOTIFICATIONS_TIME.isoformat(),
            "updated_at": UPDATED_AT.isoformat(),
        }

        # Test UserSettingsInDB deserialization
        settings_in_db = UserSettingsInDB.model_validate(settings_data)
        assert settings_in_db.telegram_id == TELEGRAM_ID
        assert settings_in_db.birth_date == BIRTH_DATE
        assert settings_in_db.updated_at == UPDATED_AT

        # Test serialization
        serialized = settings_in_db.model_dump(mode="json")
        assert serialized["birth_date"] == BIRTH_DATE.isoformat()
        assert serialized["updated_at"] == UPDATED_AT.isoformat()

    def test_user_settings_base_to_create_compatibility(self) -> None:
        """Test compatibility between UserSettingsBase and UserSettingsCreate.

        This test verifies that data from UserSettingsBase can be used
        to create UserSettingsCreate instances.

        :returns: None
        :rtype: None
        """
        base_data = {
            "telegram_id": TELEGRAM_ID,
            "birth_date": BIRTH_DATE,
            "notifications_day": NOTIFICATIONS_DAY,
            "life_expectancy": LIFE_EXPECTANCY,
            "timezone": TIMEZONE,
            "notifications": NOTIFICATIONS,
            "notifications_time": NOTIFICATIONS_TIME,
        }

        settings_base = UserSettingsBase(**base_data)
        settings_create = UserSettingsCreate(**settings_base.model_dump())

        assert settings_create.telegram_id == settings_base.telegram_id
        assert settings_create.birth_date == settings_base.birth_date
        assert settings_create.notifications_day == settings_base.notifications_day
        assert settings_create.life_expectancy == settings_base.life_expectancy
        assert settings_create.timezone == settings_base.timezone
        assert settings_create.notifications == settings_base.notifications
        assert settings_create.notifications_time == settings_base.notifications_time

    def test_user_settings_update_partial_data(self) -> None:
        """Test UserSettingsUpdate with partial data.

        This test verifies that UserSettingsUpdate can handle partial
        updates with only some fields provided.

        :returns: None
        :rtype: None
        """
        partial_data = {
            "birth_date": BIRTH_DATE,
            "notifications": False,
        }

        settings_update = UserSettingsUpdate(**partial_data)
        assert settings_update.birth_date == BIRTH_DATE
        assert settings_update.notifications is False
        assert settings_update.life_expectancy is None
        assert settings_update.timezone is None
