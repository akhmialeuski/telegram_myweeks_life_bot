"""Plugin system for dynamic bot functionality loading.

This module provides the core interfaces and registry for the plugin system.
It allows decoupling the bot's core bootstrap logic from specific features.
"""

import logging
from typing import List, Protocol, runtime_checkable

from telegram.ext import Application

from .di import ServiceProvider

logger = logging.getLogger(__name__)


@runtime_checkable
class BotPlugin(Protocol):
    """Protocol defining the contract for bot plugins.

    Plugins are self-contained descriptors of functionality that
    can register handlers, middleware, and other components.
    """

    @property
    def name(self) -> str:
        """Unique name of the plugin for logging and debugging."""
        ...

    def register(self, app: Application, services: ServiceProvider) -> None:
        """Register the plugin's functionality with the application.

        :param app: The Telegram Application instance.
        :param services: The service provider for dependency resolution.
        """
        ...


class PluginRegistry:
    """Registry for managing and loading bot plugins."""

    def __init__(self) -> None:
        self._plugins: List[BotPlugin] = []

    def register_plugin(self, plugin: BotPlugin) -> None:
        """Add a plugin to the registry.

        :param plugin: The plugin instance to register.
        """
        self._plugins.append(plugin)
        logger.debug(f"Registered plugin: {plugin.name}")

    def load_all(self, app: Application, services: ServiceProvider) -> None:
        """Load and register all plugins with the application.

        :param app: The Telegram Application instance.
        :param services: The service provider for dependency resolution.
        """
        for plugin in self._plugins:
            try:
                logger.info(f"Loading plugin: {plugin.name}")
                plugin.register(app, services)
                logger.info(f"Successfully loaded plugin: {plugin.name}")
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin.name}: {e}", exc_info=True)
                # We decide here if we want to crash or continue.
                # For now, we log and continue to allow other plugins to load.
