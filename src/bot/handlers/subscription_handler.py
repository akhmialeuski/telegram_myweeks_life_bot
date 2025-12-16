"""Subscription command handler for user subscription management.

This module contains the SubscriptionHandler class which handles the /subscription command
and related callbacks. It allows users to view their subscription status and manage
subscription features.

The subscription management includes:
- Display current subscription status
- Show subscription benefits and features
- Manage subscription upgrades
- Handle subscription-related callbacks
"""

from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.core.messages import SubscriptionMessages
from src.enums import SubscriptionType

from ...database.service import UserSubscriptionUpdateError
from ...services.container import ServiceContainer
from ...services.i18n_adapter import BabelI18nAdapter
from ...utils.config import BOT_NAME, BUYMEACOFFEE_URL
from ...utils.logger import get_logger
from ..constants import COMMAND_SUBSCRIPTION
from .base_handler import BaseHandler

# from src.i18n import use_locale # This line is removed as pgettext is no longer used


# Initialize logger for this module
logger = get_logger(BOT_NAME)


class SubscriptionHandler(BaseHandler):
    """Handler for /subscription command and related callbacks.

    This handler manages user subscription information and provides
    subscription-related functionality including status display,
    upgrade options, and feature explanations.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the subscription handler.

        Sets up the command name and initializes the base handler.

        :param services: Service container with all dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = f"/{COMMAND_SUBSCRIPTION}"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle /subscription command - show user subscription.

        This command allows users to view and manage their subscription.
        It provides a list of available subscriptions and allows users to change them.

        :param update: The update object containing the subscription command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Optional[int] or None
        """
        return await self._wrap_with_registration(
            handler_method=self._handle_subscription
        )(
            update=update,
            context=context,
        )

    async def _handle_subscription(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> Optional[int]:
        """Internal method to handle /subscription command with registration check.

        :param update: The update object containing the subscription command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Optional[int] or None
        """
        # Extract user information using the new helper method
        cmd_context = await self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        user_profile = cmd_context.user_profile
        current_subscription = user_profile.subscription.subscription_type

        logger.info(f"{self.command_name}: [{user_id}]: Handling command")

        try:
            # Resolve language from DB or Telegram
            profile = await self.services.user_service.get_user_profile(
                telegram_id=user_id
            )
            lang = (
                profile.settings.language
                if profile and profile.settings and profile.settings.language
                else (user.language_code or "en")
            )

            # Use helpers
            i18n = BabelI18nAdapter(lang=lang)
            messages = SubscriptionMessages(i18n=i18n)

            # Create subscription selection keyboard
            keyboard = []
            for subscription_type in SubscriptionType:
                # Add checkmark for current subscription
                text = (
                    f"{'✅ ' if subscription_type == current_subscription else ''}"
                    f"{subscription_type.value.title()}"
                )
                callback_data = f"subscription_{subscription_type.value}"
                keyboard.append(
                    [InlineKeyboardButton(text=text, callback_data=callback_data)]
                )

            # Prepare description for current subscription (optional)
            if current_subscription == SubscriptionType.BASIC:
                subscription_description = messages.basic_info(
                    buymeacoffee_url=BUYMEACOFFEE_URL
                )
            else:
                subscription_description = messages.premium_content()

            # Send current subscription message
            await self.send_message(
                update=update,
                message_text=messages.management(
                    subscription_type=current_subscription.value,
                    subscription_description=subscription_description,
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as error:
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=str(error),
            )

    async def handle_subscription_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle subscription selection callback from inline keyboard.

        This function processes the user's subscription selection and updates
        the database accordingly. It provides feedback about the change.

        :param update: The update object containing the callback
        :type update: Update
        :param context: The context object for the callback execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        query = update.callback_query
        cmd_context = await self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        user_profile = cmd_context.user_profile

        callback_data = query.data
        logger.info(
            f"{self.command_name}: [{user_id}]: Callback executed: {callback_data}"
        )

        # Resolve language
        profile = await self.services.user_service.get_user_profile(telegram_id=user_id)
        lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else (user.language_code or "en")
        )

        # Use helpers
        i18n = BabelI18nAdapter(lang=lang)
        messages = SubscriptionMessages(i18n=i18n)

        try:
            # Answer the callback query to remove loading state
            await query.answer()

            # Extract subscription type from callback data
            new_subscription_type = SubscriptionType(
                callback_data.replace("subscription_", "")
            )

            current_subscription = user_profile.subscription.subscription_type

            # Check if subscription actually changed
            if current_subscription == new_subscription_type:
                await self.edit_message(
                    query=query,
                    message_text=messages.already_active(
                        subscription=user_profile.subscription
                    ),
                )
                return

            # Update subscription in database
            await self.services.user_service.update_user_subscription(
                telegram_id=user_id,
                subscription_type=new_subscription_type,
            )

            # Prepare description for new subscription
            if new_subscription_type == SubscriptionType.BASIC:
                subscription_description = messages.basic_info(
                    buymeacoffee_url=BUYMEACOFFEE_URL
                )
            else:
                subscription_description = messages.premium_content()

            # Show success message
            await self.edit_message(
                query=query,
                message_text=messages.change_success(
                    subscription_type=new_subscription_type.value,
                    subscription_description=subscription_description,
                ),
            )

            logger.info(
                f"{self.command_name}: [{user_id}]: Subscription changed from {current_subscription} to {new_subscription_type}"
            )

        except UserSubscriptionUpdateError:
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=messages.change_failed(),
            )

        except Exception:
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=messages.change_error(),
            )
