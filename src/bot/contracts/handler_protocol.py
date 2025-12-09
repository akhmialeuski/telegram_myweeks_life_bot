"""Handler protocol definition for bot command handlers.

This module defines the contract that all command handlers must implement.
It provides a runtime-checkable Protocol for handler validation and
enables plugin-based handler discovery.
"""

from typing import Protocol, runtime_checkable

from telegram import Update
from telegram.ext import ContextTypes


@runtime_checkable
class HandlerProtocol(Protocol):
    """Protocol defining the contract for bot command handlers.

    All command handlers must implement this protocol to be discoverable
    by the plugin system. The protocol ensures consistent handler behavior
    and enables automatic registration.

    Attributes:
        command: The command name this handler responds to (without /)
        callbacks: List of callback configurations for inline keyboard handling
        text_input: Method name for handling text input (or None)
        waiting_states: List of waiting state identifiers for text input routing
    """

    @property
    def command(self) -> str:
        """Return the command name this handler responds to.

        :returns: Command name without the leading slash
        :rtype: str
        """
        ...

    @property
    def callbacks(self) -> list[dict[str, str]]:
        """Return list of callback configurations.

        Each callback configuration is a dict with:
        - 'method': Method name to call for this callback
        - 'pattern': Regex pattern to match callback data

        :returns: List of callback configuration dictionaries
        :rtype: list[dict[str, str]]
        """
        ...

    @property
    def text_input(self) -> str | None:
        """Return method name for handling text input.

        :returns: Method name for text input handling, or None if not applicable
        :rtype: str | None
        """
        ...

    @property
    def waiting_states(self) -> list[str]:
        """Return list of waiting state identifiers.

        Waiting states are used by the universal text handler to route
        user input to the appropriate handler method.

        :returns: List of waiting state string identifiers
        :rtype: list[str]
        """
        ...

    async def handle(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Execute the main handler logic.

        This is the entry point for command handling. It receives the
        Telegram update and context, and performs the handler's main logic.

        :param update: Telegram update object containing the command
        :type update: Update
        :param context: Telegram context for bot operations
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        ...
