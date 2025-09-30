"""Test module for base schema classes.

This module contains tests for the BaseSchema class and its configuration,
ensuring proper validation and serialization behavior.
"""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.database.schemas.base import BaseSchema


class MockSchema(BaseSchema):
    """Mock schema class for testing BaseSchema functionality."""

    name: str
    value: int
    timestamp: datetime


class TestBaseSchema:
    """Test class for BaseSchema functionality.

    This class contains all tests for the BaseSchema class,
    including configuration validation, serialization, and error handling.
    """

    def test_base_schema_creation_success(self):
        """Test successful creation of schema instance with valid data.

        This test verifies that a schema instance can be created
        with valid data and all fields are properly assigned.
        """
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        schema = MockSchema(name="test", value=42, timestamp=test_datetime)

        assert schema.name == "test"
        assert schema.value == 42
        assert schema.timestamp == test_datetime

    def test_base_schema_from_attributes_true(self):
        """Test schema creation from object attributes.

        This test verifies that the from_attributes=True configuration
        allows creating schema instances from objects with attributes.
        """

        class MockObject:
            def __init__(self):
                self.name = "mock"
                self.value = 100
                self.timestamp = datetime(2023, 1, 1)

        mock_obj = MockObject()
        schema = MockSchema.model_validate(mock_obj)

        assert schema.name == "mock"
        assert schema.value == 100
        assert schema.timestamp == datetime(2023, 1, 1)

    def test_base_schema_validate_assignment_true(self):
        """Test that assignment validation is enabled.

        This test verifies that the validate_assignment=True configuration
        validates data when fields are assigned after creation.
        """
        schema = MockSchema(name="test", value=42, timestamp=datetime(2023, 1, 1))

        # Valid assignment should work
        schema.value = 100
        assert schema.value == 100

        # Invalid assignment should raise ValidationError
        with pytest.raises(ValidationError):
            schema.value = "invalid"

    def test_base_schema_extra_forbid(self):
        """Test that extra fields are forbidden.

        This test verifies that the extra='forbid' configuration
        prevents creation of schema instances with extra fields.
        """
        with pytest.raises(ValidationError) as exc_info:
            MockSchema(
                name="test",
                value=42,
                timestamp=datetime(2023, 1, 1),
                extra_field="not allowed",
            )

        assert "extra_field" in str(exc_info.value)

    def test_base_schema_json_serialization(self):
        """Test complete JSON serialization and deserialization.

        This test verifies that schema instances can be properly
        serialized to JSON and deserialized back.
        """
        test_datetime = datetime(2023, 1, 1, 12, 30, 45)
        original_schema = MockSchema(name="test", value=42, timestamp=test_datetime)

        # Serialize to JSON
        json_str = original_schema.model_dump_json()
        json_data = json.loads(json_str)

        # Check that datetime is in ISO format
        assert json_data["timestamp"] == test_datetime.isoformat()

        # Deserialize back
        restored_schema = MockSchema.model_validate_json(json_str)
        assert restored_schema.name == original_schema.name
        assert restored_schema.value == original_schema.value
        assert restored_schema.timestamp == original_schema.timestamp

    def test_base_schema_validation_error_on_invalid_data(self):
        """Test that validation errors are raised for invalid data.

        This test verifies that the schema properly validates
        input data and raises appropriate errors for invalid values.
        """
        with pytest.raises(ValidationError):
            MockSchema(
                name=123, value=42, timestamp=datetime(2023, 1, 1)  # Should be string
            )

        with pytest.raises(ValidationError):
            MockSchema(
                name="test",
                value="not_a_number",  # Should be int
                timestamp=datetime(2023, 1, 1),
            )

    def test_base_schema_model_config_attributes(self):
        """Test that all expected model configuration attributes are set.

        This test verifies that the BaseSchema has all the expected
        configuration attributes with correct values.
        """
        config = BaseSchema.model_config

        assert config["from_attributes"] is True
        assert config["validate_assignment"] is True
        assert config["extra"] == "forbid"

    def test_base_schema_datetime_serializer(self):
        """Test that datetime fields are properly serialized with custom serializer.

        This test verifies that the custom datetime serializer properly
        handles datetime objects and converts them to ISO format in JSON mode.
        """
        test_datetime = datetime(2023, 1, 1, 12, 30, 45)
        schema = MockSchema(name="test", value=42, timestamp=test_datetime)

        # Test JSON serialization
        json_data = schema.model_dump(mode="json")
        assert json_data["timestamp"] == test_datetime.isoformat()

        # Test regular serialization (should preserve datetime object)
        regular_data = schema.model_dump()
        assert regular_data["timestamp"] == test_datetime
        assert isinstance(regular_data["timestamp"], datetime)

    def test_base_schema_inheritance(self):
        """Test that BaseSchema can be properly inherited.

        This test verifies that custom schemas can inherit from BaseSchema
        and maintain all the base configuration settings.
        """
        schema = MockSchema(
            name="inheritance_test", value=999, timestamp=datetime(2023, 12, 31)
        )

        # Should inherit all base configuration
        assert isinstance(schema, BaseSchema)
        assert schema.model_config["from_attributes"] is True
        assert schema.model_config["validate_assignment"] is True
        assert schema.model_config["extra"] == "forbid"

    def test_serialize_model_with_datetime_conversion(self):
        """Test serialize_model properly converts datetime objects to ISO format.

        :returns: None
        """

        # Create a test schema with datetime field
        class TestSchema(BaseSchema):
            name: str
            created_at: datetime
            updated_at: datetime

        # Create test instance
        now = datetime.now()
        schema = TestSchema(name="test", created_at=now, updated_at=now)

        # Test serialization with datetime conversion
        result = schema.serialize_model(
            serializer=lambda x: {
                "name": x.name,
                "created_at": x.created_at,
                "updated_at": x.updated_at,
            },
            info=None,
        )

        # Verify datetime conversion
        assert result["name"] == "test"
        assert result["created_at"] == now.isoformat()
        assert result["updated_at"] == now.isoformat()

    def test_serialize_model_without_datetime(self):
        """Test serialize_model with data that doesn't contain datetime objects.

        :returns: None
        """

        class TestSchema(BaseSchema):
            name: str
            value: int

        schema = TestSchema(name="test", value=42)

        # Test serialization without datetime
        result = schema.serialize_model(
            serializer=lambda x: {"name": x.name, "value": x.value}, info=None
        )

        # Verify no datetime conversion occurred
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_serialize_model_with_mixed_data_types(self):
        """Test serialize_model with mixed data types including datetime.

        :returns: None
        """

        class TestSchema(BaseSchema):
            name: str
            created_at: datetime
            value: int

        now = datetime.now()
        schema = TestSchema(name="test", created_at=now, value=42)

        # Test serialization with mixed types
        result = schema.serialize_model(
            serializer=lambda x: {
                "name": x.name,
                "created_at": x.created_at,
                "value": x.value,
            },
            info=None,
        )

        # Verify mixed data types
        assert result["name"] == "test"
        assert result["created_at"] == now.isoformat()
        assert result["value"] == 42

    def test_serialize_model_with_none_values(self):
        """Test serialize_model with None values.

        :returns: None
        """

        class TestSchema(BaseSchema):
            name: str
            optional_field: str | None = None

        schema = TestSchema(name="test")

        # Test serialization with None values
        result = schema.serialize_model(
            serializer=lambda x: {"name": x.name, "optional_field": x.optional_field},
            info=None,
        )

        # Verify None values are preserved
        assert result["name"] == "test"
        assert result["optional_field"] is None

    def test_serialize_model_with_nested_datetime(self):
        """Test serialize_model with nested datetime objects.

        :returns: None
        """

        class TestSchema(BaseSchema):
            name: str
            metadata: dict

        now = datetime.now()
        schema = TestSchema(
            name="test",
            metadata={"created_at": now, "updated_at": now, "info": "test info"},
        )

        # Test serialization with nested datetime
        result = schema.serialize_model(
            serializer=lambda x: {"name": x.name, "metadata": x.metadata}, info=None
        )

        # Verify nested datetime conversion
        assert result["name"] == "test"
        assert result["metadata"]["created_at"] == now
        assert result["metadata"]["updated_at"] == now
        assert result["metadata"]["info"] == "test info"

    def test_serialize_model_with_empty_dict(self):
        """Test serialize_model with empty dictionary result.

        :returns: None
        """

        class TestSchema(BaseSchema):
            name: str

        schema = TestSchema(name="test")

        # Test serialization with empty dict
        result = schema.serialize_model(serializer=lambda x: {}, info=None)

        # Verify empty dict is returned
        assert result == {}

    def test_serialize_model_with_non_dict_result(self):
        """Test serialize_model with non-dictionary result.

        :returns: None
        """

        class TestSchema(BaseSchema):
            name: str

        schema = TestSchema(name="test")

        # Test serialization with non-dict result
        result = schema.serialize_model(serializer=lambda x: "string result", info=None)

        # Verify non-dict result is returned as-is
        assert result == "string result"

    def test_serialize_model_with_complex_serializer(self):
        """Test serialize_model with complex serializer function.

        :returns: None
        """

        class TestSchema(BaseSchema):
            name: str
            created_at: datetime

        now = datetime.now()
        schema = TestSchema(name="test", created_at=now)

        # Test serialization with complex serializer
        result = schema.serialize_model(
            serializer=lambda x: {
                "data": {"user": {"name": x.name, "created_at": x.created_at}},
                "metadata": {"timestamp": now},
            },
            info=None,
        )

        # Verify structure is preserved and datetimes converted
        assert result["data"]["user"]["name"] == "test"
        assert result["data"]["user"]["created_at"] == now
        assert result["metadata"]["timestamp"] == now

    def test_serialize_model_with_info_parameter(self):
        """Test serialize_model with info parameter.

        :returns: None
        """

        class TestSchema(BaseSchema):
            name: str
            created_at: datetime

        # Create test instance
        now = datetime.now()
        schema = TestSchema(name="test", created_at=now)

        # Mock info parameter
        from unittest.mock import Mock

        mock_info = Mock()
        mock_info.mode = "json"

        # Test serialization with info parameter
        result = schema.serialize_model(
            serializer=lambda x: {"name": x.name, "created_at": x.created_at},
            info=mock_info,
        )

        # Verify info parameter is handled
        assert result["name"] == "test"
        assert result["created_at"] == now.isoformat()

    def test_base_schema_configuration(self):
        """Test BaseSchema configuration settings.

        :returns: None
        """
        # Test configuration is properly set
        config = BaseSchema.model_config

        assert config["from_attributes"] is True
        assert config["validate_assignment"] is True
        assert config["extra"] == "forbid"

    def test_base_schema_validation(self):
        """Test BaseSchema validation behavior.

        :returns: None
        """

        class TestSchema(BaseSchema):
            name: str
            value: int

        # Test valid data
        schema = TestSchema(name="test", value=42)
        assert schema.name == "test"
        assert schema.value == 42

        # Test validation error
        with pytest.raises(ValidationError):
            TestSchema(name="test", value="invalid")
