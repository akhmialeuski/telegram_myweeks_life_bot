"""Base schemas for data validation.

This module provides base Pydantic models with common functionality
for all schemas in the application.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM model parsing
        validate_assignment=True,  # Validate data on assignment
        extra="forbid",  # Forbid extra fields
        json_encoders={
            datetime: lambda v: v.isoformat(),  # ISO format for datetime
        },
    )
