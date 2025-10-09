"""Base schemas for data validation.

This module provides base Pydantic models with common functionality
for all schemas in the application.
"""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, model_serializer


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM model parsing
        validate_assignment=True,  # Validate data on assignment
        extra="forbid",  # Forbid extra fields
    )

    @model_serializer(mode="wrap", when_used="json")
    def serialize_model(self, serializer: Any, info: Any) -> Dict[str, Any]:
        """Serialize model with custom datetime handling for JSON mode.

        This serializer wraps the default serialization and converts
        datetime objects to ISO format when serializing to JSON.

        :param serializer: The default serializer function
        :type serializer: Any
        :param info: Serialization context information
        :type info: Any
        :returns: Serialized model data with datetime objects as ISO strings
        :rtype: Dict[str, Any]
        """
        data = serializer(self)

        # Convert datetime objects to ISO format for JSON serialization
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()

        return data
