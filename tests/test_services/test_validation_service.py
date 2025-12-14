"""Unit tests for ValidationService.

Tests birth date and life expectancy validation with various
valid and invalid inputs.
"""

from datetime import date

import pytest

from src.services.validation_service import (
    ERROR_DATE_IN_FUTURE,
    ERROR_DATE_TOO_OLD,
    ERROR_INVALID_DATE_FORMAT,
    ERROR_INVALID_NUMBER,
    ERROR_VALUE_TOO_HIGH,
    ERROR_VALUE_TOO_LOW,
    ValidationResult,
    ValidationService,
)
from src.utils.config import MAX_LIFE_EXPECTANCY, MIN_BIRTH_YEAR, MIN_LIFE_EXPECTANCY


class TestValidationResult:
    """Test suite for ValidationResult dataclass.

    Tests the factory methods and properties of ValidationResult.
    """

    def test_success_creates_valid_result(self) -> None:
        """Test success factory method creates valid result.

        This test verifies that success() creates a ValidationResult
        with is_valid=True and the provided value.
        """
        result = ValidationResult.success(value=date(1990, 1, 1))
        assert result.is_valid is True
        assert result.value == date(1990, 1, 1)
        assert result.error_key is None

    def test_failure_creates_invalid_result(self) -> None:
        """Test failure factory method creates invalid result.

        This test verifies that failure() creates a ValidationResult
        with is_valid=False and the provided error_key.
        """
        result = ValidationResult.failure(error_key=ERROR_INVALID_DATE_FORMAT)
        assert result.is_valid is False
        assert result.value is None
        assert result.error_key == ERROR_INVALID_DATE_FORMAT


class TestValidateBirthDate:
    """Test suite for ValidationService.validate_birth_date method.

    Tests birth date validation with various input formats and values.
    """

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
        assert result.is_valid is True
        assert result.value == date(1990, 3, 15)

    def test_valid_date_boundary_current_year(self, service: ValidationService) -> None:
        """Test validation accepts dates up to current date.

        This test verifies that today's date is accepted as valid.
        """
        today = date.today()
        date_str = today.strftime("%d.%m.%Y")
        result = service.validate_birth_date(input_str=date_str)
        assert result.is_valid is True

    def test_invalid_date_format(self, service: ValidationService) -> None:
        """Test validation rejects invalid date formats.

        This test verifies that non-matching formats return
        an invalid result with format error.
        """
        result = service.validate_birth_date(input_str="1990-03-15")
        assert result.is_valid is False
        assert result.error_key == ERROR_INVALID_DATE_FORMAT

    def test_invalid_date_text(self, service: ValidationService) -> None:
        """Test validation rejects non-date text.

        This test verifies that arbitrary text returns
        an invalid result with format error.
        """
        result = service.validate_birth_date(input_str="not a date")
        assert result.is_valid is False
        assert result.error_key == ERROR_INVALID_DATE_FORMAT

    def test_invalid_date_empty_string(self, service: ValidationService) -> None:
        """Test validation rejects empty string.

        This test verifies that empty input returns
        an invalid result with format error.
        """
        result = service.validate_birth_date(input_str="")
        assert result.is_valid is False
        assert result.error_key == ERROR_INVALID_DATE_FORMAT

    def test_future_date_rejected(self, service: ValidationService) -> None:
        """Test validation rejects future dates.

        This test verifies that dates in the future return
        an invalid result with future date error.
        """
        result = service.validate_birth_date(input_str="01.01.2099")
        assert result.is_valid is False
        assert result.error_key == ERROR_DATE_IN_FUTURE

    def test_too_old_date_rejected(self, service: ValidationService) -> None:
        """Test validation rejects dates before MIN_BIRTH_YEAR.

        This test verifies that very old dates return
        an invalid result with too old error.
        """
        old_date_str = "01.01.1800"
        result = service.validate_birth_date(input_str=old_date_str)
        assert result.is_valid is False
        assert result.error_key == ERROR_DATE_TOO_OLD

    def test_boundary_min_birth_year(self, service: ValidationService) -> None:
        """Test validation accepts MIN_BIRTH_YEAR boundary.

        This test verifies that the minimum birth year is accepted.
        """
        date_str = f"01.01.{MIN_BIRTH_YEAR}"
        result = service.validate_birth_date(input_str=date_str)
        assert result.is_valid is True


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
        assert result.is_valid is True
        assert result.value == 80

    def test_valid_boundary_minimum(self, service: ValidationService) -> None:
        """Test validation accepts minimum boundary.

        This test verifies that MIN_LIFE_EXPECTANCY is accepted.
        """
        result = service.validate_life_expectancy(input_str=str(MIN_LIFE_EXPECTANCY))
        assert result.is_valid is True
        assert result.value == MIN_LIFE_EXPECTANCY

    def test_valid_boundary_maximum(self, service: ValidationService) -> None:
        """Test validation accepts maximum boundary.

        This test verifies that MAX_LIFE_EXPECTANCY is accepted.
        """
        result = service.validate_life_expectancy(input_str=str(MAX_LIFE_EXPECTANCY))
        assert result.is_valid is True
        assert result.value == MAX_LIFE_EXPECTANCY

    def test_too_low_rejected(self, service: ValidationService) -> None:
        """Test validation rejects values below minimum.

        This test verifies that values below MIN_LIFE_EXPECTANCY
        return an invalid result with too low error.
        """
        too_low = MIN_LIFE_EXPECTANCY - 1
        result = service.validate_life_expectancy(input_str=str(too_low))
        assert result.is_valid is False
        assert result.error_key == ERROR_VALUE_TOO_LOW

    def test_too_high_rejected(self, service: ValidationService) -> None:
        """Test validation rejects values above maximum.

        This test verifies that values above MAX_LIFE_EXPECTANCY
        return an invalid result with too high error.
        """
        too_high = MAX_LIFE_EXPECTANCY + 1
        result = service.validate_life_expectancy(input_str=str(too_high))
        assert result.is_valid is False
        assert result.error_key == ERROR_VALUE_TOO_HIGH

    def test_non_numeric_rejected(self, service: ValidationService) -> None:
        """Test validation rejects non-numeric input.

        This test verifies that non-numeric strings return
        an invalid result with invalid number error.
        """
        result = service.validate_life_expectancy(input_str="abc")
        assert result.is_valid is False
        assert result.error_key == ERROR_INVALID_NUMBER

    def test_float_rejected(self, service: ValidationService) -> None:
        """Test validation rejects floating point input.

        This test verifies that floats return an invalid
        result with invalid number error.
        """
        result = service.validate_life_expectancy(input_str="80.5")
        assert result.is_valid is False
        assert result.error_key == ERROR_INVALID_NUMBER

    def test_empty_string_rejected(self, service: ValidationService) -> None:
        """Test validation rejects empty string.

        This test verifies that empty input returns
        an invalid result with invalid number error.
        """
        result = service.validate_life_expectancy(input_str="")
        assert result.is_valid is False
        assert result.error_key == ERROR_INVALID_NUMBER
