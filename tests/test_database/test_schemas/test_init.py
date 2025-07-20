"""Test module for schemas package initialization.

This module contains tests for the schemas package __init__.py file,
ensuring all imports and exports work correctly.
"""

# Import the schemas package to test the __init__.py
import src.database.schemas as schemas


class TestSchemasPackageInit:
    """Test class for schemas package initialization.

    This class contains all tests for the schemas package __init__.py file,
    testing imports and exports.
    """

    def test_schemas_package_imports(self):
        """Test that all schemas can be imported from the package.

        This test verifies that all schema classes can be imported
        from the schemas package __init__.py file.
        """
        # Test BaseSchema import
        assert hasattr(schemas, "BaseSchema")
        from src.database.schemas.base import BaseSchema

        assert schemas.BaseSchema is BaseSchema

        # Test User schema imports
        assert hasattr(schemas, "UserBase")
        assert hasattr(schemas, "UserCreate")
        assert hasattr(schemas, "UserUpdate")
        assert hasattr(schemas, "UserInDB")
        assert hasattr(schemas, "UserResponse")

        from src.database.schemas.user import (
            UserBase,
            UserCreate,
            UserInDB,
            UserResponse,
            UserUpdate,
        )

        assert schemas.UserBase is UserBase
        assert schemas.UserCreate is UserCreate
        assert schemas.UserUpdate is UserUpdate
        assert schemas.UserInDB is UserInDB
        assert schemas.UserResponse is UserResponse

        # Test UserSettings schema imports
        assert hasattr(schemas, "UserSettingsBase")
        assert hasattr(schemas, "UserSettingsCreate")
        assert hasattr(schemas, "UserSettingsUpdate")
        assert hasattr(schemas, "UserSettingsInDB")
        assert hasattr(schemas, "UserSettingsResponse")

        from src.database.schemas.user_settings import (
            UserSettingsBase,
            UserSettingsCreate,
            UserSettingsInDB,
            UserSettingsResponse,
            UserSettingsUpdate,
        )

        assert schemas.UserSettingsBase is UserSettingsBase
        assert schemas.UserSettingsCreate is UserSettingsCreate
        assert schemas.UserSettingsUpdate is UserSettingsUpdate
        assert schemas.UserSettingsInDB is UserSettingsInDB
        assert schemas.UserSettingsResponse is UserSettingsResponse

        # Test UserSubscription schema imports
        assert hasattr(schemas, "UserSubscriptionBase")
        assert hasattr(schemas, "UserSubscriptionCreate")
        assert hasattr(schemas, "UserSubscriptionUpdate")
        assert hasattr(schemas, "UserSubscriptionInDB")
        assert hasattr(schemas, "UserSubscriptionResponse")

        from src.database.schemas.user_subscription import (
            UserSubscriptionBase,
            UserSubscriptionCreate,
            UserSubscriptionInDB,
            UserSubscriptionResponse,
            UserSubscriptionUpdate,
        )

        assert schemas.UserSubscriptionBase is UserSubscriptionBase
        assert schemas.UserSubscriptionCreate is UserSubscriptionCreate
        assert schemas.UserSubscriptionUpdate is UserSubscriptionUpdate
        assert schemas.UserSubscriptionInDB is UserSubscriptionInDB
        assert schemas.UserSubscriptionResponse is UserSubscriptionResponse

    def test_schemas_package_all_export(self):
        """Test that __all__ export list contains all expected items.

        This test verifies that the __all__ list in __init__.py
        contains all the expected schema class names.
        """
        expected_exports = [
            # Base
            "BaseSchema",
            # User
            "UserBase",
            "UserCreate",
            "UserUpdate",
            "UserInDB",
            "UserResponse",
            # User Settings
            "UserSettingsBase",
            "UserSettingsCreate",
            "UserSettingsUpdate",
            "UserSettingsInDB",
            "UserSettingsResponse",
            # User Subscription
            "UserSubscriptionBase",
            "UserSubscriptionCreate",
            "UserSubscriptionUpdate",
            "UserSubscriptionInDB",
            "UserSubscriptionResponse",
        ]

        # Check that __all__ exists
        assert hasattr(schemas, "__all__")
        actual_exports = schemas.__all__

        # Check that all expected exports are in __all__
        for expected_export in expected_exports:
            assert (
                expected_export in actual_exports
            ), f"{expected_export} not found in __all__"

        # Check that we have the correct number of exports
        assert len(actual_exports) == len(expected_exports)

    def test_schemas_can_instantiate_classes(self):
        """Test that schema classes can be instantiated from package imports.

        This test verifies that schema classes imported from the package
        can be properly instantiated and used.
        """
        from datetime import datetime

        # Test UserBase instantiation
        user_base = schemas.UserBase(telegram_id=123456789)
        assert user_base.telegram_id == 123456789

        # Test UserSettingsBase instantiation
        user_settings = schemas.UserSettingsBase(telegram_id=123456789)
        assert user_settings.telegram_id == 123456789
        assert user_settings.notifications is True

        # Test UserSubscriptionBase instantiation
        user_subscription = schemas.UserSubscriptionBase(telegram_id=123456789)
        assert user_subscription.telegram_id == 123456789
        assert user_subscription.is_active is True

        # Test UserInDB instantiation
        user_in_db = schemas.UserInDB(
            telegram_id=123456789,
            created_at=datetime(2023, 1, 1),
        )
        assert user_in_db.telegram_id == 123456789
        assert user_in_db.created_at == datetime(2023, 1, 1)

        # Test UserSettingsInDB instantiation
        settings_in_db = schemas.UserSettingsInDB(
            id=1,
            telegram_id=123456789,
            updated_at=datetime(2023, 1, 1),
        )
        assert settings_in_db.id == 1
        assert settings_in_db.telegram_id == 123456789
        assert settings_in_db.updated_at == datetime(2023, 1, 1)

        # Test UserSubscriptionInDB instantiation
        subscription_in_db = schemas.UserSubscriptionInDB(
            id=1,
            telegram_id=123456789,
            created_at=datetime(2023, 1, 1),
        )
        assert subscription_in_db.id == 1
        assert subscription_in_db.telegram_id == 123456789
        assert subscription_in_db.created_at == datetime(2023, 1, 1)

    def test_schemas_package_no_extra_exports(self):
        """Test that the package doesn't export unexpected items.

        This test verifies that the package only exports the items
        listed in __all__ and doesn't have unexpected public exports.
        """
        # Get all public attributes (not starting with _)
        public_attrs = [attr for attr in dir(schemas) if not attr.startswith("_")]

        # Filter out the expected exports and module names
        expected_exports = schemas.__all__
        module_names = ["base", "user", "user_settings", "user_subscription"]
        expected_all = expected_exports + module_names
        unexpected_exports = [attr for attr in public_attrs if attr not in expected_all]

        # Should not have any unexpected exports
        assert (
            len(unexpected_exports) == 0
        ), f"Unexpected exports found: {unexpected_exports}"

    def test_schemas_package_module_docstring(self):
        """Test that the schemas package has proper documentation.

        This test verifies that the schemas package __init__.py
        has a proper module-level docstring.
        """
        # Check that the module has a docstring
        assert schemas.__doc__ is not None
        assert len(schemas.__doc__.strip()) > 0

        # Check that docstring contains expected content
        docstring = schemas.__doc__.lower()
        assert "schemas" in docstring
        assert "data validation" in docstring or "validation" in docstring
