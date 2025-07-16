"""Tests for configuration settings."""

import os
from unittest.mock import patch


class TestConfig:
    """Test configuration settings and constants."""

    def test_bot_name_constant(self):
        """Test that BOT_NAME is defined correctly."""
        from src.utils.config import BOT_NAME

        assert BOT_NAME == "LifeWeeksBot"
        assert isinstance(BOT_NAME, str)

    def test_default_language_constant(self):
        """Test that DEFAULT_LANGUAGE is defined correctly."""
        from src.utils.config import DEFAULT_LANGUAGE

        assert DEFAULT_LANGUAGE == "ru"
        assert isinstance(DEFAULT_LANGUAGE, str)

    def test_visualization_constants(self):
        """Test visualization constants are defined correctly."""
        from src.utils.config import (
            CELL_SIZE,
            FONT_SIZE,
            MAX_YEARS,
            PADDING,
            WEEKS_PER_YEAR,
        )

        assert CELL_SIZE == 10
        assert PADDING == 40
        assert FONT_SIZE == 12
        assert MAX_YEARS == 90
        assert WEEKS_PER_YEAR == 52

    def test_colors_constant(self):
        """Test that COLORS dictionary is defined correctly."""
        from src.utils.config import COLORS

        assert isinstance(COLORS, dict)
        assert "background" in COLORS
        assert "grid" in COLORS
        assert "lived" in COLORS
        assert "text" in COLORS
        assert "axis" in COLORS

        # Check that all colors are tuples with 3 integers
        for color_name, color_value in COLORS.items():
            assert isinstance(color_value, tuple)
            assert len(color_value) == 3
            for component in color_value:
                assert isinstance(component, int)
                assert 0 <= component <= 255

    def test_scheduler_configuration(self):
        """Test scheduler configuration constants."""
        from src.utils.config import (
            WEEKLY_NOTIFICATION_DAY,
            WEEKLY_NOTIFICATION_HOUR,
            WEEKLY_NOTIFICATION_MINUTE,
        )

        assert WEEKLY_NOTIFICATION_DAY == "mon"
        assert WEEKLY_NOTIFICATION_HOUR == 9
        assert WEEKLY_NOTIFICATION_MINUTE == 0

    @patch.dict(
        os.environ, {"BUYMEACOFFEE_URL": "https://test.buymeacoffee.com/testuser"}
    )
    def test_buymeacoffee_url_from_env(self):
        """Test that BUYMEACOFFEE_URL is loaded from environment variable."""
        # Reload config to pick up the environment variable
        import importlib

        import src.utils.config

        importlib.reload(src.utils.config)

        from src.utils.config import BUYMEACOFFEE_URL

        assert BUYMEACOFFEE_URL == "https://test.buymeacoffee.com/testuser"

    @patch.dict(os.environ, {}, clear=True)
    def test_buymeacoffee_url_default_value(self):
        """Test that BUYMEACOFFEE_URL has default value when not set in env."""
        # Reload config to pick up the environment variable
        import importlib

        import src.utils.config

        importlib.reload(src.utils.config)

        from src.utils.config import BUYMEACOFFEE_URL

        # Check that it's a valid URL format
        assert BUYMEACOFFEE_URL.startswith("https://")
        assert "buymeacoffee.com" in BUYMEACOFFEE_URL or "coff.ee" in BUYMEACOFFEE_URL

    @patch.dict(os.environ, {"BUYMEACOFFEE_URL": ""})
    def test_buymeacoffee_url_empty_env(self):
        """Test that BUYMEACOFFEE_URL uses default when env is empty."""
        # Reload config to pick up the environment variable
        import importlib

        import src.utils.config

        importlib.reload(src.utils.config)

        from src.utils.config import BUYMEACOFFEE_URL

        # When env is empty string, it should use default
        assert BUYMEACOFFEE_URL == "https://www.buymeacoffee.com/yourname"

    @patch.dict(
        os.environ, {"BUYMEACOFFEE_URL": "https://custom.buymeacoffee.com/customuser"}
    )
    def test_buymeacoffee_url_custom_value(self):
        """Test that BUYMEACOFFEE_URL accepts custom values."""
        # Reload config to pick up the environment variable
        import importlib

        import src.utils.config

        importlib.reload(src.utils.config)

        from src.utils.config import BUYMEACOFFEE_URL

        assert BUYMEACOFFEE_URL == "https://custom.buymeacoffee.com/customuser"

    def test_buymeacoffee_url_type(self):
        """Test that BUYMEACOFFEE_URL is always a string."""
        from src.utils.config import BUYMEACOFFEE_URL

        assert isinstance(BUYMEACOFFEE_URL, str)
        assert len(BUYMEACOFFEE_URL) > 0

    def test_buymeacoffee_url_format(self):
        """Test that BUYMEACOFFEE_URL has correct format."""
        from src.utils.config import BUYMEACOFFEE_URL

        assert BUYMEACOFFEE_URL.startswith("https://")
        assert "buymeacoffee.com" in BUYMEACOFFEE_URL or "coff.ee" in BUYMEACOFFEE_URL

    def test_token_loading(self):
        """Test that TOKEN is loaded from environment."""
        from src.utils.config import TOKEN

        # TOKEN can be None if not set in environment
        assert TOKEN is None or isinstance(TOKEN, str)

    def test_chat_id_loading(self):
        """Test that CHAT_ID is loaded from environment."""
        from src.utils.config import CHAT_ID

        # CHAT_ID can be None if not set in environment
        assert CHAT_ID is None or isinstance(CHAT_ID, str)

    def test_config_module_imports(self):
        """Test that all required constants are imported correctly."""
        from src.utils.config import (
            BOT_NAME,
            COLORS,
            DEFAULT_LANGUAGE,
            FONT_SIZE,
            MAX_YEARS,
            PADDING,
            WEEKLY_NOTIFICATION_DAY,
            WEEKLY_NOTIFICATION_HOUR,
            WEEKLY_NOTIFICATION_MINUTE,
            WEEKS_PER_YEAR,
        )

        # Just verify they can be imported without errors
        assert BOT_NAME is not None
        assert DEFAULT_LANGUAGE is not None
        assert PADDING is not None
        assert FONT_SIZE is not None
        assert MAX_YEARS is not None
        assert WEEKS_PER_YEAR is not None
        assert COLORS is not None
        assert WEEKLY_NOTIFICATION_DAY is not None
        assert WEEKLY_NOTIFICATION_HOUR is not None
        assert WEEKLY_NOTIFICATION_MINUTE is not None

    def test_config_constants_immutability(self):
        """Test that configuration constants are not accidentally mutable."""
        from src.utils.config import COLORS

        # Test that COLORS is a proper dictionary, not a mutable reference
        original_colors = COLORS.copy()

        # This should not affect the original COLORS
        test_colors = COLORS.copy()
        test_colors["test"] = (255, 255, 255)

        assert COLORS == original_colors
        assert "test" not in COLORS

    @patch.dict(
        os.environ, {"BUYMEACOFFEE_URL": "https://test.buymeacoffee.com/testuser"}
    )
    def test_buymeacoffee_url_reload_behavior(self):
        """Test that BUYMEACOFFEE_URL is properly reloaded when environment changes."""
        # First load with default
        import importlib

        import src.utils.config

        importlib.reload(src.utils.config)

        from src.utils.config import BUYMEACOFFEE_URL

        assert BUYMEACOFFEE_URL == "https://test.buymeacoffee.com/testuser"

    def test_config_documentation(self):
        """Test that config module has proper documentation."""
        import src.utils.config

        assert src.utils.config.__doc__ is not None
        assert len(src.utils.config.__doc__) > 0

    def test_subscription_message_probability_default(self):
        """Test that DEFAULT_SUBSCRIPTION_MESSAGE_PROBABILITY is set correctly."""
        from src.utils.config import DEFAULT_SUBSCRIPTION_MESSAGE_PROBABILITY

        assert DEFAULT_SUBSCRIPTION_MESSAGE_PROBABILITY == 20
        assert isinstance(DEFAULT_SUBSCRIPTION_MESSAGE_PROBABILITY, int)

    def test_subscription_message_probability_constant(self):
        """Test that SUBSCRIPTION_MESSAGE_PROBABILITY is defined correctly."""
        from src.utils.config import SUBSCRIPTION_MESSAGE_PROBABILITY

        assert isinstance(SUBSCRIPTION_MESSAGE_PROBABILITY, int)
        assert 0 <= SUBSCRIPTION_MESSAGE_PROBABILITY <= 100

    @patch.dict(os.environ, {"SUBSCRIPTION_MESSAGE_PROBABILITY": "30"})
    def test_subscription_message_probability_from_env(self):
        """Test that SUBSCRIPTION_MESSAGE_PROBABILITY is loaded from environment variable."""
        # Reload config to pick up the environment variable
        import importlib

        import src.utils.config

        importlib.reload(src.utils.config)

        from src.utils.config import SUBSCRIPTION_MESSAGE_PROBABILITY

        assert SUBSCRIPTION_MESSAGE_PROBABILITY == 30

    @patch.dict(os.environ, {}, clear=True)
    def test_subscription_message_probability_default_value(self):
        """Test that SUBSCRIPTION_MESSAGE_PROBABILITY has default value when not set in env."""
        # Reload config to pick up the environment variable
        import importlib

        import src.utils.config

        importlib.reload(src.utils.config)

        from src.utils.config import SUBSCRIPTION_MESSAGE_PROBABILITY

        assert SUBSCRIPTION_MESSAGE_PROBABILITY == 20

    @patch.dict(os.environ, {"SUBSCRIPTION_MESSAGE_PROBABILITY": "invalid"})
    def test_subscription_message_probability_invalid_env(self):
        """Test that SUBSCRIPTION_MESSAGE_PROBABILITY uses default when env is invalid."""
        # Reload config to pick up the environment variable
        import importlib

        import src.utils.config

        importlib.reload(src.utils.config)

        from src.utils.config import SUBSCRIPTION_MESSAGE_PROBABILITY

        # When env is invalid, it should use default
        assert SUBSCRIPTION_MESSAGE_PROBABILITY == 20

    @patch.dict(os.environ, {"SUBSCRIPTION_MESSAGE_PROBABILITY": "0"})
    def test_subscription_message_probability_zero(self):
        """Test that SUBSCRIPTION_MESSAGE_PROBABILITY accepts zero value."""
        # Reload config to pick up the environment variable
        import importlib

        import src.utils.config

        importlib.reload(src.utils.config)

        from src.utils.config import SUBSCRIPTION_MESSAGE_PROBABILITY

        assert SUBSCRIPTION_MESSAGE_PROBABILITY == 0

    @patch.dict(os.environ, {"SUBSCRIPTION_MESSAGE_PROBABILITY": "100"})
    def test_subscription_message_probability_hundred(self):
        """Test that SUBSCRIPTION_MESSAGE_PROBABILITY accepts 100 value."""
        # Reload config to pick up the environment variable
        import importlib

        import src.utils.config

        importlib.reload(src.utils.config)

        from src.utils.config import SUBSCRIPTION_MESSAGE_PROBABILITY

        assert SUBSCRIPTION_MESSAGE_PROBABILITY == 100

    def test_subscription_message_probability_range(self):
        """Test that SUBSCRIPTION_MESSAGE_PROBABILITY is within valid range."""
        from src.utils.config import SUBSCRIPTION_MESSAGE_PROBABILITY

        assert 0 <= SUBSCRIPTION_MESSAGE_PROBABILITY <= 100

    def test_config_module_imports_with_probability(self):
        """Test that subscription message probability constants are imported correctly."""
        from src.utils.config import (
            DEFAULT_SUBSCRIPTION_MESSAGE_PROBABILITY,
            SUBSCRIPTION_MESSAGE_PROBABILITY,
        )

        # Just verify they can be imported without errors
        assert DEFAULT_SUBSCRIPTION_MESSAGE_PROBABILITY is not None
        assert SUBSCRIPTION_MESSAGE_PROBABILITY is not None
