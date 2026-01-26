"""Unit tests for ValidationService.

Tests birth date and life expectancy validation with various
valid and invalid inputs.
"""

from datetime import date

import pytest

from src.core.exceptions import ValidationError as CoreValidationError
from src.services.validation_service import (
    ERROR_DATE_IN_FUTURE,
    ERROR_DATE_TOO_OLD,
    ERROR_INVALID_DATE_FORMAT,
    ERROR_INVALID_NUMBER,
    ERROR_VALUE_TOO_HIGH,
    ERROR_VALUE_TOO_LOW,
    ValidationService,
)
from src.utils.config import MAX_LIFE_EXPECTANCY, MIN_BIRTH_YEAR, MIN_LIFE_EXPECTANCY


class TestValidateBirthDate:
    """Test suite for birth date validation."""

    @pytest.fixture
    def service(self) -> ValidationService:
        """Create ValidationService instance for testing.

        :returns: ValidationService instance
        :rtype: ValidationService
        """
        return ValidationService()

    def test_valid_date_format_dd_mm_yyyy(self, service: ValidationService) -> None:
        """Test validation accepts DD.MM.YYYY format.

        This test verifies that dates in DD.MM.YYYY format
        are correctly parsed and validated.
        """
        result = service.validate_birth_date(input_str="15.03.1990")
        assert result == date(1990, 3, 15)

    def test_valid_date_boundary_current_year(self, service: ValidationService) -> None:
        """Test validation accepts dates up to current date.

        This test verifies that today's date is accepted as valid.
        """
        today = date.today()
        date_str = today.strftime("%d.%m.%Y")
        result = service.validate_birth_date(input_str=date_str)
        assert result == today

    def test_invalid_date_format(self, service: ValidationService) -> None:
        """Test validation rejects invalid date formats.

        This test verifies that non-matching formats raise ValidationError
        with format error.
        """
        with pytest.raises(CoreValidationError) as exc_info:
            service.validate_birth_date(input_str="1990-03-15")
        assert exc_info.value.error_key == ERROR_INVALID_DATE_FORMAT

    def test_invalid_date_text(self, service: ValidationService) -> None:
        """Test validation rejects non-date text.

        This test verifies that arbitrary text raises ValidationError
        with format error.
        """
        with pytest.raises(CoreValidationError) as exc_info:
            service.validate_birth_date(input_str="not a date")
        assert exc_info.value.error_key == ERROR_INVALID_DATE_FORMAT

    def test_invalid_date_empty_string(self, service: ValidationService) -> None:
        """Test validation rejects empty string.

        This test verifies that empty input raises ValidationError
        with format error.
        """
        with pytest.raises(CoreValidationError) as exc_info:
            service.validate_birth_date(input_str="")
        assert exc_info.value.error_key == ERROR_INVALID_DATE_FORMAT

    def test_future_date_rejected(self, service: ValidationService) -> None:
        """Test validation rejects future dates.

        This test verifies that dates in the future raise ValidationError
        with future date error.
        """
        with pytest.raises(CoreValidationError) as exc_info:
            service.validate_birth_date(input_str="01.01.2099")
        assert exc_info.value.error_key == ERROR_DATE_IN_FUTURE

    def test_too_old_date_rejected(self, service: ValidationService) -> None:
        """Test validation rejects dates before MIN_BIRTH_YEAR.

        This test verifies that very old dates raise ValidationError
        with too old error.
        """
        old_date_str = "01.01.1800"
        with pytest.raises(CoreValidationError) as exc_info:
            service.validate_birth_date(input_str=old_date_str)
        assert exc_info.value.error_key == ERROR_DATE_TOO_OLD

    def test_boundary_min_birth_year(self, service: ValidationService) -> None:
        """Test validation accepts MIN_BIRTH_YEAR boundary.

        This test verifies that the minimum birth year is accepted.
        """
        date_str = f"01.01.{MIN_BIRTH_YEAR}"
        result = service.validate_birth_date(input_str=date_str)
        assert result == date(MIN_BIRTH_YEAR, 1, 1)


class TestValidateLifeExpectancy:
    """Test suite for ValidationService.validate_life_expectancy method.

    Tests life expectancy validation with various numeric inputs.
    """

    @pytest.fixture
    def service(self) -> ValidationService:
        """Create ValidationService instance for testing.

        :returns: ValidationService instance
        :rtype: ValidationService
        """
        return ValidationService()

    def test_valid_life_expectancy(self, service: ValidationService) -> None:
        """Test validation accepts valid life expectancy.

        This test verifies that a typical life expectancy value
        is correctly validated.
        """
        result = service.validate_life_expectancy(input_str="80")
        assert result == 80

    def test_valid_boundary_minimum(self, service: ValidationService) -> None:
        """Test validation accepts minimum boundary.

        This test verifies that MIN_LIFE_EXPECTANCY is accepted.
        """
        result = service.validate_life_expectancy(input_str=str(MIN_LIFE_EXPECTANCY))
        assert result == MIN_LIFE_EXPECTANCY

    def test_valid_boundary_maximum(self, service: ValidationService) -> None:
        """Test validation accepts maximum boundary.

        This test verifies that MAX_LIFE_EXPECTANCY is accepted.
        """
        result = service.validate_life_expectancy(input_str=str(MAX_LIFE_EXPECTANCY))
        assert result == MAX_LIFE_EXPECTANCY

    def test_too_low_rejected(self, service: ValidationService) -> None:
        """Test validation rejects values below minimum.

        This test verifies that values below MIN_LIFE_EXPECTANCY
        raise ValidationError with too low error.
        """
        too_low = MIN_LIFE_EXPECTANCY - 1
        with pytest.raises(CoreValidationError) as exc_info:
            service.validate_life_expectancy(input_str=str(too_low))
        assert exc_info.value.error_key == ERROR_VALUE_TOO_LOW

    def test_too_high_rejected(self, service: ValidationService) -> None:
        """Test validation rejects values above maximum.

        This test verifies that values above MAX_LIFE_EXPECTANCY
        raise ValidationError with too high error.
        """
        too_high = MAX_LIFE_EXPECTANCY + 1
        with pytest.raises(CoreValidationError) as exc_info:
            service.validate_life_expectancy(input_str=str(too_high))
        assert exc_info.value.error_key == ERROR_VALUE_TOO_HIGH

    def test_non_numeric_rejected(self, service: ValidationService) -> None:
        """Test validation rejects non-numeric input.

        This test verifies that non-numeric strings raise ValidationError
        with invalid number error.
        """
        with pytest.raises(CoreValidationError) as exc_info:
            service.validate_life_expectancy(input_str="abc")
        assert exc_info.value.error_key == ERROR_INVALID_NUMBER

    def test_float_rejected(self, service: ValidationService) -> None:
        """Test validation rejects floating point input.

        This test verifies that floats raise ValidationError
        with invalid number error.
        """
        with pytest.raises(CoreValidationError) as exc_info:
            service.validate_life_expectancy(input_str="80.5")
        assert exc_info.value.error_key == ERROR_INVALID_NUMBER

    def test_empty_string_rejected(self, service: ValidationService) -> None:
        """Test validation rejects empty string.

        This test verifies that empty input raise ValidationError
        with invalid number error.
        """
        with pytest.raises(CoreValidationError) as exc_info:
            service.validate_life_expectancy(input_str="")
        assert exc_info.value.error_key == ERROR_INVALID_NUMBER
