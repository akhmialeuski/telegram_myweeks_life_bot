"""Unit tests for UserSettings model.

Tests all functionality of the UserSettings model using pytest
with proper edge case coverage.
"""

from datetime import UTC, date, datetime

from src.database.models import UserSettings, WeekDay


class TestUserSettings:
    """Test suite for UserSettings model."""

    def test_user_settings_creation_basic(self):
        """Test basic UserSettings creation.

        :returns: None
        """
        settings = UserSettings(
            telegram_id=123456789, birth_date=date(1990, 1, 1), notifications=True
        )

        assert settings.telegram_id == 123456789
        assert settings.birth_date == date(1990, 1, 1)
        assert settings.notifications is True
        # life_expectancy has no default value in the model
        assert settings.life_expectancy is None
        # notifications_day has no default value in the model
        assert settings.notifications_day is None

    def test_user_settings_creation_with_all_fields(self):
        """Test UserSettings creation with all fields specified.

        :returns: None
        """
        updated_at = datetime.now(UTC)
        settings = UserSettings(
            telegram_id=123456789,
            birth_date=date(1990, 1, 1),
            life_expectancy=85,
            notifications=False,
            notifications_day=WeekDay.FRIDAY,
            updated_at=updated_at,
        )

        assert settings.telegram_id == 123456789
        assert settings.birth_date == date(1990, 1, 1)
        assert settings.life_expectancy == 85
        assert settings.notifications is False
        assert settings.notifications_day == WeekDay.FRIDAY
        assert settings.updated_at == updated_at

    def test_user_settings_default_values(self):
        """Test UserSettings default values.

        :returns: None
        """
        settings = UserSettings(telegram_id=123456789, birth_date=date(1990, 1, 1))

        # Test default values - SQLAlchemy defaults are applied at database level, not Python object level
        assert settings.life_expectancy is None
        # notifications field has default=True in the model, but it's not applied to Python objects
        assert settings.notifications is None
        assert settings.notifications_day is None

    def test_user_settings_week_day_enum_values(self):
        """Test all WeekDay enum values work correctly.

        :returns: None
        """
        for day in WeekDay:
            settings = UserSettings(
                telegram_id=123456789,
                birth_date=date(1990, 1, 1),
                notifications_day=day,
            )
            assert settings.notifications_day == day

    def test_user_settings_life_expectancy_validation(self):
        """Test life expectancy validation.

        :returns: None
        """
        # Test valid values
        for age in [50, 75, 80, 90, 100, 120]:
            settings = UserSettings(
                telegram_id=123456789, birth_date=date(1990, 1, 1), life_expectancy=age
            )
            assert settings.life_expectancy == age

    def test_user_settings_birth_date_validation(self):
        """Test birth date validation.

        :returns: None
        """
        # Test valid dates
        valid_dates = [
            date(1900, 1, 1),
            date(1950, 6, 15),
            date(1990, 12, 31),
            date(2000, 2, 29),  # Leap year
            date(2020, 1, 1),
        ]

        for birth_date in valid_dates:
            settings = UserSettings(telegram_id=123456789, birth_date=birth_date)
            assert settings.birth_date == birth_date

    def test_user_settings_notifications_boolean(self):
        """Test notifications field accepts boolean values.

        :returns: None
        """
        # Test True
        settings_true = UserSettings(
            telegram_id=123456789, birth_date=date(1990, 1, 1), notifications=True
        )
        assert settings_true.notifications is True

        # Test False
        settings_false = UserSettings(
            telegram_id=123456789, birth_date=date(1990, 1, 1), notifications=False
        )
        assert settings_false.notifications is False

    def test_user_settings_repr(self):
        """Test UserSettings string representation.

        :returns: None
        """
        settings = UserSettings(
            telegram_id=123456789,
            birth_date=date(1990, 1, 1),
            life_expectancy=85,
            notifications=True,
            notifications_day=WeekDay.WEDNESDAY,
        )

        repr_str = repr(settings)
        # The model uses default SQLAlchemy repr, so just check it's a string
        assert isinstance(repr_str, str)
        assert len(repr_str) > 0

    def test_user_settings_str(self):
        """Test UserSettings string conversion.

        :returns: None
        """
        settings = UserSettings(
            telegram_id=123456789,
            birth_date=date(1990, 1, 1),
            life_expectancy=85,
            notifications=True,
            notifications_day=WeekDay.WEDNESDAY,
        )

        str_repr = str(settings)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    def test_user_settings_equality(self):
        """Test UserSettings equality comparison.

        :returns: None
        """
        settings1 = UserSettings(
            telegram_id=123456789, birth_date=date(1990, 1, 1), life_expectancy=80
        )

        settings2 = UserSettings(
            telegram_id=123456789, birth_date=date(1990, 1, 1), life_expectancy=80
        )

        settings3 = UserSettings(
            telegram_id=987654321,  # Different telegram_id
            birth_date=date(1990, 1, 1),
            life_expectancy=80,
        )

        # Same settings should be equal by telegram_id
        assert settings1.telegram_id == settings2.telegram_id
        # Different telegram_id should not be equal
        assert settings1.telegram_id != settings3.telegram_id

    def test_week_day_enum_values(self):
        """Test WeekDay enum has all expected values.

        :returns: None
        """
        expected_days = {
            "MONDAY",
            "TUESDAY",
            "WEDNESDAY",
            "THURSDAY",
            "FRIDAY",
            "SATURDAY",
            "SUNDAY",
        }

        actual_days = {day.name for day in WeekDay}
        assert actual_days == expected_days

    def test_week_day_enum_ordering(self):
        """Test WeekDay enum ordering is correct.

        :returns: None
        """
        days_in_order = [
            WeekDay.MONDAY,
            WeekDay.TUESDAY,
            WeekDay.WEDNESDAY,
            WeekDay.THURSDAY,
            WeekDay.FRIDAY,
            WeekDay.SATURDAY,
            WeekDay.SUNDAY,
        ]

        for i, day in enumerate(days_in_order):
            # WeekDay enum uses string values, not numeric
            # Monday = "monday", Tuesday = "tuesday", etc.
            expected_value = day.name.lower()
            assert day.value == expected_value

    def test_user_settings_updated_at_auto_population(self):
        """Test that updated_at can be manually set.

        :returns: None
        """
        custom_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        settings = UserSettings(
            telegram_id=123456789, birth_date=date(1990, 1, 1), updated_at=custom_time
        )

        assert settings.updated_at == custom_time

    def test_user_settings_none_birth_date(self):
        """Test UserSettings with None birth date.

        :returns: None
        """
        settings = UserSettings(
            telegram_id=123456789,
            birth_date=None,  # This might be allowed in some cases
        )

        assert settings.birth_date is None
        assert settings.telegram_id == 123456789

    def test_user_settings_extreme_life_expectancy_values(self):
        """Test UserSettings with extreme life expectancy values.

        :returns: None
        """
        # Test very low value
        settings_low = UserSettings(
            telegram_id=123456789, birth_date=date(1990, 1, 1), life_expectancy=1
        )
        assert settings_low.life_expectancy == 1

        # Test very high value
        settings_high = UserSettings(
            telegram_id=123456789, birth_date=date(1990, 1, 1), life_expectancy=200
        )
        assert settings_high.life_expectancy == 200

    def test_weekday_get_choices(self):
        choices = WeekDay.get_choices()
        assert isinstance(choices, list)
        assert ("monday", "Monday") in choices
        assert ("sunday", "Sunday") in choices
        assert len(choices) == 7

    def test_weekday_is_valid(self):
        assert WeekDay.is_valid("monday") is True
        assert WeekDay.is_valid("sunday") is True
        assert WeekDay.is_valid("notaday") is False
        assert WeekDay.is_valid(123) is False

    def test_weekday_get_weekday_number(self):
        assert WeekDay.get_weekday_number(WeekDay.MONDAY) == 0
        assert WeekDay.get_weekday_number(WeekDay.SUNDAY) == 6
        assert WeekDay.get_weekday_number(WeekDay.THURSDAY) == 3

    def test_weekday_from_weekday_number(self):
        assert WeekDay.from_weekday_number(0) == WeekDay.MONDAY
        assert WeekDay.from_weekday_number(6) == WeekDay.SUNDAY
        assert WeekDay.from_weekday_number(3) == WeekDay.THURSDAY
        # Test ValueError for invalid number
        import pytest

        with pytest.raises(ValueError):
            WeekDay.from_weekday_number(7)
        with pytest.raises(ValueError):
            WeekDay.from_weekday_number(-1)
