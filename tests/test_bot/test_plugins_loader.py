"""Unit tests for PluginLoader.

Tests plugin discovery, configuration loading, and error handling.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from src.bot.plugins.loader import (
    DEFAULT_CONFIG_PATH,
    HandlerConfig,
    PluginLoader,
    PluginLoadError,
    create_default_loader,
)


class TestPluginLoader:
    """Test suite for PluginLoader class."""

    @pytest.fixture
    def mock_config_path(self, tmp_path):
        """Create a temporary config file.

        :param tmp_path: Pytest temporary directory fixture
        :returns: Path to temporary config file
        """
        config_file = tmp_path / "handlers.yaml"
        return config_file

    def test_init_defaults(self):
        """Test initialization with default path."""
        loader = PluginLoader()
        assert loader._config_path == DEFAULT_CONFIG_PATH
        assert loader._loaded_handlers == {}

    def test_init_custom_path(self):
        """Test initialization with custom path."""
        path = Path("/custom/path.yaml")
        loader = PluginLoader(config_path=path)
        assert loader._config_path == path

    def test_discover_from_yaml_file_not_found(self, mock_config_path):
        """Test discovery when file does not exist."""
        loader = PluginLoader(config_path=mock_config_path)
        configs = loader.discover_handlers()
        assert configs == []

    def test_discover_from_yaml_empty_file(self, mock_config_path):
        """Test discovery from empty file."""
        mock_config_path.touch()
        loader = PluginLoader(config_path=mock_config_path)
        configs = loader.discover_handlers()
        assert configs == []

    def test_discover_from_yaml_valid(self, mock_config_path):
        """Test valid configuration discovery."""
        data = {
            "handlers": [
                {
                    "module": "src.bot.handlers.test",
                    "class": "TestHandler",
                    "command": "test",
                    "callbacks": [{"name": "cb", "method": "on_cb"}],
                    "text_input": "handle_text",
                    "waiting_states": ["waiting"],
                }
            ]
        }
        mock_config_path.write_text(yaml.dump(data), encoding="utf-8")

        loader = PluginLoader(config_path=mock_config_path)
        configs = loader.discover_handlers()

        assert len(configs) == 1
        config = configs[0]
        assert config.module == "src.bot.handlers.test"
        assert config.class_name == "TestHandler"
        assert config.command == "test"
        assert len(config.callbacks) == 1
        assert config.text_input == "handle_text"
        assert config.waiting_states == ["waiting"]

    def test_discover_from_yaml_invalid_format(self, mock_config_path):
        """Test handling of invalid YAML."""
        mock_config_path.write_text("invalid: yaml: content: [", encoding="utf-8")
        loader = PluginLoader(config_path=mock_config_path)
        configs = loader.discover_handlers()
        assert configs == []

    def test_load_handler_class_success(self):
        """Test successful handler class loading."""
        loader = PluginLoader()
        config = HandlerConfig(
            module="unittest.mock", class_name="MagicMock", command="mock"
        )

        handler_class = loader.load_handler_class(config)
        assert handler_class == MagicMock

        # Verify caching
        assert loader._loaded_handlers["mock"] == MagicMock
        assert loader.get_loaded_handler("mock") == MagicMock

    def test_load_handler_class_import_error(self):
        """Test loading handler from non-existent module."""
        loader = PluginLoader()
        config = HandlerConfig(
            module="non.existent.module", class_name="TestHandler", command="fail"
        )

        with pytest.raises(PluginLoadError) as exc:
            loader.load_handler_class(config)
        assert "Could not import module" in str(exc.value)

    def test_load_handler_class_attribute_error(self):
        """Test loading non-existent class from valid module."""
        loader = PluginLoader()
        config = HandlerConfig(
            module="unittest.mock", class_name="NonExistentClass", command="fail"
        )

        with pytest.raises(PluginLoadError) as exc:
            loader.load_handler_class(config)
        assert "Class 'NonExistentClass' not found" in str(exc.value)

    def test_get_handler_configs_copy(self):
        """Test get_handler_configs returns independent copy."""
        loader = PluginLoader()
        # access private attribute to seed data
        config = HandlerConfig("mod", "cls", "cmd")
        loader._handler_configs = [config]

        configs = loader.get_handler_configs()
        configs.append("fake")

        assert len(loader._handler_configs) == 1
        assert "fake" not in loader._handler_configs

    def test_create_default_loader(self):
        """Test create_default_loader factory."""
        loader = create_default_loader()
        assert isinstance(loader, PluginLoader)
        assert loader._config_path == DEFAULT_CONFIG_PATH
