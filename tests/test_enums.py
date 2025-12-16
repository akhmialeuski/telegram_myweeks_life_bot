"""Tests for enums module.

This module contains unit tests for the SubscriptionType and other enums
defined in the src.enums module.
"""

from src.enums import SubscriptionType, SupportedLanguage, WeekDay


class TestSubscriptionTypeIsValid:
    """Test class for SubscriptionType.is_valid class method.

    This class contains all tests for the is_valid method,
    including various input types and edge cases.
    """

    def test_is_valid_with_subscription_type_instance(self) -> None:
        """Test is_valid with SubscriptionType enum instance.

        This test verifies that is_valid returns True when passed
        a SubscriptionType enum instance directly.
        """
        assert SubscriptionType.is_valid(SubscriptionType.BASIC) is True
        assert SubscriptionType.is_valid(SubscriptionType.PREMIUM) is True
        assert SubscriptionType.is_valid(SubscriptionType.TRIAL) is True

    def test_is_valid_with_valid_string(self) -> None:
        """Test is_valid with valid string values.

        This test verifies that is_valid returns True when passed
        valid string values that correspond to enum members.
        """
        assert SubscriptionType.is_valid("basic") is True
        assert SubscriptionType.is_valid("premium") is True
        assert SubscriptionType.is_valid("trial") is True

    def test_is_valid_with_invalid_string(self) -> None:
        """Test is_valid with invalid string values.

        This test verifies that is_valid returns False when passed
        invalid string values that don't correspond to enum members.
        """
        assert SubscriptionType.is_valid("invalid") is False
        assert SubscriptionType.is_valid("enterprise") is False
        assert SubscriptionType.is_valid("") is False

    def test_is_valid_with_non_string_non_enum(self) -> None:
        """Test is_valid with non-string and non-enum values.

        This test verifies that is_valid returns False when passed
        values that are neither strings nor SubscriptionType instances.
        """
        assert SubscriptionType.is_valid(123) is False
        assert SubscriptionType.is_valid(None) is False
        assert SubscriptionType.is_valid([]) is False
        assert SubscriptionType.is_valid({}) is False
        assert SubscriptionType.is_valid(3.14) is False


class TestWeekDay:
    """Test class for WeekDay enum.

    This class contains tests for the WeekDay enumeration.
    """

    def test_weekday_values(self) -> None:
        """Test that WeekDay has all expected values.

        This test verifies that the WeekDay enum contains
        all seven days of the week.
        """
        assert WeekDay.MONDAY is not None
        assert WeekDay.TUESDAY is not None
        assert WeekDay.WEDNESDAY is not None
        assert WeekDay.THURSDAY is not None
        assert WeekDay.FRIDAY is not None
        assert WeekDay.SATURDAY is not None
        assert WeekDay.SUNDAY is not None

    def test_weekday_count(self) -> None:
        """Test that WeekDay has exactly 7 members.

        This test verifies that the WeekDay enum has
        exactly 7 members for all days of the week.
        """
        assert len(WeekDay) == 7


class TestSupportedLanguage:
    """Test class for SupportedLanguage enum.

    This class contains tests for the SupportedLanguage enumeration.
    """

    def test_supported_language_values(self) -> None:
        """Test that SupportedLanguage has expected values.

        This test verifies that the SupportedLanguage enum contains
        all supported language codes.
        """
        assert SupportedLanguage.RU == "ru"
        assert SupportedLanguage.EN == "en"
        assert SupportedLanguage.UA == "ua"
        assert SupportedLanguage.BY == "by"

    def test_supported_language_count(self) -> None:
        """Test that SupportedLanguage has expected number of members.

        This test verifies that the SupportedLanguage enum has
        the expected number of language options.
        """
        assert len(SupportedLanguage) == 4
