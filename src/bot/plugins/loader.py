"""Plugin loader for handler discovery via YAML configuration.

This module provides the PluginLoader class that discovers handlers using
YAML configuration as the source of truth. Entry points are not used for
configuration since metadata (callbacks, text_input, waiting_states) cannot
be stored in entry point declarations.
"""

import importlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Default configuration file path
DEFAULT_CONFIG_PATH = (
    Path(__file__).parent.parent.parent.parent / "config" / "handlers.yaml"
)


@dataclass
class HandlerConfig:
    """Configuration for a single handler.

    :ivar module: Module path containing the handler class
    :type module: str
    :ivar class_name: Name of the handler class
    :type class_name: str
    :ivar command: Command name (without leading slash)
    :type command: str
    :ivar callbacks: List of callback configurations
    :type callbacks: list[dict[str, str]]
    :ivar text_input: Method name for text input handling
    :type text_input: str | None
    :ivar waiting_states: List of waiting state identifiers
    :type waiting_states: list[str]
    """

    module: str
    class_name: str
    command: str
    callbacks: list[dict[str, str]] = field(default_factory=list)
    text_input: str | None = None
    waiting_states: list[str] = field(default_factory=list)


class PluginLoadError(Exception):
    """Exception raised when a plugin fails to load.

    :ivar plugin_name: Name of the plugin that failed to load
    :type plugin_name: str
    :ivar reason: Reason for the failure
    :type reason: str
    """

    def __init__(self, plugin_name: str, reason: str) -> None:
        """Initialize the exception.

        :param plugin_name: Name of the plugin that failed
        :type plugin_name: str
        :param reason: Reason for the failure
        :type reason: str
        """
        self.plugin_name = plugin_name
        self.reason = reason
        super().__init__(f"Failed to load plugin '{plugin_name}': {reason}")


class PluginLoader:
    """Loader for discovering and loading handler plugins.

    The loader reads handler configuration from YAML file which is the
    single source of truth for handler metadata (callbacks, text_input,
    waiting_states). This ensures consistent behavior in both development
    and installed environments.

    :ivar _config_path: Path to the YAML configuration file
    :type _config_path: Path
    :ivar _loaded_handlers: Cache of loaded handler classes
    :type _loaded_handlers: dict[str, type]
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the plugin loader.

        :param config_path: Optional path to YAML configuration file
        :type config_path: Path | None
        """
        self._config_path = config_path or DEFAULT_CONFIG_PATH
        self._loaded_handlers: dict[str, type] = {}
        self._handler_configs: list[HandlerConfig] = []

    def discover_handlers(self) -> list[HandlerConfig]:
        """Discover all available handlers from YAML configuration.

        :returns: List of handler configurations
        :rtype: list[HandlerConfig]
        """
        configs = self._discover_from_yaml()
        self._handler_configs = configs
        logger.info(f"Discovered {len(configs)} handler(s)")
        return configs

    def _discover_from_yaml(self) -> list[HandlerConfig]:
        """Discover handlers from YAML configuration file.

        :returns: List of handler configurations from YAML
        :rtype: list[HandlerConfig]
        """
        configs: list[HandlerConfig] = []

        if not self._config_path.exists():
            logger.error(f"Configuration file not found: {self._config_path}")
            return configs

        try:
            with open(self._config_path, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)

            if not data or "handlers" not in data:
                logger.warning("No handlers found in configuration file")
                return configs

            for handler_data in data["handlers"]:
                config = HandlerConfig(
                    module=handler_data["module"],
                    class_name=handler_data["class"],
                    command=handler_data["command"],
                    callbacks=handler_data.get("callbacks", []),
                    text_input=handler_data.get("text_input"),
                    waiting_states=handler_data.get("waiting_states", []),
                )
                configs.append(config)
                logger.debug(f"Loaded handler config: {config.command}")

        except Exception as error:
            logger.error(f"Failed to load YAML configuration: {error}")

        return configs

    def load_handler_class(self, config: HandlerConfig) -> type:
        """Load a handler class from its configuration.

        :param config: Handler configuration
        :type config: HandlerConfig
        :returns: The handler class
        :rtype: type
        :raises PluginLoadError: If the handler class cannot be loaded
        """
        # Check cache first
        if config.command in self._loaded_handlers:
            return self._loaded_handlers[config.command]

        try:
            module = importlib.import_module(config.module)
            handler_class = getattr(module, config.class_name)
            self._loaded_handlers[config.command] = handler_class
            return handler_class
        except ImportError as error:
            raise PluginLoadError(
                plugin_name=config.command,
                reason=f"Could not import module '{config.module}': {error}",
            ) from error
        except AttributeError as error:
            raise PluginLoadError(
                plugin_name=config.command,
                reason=f"Class '{config.class_name}' not found in '{config.module}': {error}",
            ) from error

    def get_handler_configs(self) -> list[HandlerConfig]:
        """Get all discovered handler configurations.

        :returns: List of handler configurations
        :rtype: list[HandlerConfig]
        """
        return self._handler_configs.copy()

    def get_loaded_handler(self, command: str) -> type | None:
        """Get a loaded handler class by command name.

        :param command: Command name to look up
        :type command: str
        :returns: Handler class or None if not loaded
        :rtype: type | None
        """
        return self._loaded_handlers.get(command)


def create_default_loader() -> PluginLoader:
    """Create a PluginLoader with default configuration.

    :returns: Configured PluginLoader instance
    :rtype: PluginLoader
    """
    return PluginLoader()
