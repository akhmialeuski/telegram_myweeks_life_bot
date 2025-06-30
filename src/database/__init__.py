"""Database package for LifeWeeksBot.

This package provides data models and database abstraction layer
for storing user profiles and settings using SQLAlchemy 2.0.
"""

from .models import Base, User, UserSettings
from .abstract_repository import AbstractUserRepository
from .sqlite_repository import SQLAlchemyUserRepository
from .constants import DEFAULT_DATABASE_PATH

__all__ = [
    'Base',
    'User',
    'UserSettings',
    'AbstractUserRepository',
    'SQLAlchemyUserRepository',
    'DEFAULT_DATABASE_PATH'
]
