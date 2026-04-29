"""
VPSPilot — Command Router
Maps user commands to their handler functions with a clean registry pattern.
"""

from typing import Callable, Any
from telegram import Update
from telegram.ext import ContextTypes

# Type alias for command handlers
Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Any]


class CommandRouter:
    """
    Central registry for all bot commands.
    Provides a clean way to register and look up handlers.
    """

    def __init__(self) -> None:
        self._commands: dict[str, Handler] = {}
        self._descriptions: dict[str, str] = {}

    def register(self, command: str, handler: Handler, description: str = "") -> None:
        """Register a command with its handler and optional description."""
        self._commands[command] = handler
        self._descriptions[command] = description

    def get_handler(self, command: str) -> Handler | None:
        """Look up a handler by command name."""
        return self._commands.get(command)

    def get_all_commands(self) -> dict[str, str]:
        """Return all registered commands with their descriptions."""
        return dict(self._descriptions)

    @property
    def command_names(self) -> list[str]:
        """Return a list of all registered command names."""
        return list(self._commands.keys())


# Global router instance
router = CommandRouter()
