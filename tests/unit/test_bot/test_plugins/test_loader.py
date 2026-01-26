"""Tests for plugin loader module.

This module contains unit tests for the PluginLoader class
that discovers and loads handler plugins from YAML configuration.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.bot.plugins.loader import (
    HandlerConfig,
    PluginLoader,
    PluginLoadError,
    create_default_loader,
)


class TestPluginLoader:
    """Test class for PluginLoader.

    This class contains all tests for the PluginLoader class,
    including handler discovery, loading, and caching.
    """

    @pytest.fixture
    def temp_config_path(self, tmp_path: Path) -> Path:
        """Create temporary config file path."""
        return tmp_path / "handlers.yaml"

    @pytest.fixture
    def loader(self, temp_config_path: Path) -> PluginLoader:
        """Create PluginLoader with temporary config path."""
        return PluginLoader(config_path=temp_config_path)

    def test_init_with_default_path(self) -> None:
        """Test initialization with default config path.

        This test verifies that PluginLoader uses default
        configuration path when none is provided.
        """
        loader = PluginLoader()
        assert loader._config_path is not None
        assert "handlers.yaml" in str(loader._config_path)

    def test_init_with_custom_path(self, temp_config_path: Path) -> None:
        """Test initialization with custom config path.

        This test verifies that PluginLoader uses the provided
        custom configuration path.
        """
        loader = PluginLoader(config_path=temp_config_path)
        assert loader._config_path == temp_config_path

    def test_discover_handlers_file_not_found(
        self, loader: PluginLoader, temp_config_path: Path
    ) -> None:
        """Test discover_handlers when config file doesn't exist.

        This test verifies that empty list is returned when
        configuration file is not found.
        """
        configs = loader.discover_handlers()
        assert configs == []

    def test_discover_handlers_empty_file(
        self, loader: PluginLoader, temp_config_path: Path
    ) -> None:
        """Test discover_handlers with empty config file.

        This test verifies that empty list is returned when
        configuration file is empty or has no handlers.
        """
        temp_config_path.write_text("")
        configs = loader.discover_handlers()
        assert configs == []

    def test_discover_handlers_no_handlers_key(
        self, loader: PluginLoader, temp_config_path: Path
    ) -> None:
        """Test discover_handlers when handlers key is missing.

        This test verifies that empty list is returned when
        configuration file doesn't contain 'handlers' key.
        """
        temp_config_path.write_text("other_key: value")
        configs = loader.discover_handlers()
        assert configs == []

    def test_discover_handlers_success(
        self, loader: PluginLoader, temp_config_path: Path
    ) -> None:
        """Test successful handler discovery.

        This test verifies that handlers are correctly discovered
        from valid YAML configuration.
        """
        config_content = """
handlers:
  - module: src.bot.handlers.start_handler
    class: StartHandler
    command: start
    callbacks:
      - pattern: "^start_"
        method: handle_callback
    text_input: handle_input
    waiting_states:
      - awaiting_birth_date
"""
        temp_config_path.write_text(config_content)

        configs = loader.discover_handlers()

        assert len(configs) == 1
        assert configs[0].module == "src.bot.handlers.start_handler"
        assert configs[0].class_name == "StartHandler"
        assert configs[0].command == "start"
        assert configs[0].text_input == "handle_input"
        assert "awaiting_birth_date" in configs[0].waiting_states

    def test_load_handler_class_cache_hit(self, loader: PluginLoader) -> None:
        """Test load_handler_class returns cached handler.

        This test verifies that loading a handler class returns
        the cached instance on subsequent calls.
        """
        config = HandlerConfig(
            module="src.bot.handlers.start_handler",
            class_name="StartHandler",
            command="start",
        )

        # Pre-populate cache
        mock_class = MagicMock()
        loader._loaded_handlers["start"] = mock_class

        # Load should return cached version
        result = loader.load_handler_class(config=config)

        assert result is mock_class

    def test_load_handler_class_success(self, loader: PluginLoader) -> None:
        """Test successful handler class loading.

        This test verifies that handler class is loaded correctly
        from its module.
        """
        config = HandlerConfig(
            module="src.bot.handlers.start_handler",
            class_name="StartHandler",
            command="start",
        )

        handler_class = loader.load_handler_class(config=config)

        assert handler_class is not None
        assert handler_class.__name__ == "StartHandler"

    def test_load_handler_class_import_error(self, loader: PluginLoader) -> None:
        """Test load_handler_class with import error.

        This test verifies that PluginLoadError is raised when
        module cannot be imported.
        """
        config = HandlerConfig(
            module="nonexistent.module",
            class_name="SomeHandler",
            command="test",
        )

        with pytest.raises(PluginLoadError) as exc_info:
            loader.load_handler_class(config=config)

        assert "nonexistent.module" in str(exc_info.value)

    def test_load_handler_class_attribute_error(self, loader: PluginLoader) -> None:
        """Test load_handler_class with attribute error.

        This test verifies that PluginLoadError is raised when
        class is not found in the module.
        """
        config = HandlerConfig(
            module="src.bot.handlers.start_handler",
            class_name="NonExistentHandler",
            command="test",
        )

        with pytest.raises(PluginLoadError) as exc_info:
            loader.load_handler_class(config=config)

        assert "NonExistentHandler" in str(exc_info.value)

    def test_get_handler_configs_returns_copy(
        self, loader: PluginLoader, temp_config_path: Path
    ) -> None:
        """Test get_handler_configs returns a copy.

        This test verifies that the method returns a copy
        of internal handler configs list.
        """
        config_content = """
handlers:
  - module: src.bot.handlers.help_handler
    class: HelpHandler
    command: help
"""
        temp_config_path.write_text(config_content)
        loader.discover_handlers()

        configs1 = loader.get_handler_configs()
        configs2 = loader.get_handler_configs()

        assert configs1 is not configs2
        assert len(configs1) == len(configs2)

    def test_get_loaded_handler_found(self, loader: PluginLoader) -> None:
        """Test get_loaded_handler when handler exists.

        This test verifies that loaded handler is returned
        when it exists in cache.
        """
        mock_class = MagicMock()
        loader._loaded_handlers["test"] = mock_class

        result = loader.get_loaded_handler(command="test")

        assert result is mock_class

    def test_get_loaded_handler_not_found(self, loader: PluginLoader) -> None:
        """Test get_loaded_handler when handler doesn't exist.

        This test verifies that None is returned when handler
        is not found in cache.
        """
        result = loader.get_loaded_handler(command="nonexistent")

        assert result is None


class TestPluginLoadError:
    """Test class for PluginLoadError exception."""

    def test_exception_message(self) -> None:
        """Test exception message formatting.

        This test verifies that exception message is formatted
        correctly with plugin name and reason.
        """
        error = PluginLoadError(
            plugin_name="test_plugin",
            reason="Module not found",
        )

        assert "test_plugin" in str(error)
        assert "Module not found" in str(error)
        assert error.plugin_name == "test_plugin"
        assert error.reason == "Module not found"


class TestCreateDefaultLoader:
    """Test class for create_default_loader function."""

    def test_creates_plugin_loader(self) -> None:
        """Test that function creates PluginLoader instance.

        This test verifies that create_default_loader returns
        a properly configured PluginLoader instance.
        """
        loader = create_default_loader()

        assert isinstance(loader, PluginLoader)
