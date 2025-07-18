"""Visualize command handler for life weeks visualization.

This module contains the VisualizeHandler class which handles the /visualize command
and generates visual representations of life weeks. It creates charts and graphs
to help users visualize their life progress.

The visualization includes:
- Life weeks chart showing lived vs remaining weeks
- Age progression visualization
- Life expectancy comparison
- Customizable chart types based on subscription
"""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from ...core.messages import generate_message_visualize
from ...visualization.grid import generate_visualization
from ..constants import COMMAND_VISUALIZE
from .base_handler import BaseHandler


class VisualizeHandler(BaseHandler):
    """Handler for /visualize command - generate life weeks visualization.

    This handler provides users with visual representations of their life
    weeks including charts, graphs, and progress indicators. The type of
    visualization depends on the user's subscription level.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self) -> None:
        """Initialize the visualize handler.

        Sets up the command name and initializes the base handler.
        """
        super().__init__()
        self.command_name = f"/{COMMAND_VISUALIZE}"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle /visualize command - generate life weeks visualization.

        This command creates and sends a visual grid representation of the user's
        life, showing weeks lived as filled cells and remaining weeks as empty cells.
        It provides both the visual image and a caption with key statistics.

        The visualization process:
        1. Retrieves user profile from database
        2. Generates visual grid using LifeCalculatorEngine
        3. Creates image with weeks lived highlighted
        4. Generates caption with key statistics
        5. Sends both image and caption to user

        The visual grid shows:
        - Each cell represents one week
        - Each row represents one year (52 weeks)
        - Green cells = weeks lived
        - Empty cells = weeks not yet lived
        - Years labeled on vertical axis
        - Weeks labeled on horizontal axis

        :param update: The update object containing the visualize command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None

        Example:
            User sends /visualize → Bot generates grid image → Shows visual life representation
        """
        return await self._wrap_with_registration(self._handle_visualize)(
            update, context
        )

    async def _handle_visualize(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Internal method to handle /visualize command with registration check.

        :param update: The update object containing the visualize command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        # Extract user information
        user = update.effective_user
        self.log_command(user.id, self.command_name)
        self.logger.info(f"Handling /visualize command from user {user.id}")

        # Generate and send visual representation with caption
        await update.message.reply_photo(
            photo=generate_visualization(user_info=user),
            caption=generate_message_visualize(user_info=user),
            parse_mode="HTML",
        )
