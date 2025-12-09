"""Plugin loader for handler discovery via entry points and configuration.

This module provides the PluginLoader class that discovers handlers using
Python entry points (for installed packages) or falls back to YAML
configuration files for development environments.
"""

import importlib
import logging
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Entry point group name for handler plugins
ENTRY_POINT_GROUP = "lifeweeksbot.handlers"

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

    The loader attempts to discover handlers in the following order:
    1. Entry points from the 'lifeweeksbot.handlers' group
    2. YAML configuration file (fallback for development)

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
        """Discover all available handlers.

        First attempts to load from entry points, then falls back to
        YAML configuration if no entry points are found.

        :returns: List of handler configurations
        :rtype: list[HandlerConfig]
        """
        # Try entry points first
        configs = self._discover_from_entry_points()

        if not configs:
            # Fall back to YAML configuration
            logger.debug("No entry points found, trying YAML configuration")
            configs = self._discover_from_yaml()

        self._handler_configs = configs
        logger.info(f"Discovered {len(configs)} handler(s)")
        return configs

    def _discover_from_entry_points(self) -> list[HandlerConfig]:
        """Discover handlers from Python entry points.

        :returns: List of handler configurations from entry points
        :rtype: list[HandlerConfig]
        """
        configs: list[HandlerConfig] = []

        try:
            eps = entry_points(group=ENTRY_POINT_GROUP)
            for ep in eps:
                try:
                    handler_class = ep.load()
                    config = self._create_config_from_class(
                        handler_class=handler_class,
                        command=ep.name,
                    )
                    configs.append(config)
                    self._loaded_handlers[ep.name] = handler_class
                    logger.debug(f"Loaded handler from entry point: {ep.name}")
                except Exception as error:
                    logger.warning(f"Failed to load entry point '{ep.name}': {error}")
        except Exception as error:
            logger.debug(
                f"No entry points found for group '{ENTRY_POINT_GROUP}': {error}"
            )

        return configs

    def _discover_from_yaml(self) -> list[HandlerConfig]:
        """Discover handlers from YAML configuration file.

        :returns: List of handler configurations from YAML
        :rtype: list[HandlerConfig]
        """
        configs: list[HandlerConfig] = []

        if not self._config_path.exists():
            logger.debug(f"Configuration file not found: {self._config_path}")
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
                logger.debug(f"Loaded handler config from YAML: {config.command}")

        except Exception as error:
            logger.error(f"Failed to load YAML configuration: {error}")

        return configs

    def _create_config_from_class(
        self,
        handler_class: type,
        command: str,
    ) -> HandlerConfig:
        """Create HandlerConfig from a handler class.

        Extracts configuration from class attributes if available.

        :param handler_class: The handler class to inspect
        :type handler_class: type
        :param command: Command name for this handler
        :type command: str
        :returns: Handler configuration
        :rtype: HandlerConfig
        """
        # Try to get configuration from class attributes
        callbacks = getattr(handler_class, "CALLBACKS", [])
        text_input = getattr(handler_class, "TEXT_INPUT", None)
        waiting_states = getattr(handler_class, "WAITING_STATES", [])

        return HandlerConfig(
            module=handler_class.__module__,
            class_name=handler_class.__name__,
            command=command,
            callbacks=callbacks,
            text_input=text_input,
            waiting_states=waiting_states,
        )

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
                reason=f"Class '{config.class_name}' not found in module '{config.module}': {error}",
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
