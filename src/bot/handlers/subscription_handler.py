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

from src.i18n import use_locale

from ...core.enums import SubscriptionType
from ...database.service import UserSubscriptionUpdateError
from ...services.container import ServiceContainer
from ...utils.config import BOT_NAME, BUYMEACOFFEE_URL
from ...utils.logger import get_logger
from ..constants import COMMAND_SUBSCRIPTION
from .base_handler import BaseHandler

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
        cmd_context = self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        user_profile = cmd_context.user_profile
        current_subscription = user_profile.subscription.subscription_type

        logger.info(f"{self.command_name}: [{user_id}]: Handling command")

        try:
            # Resolve language from DB or Telegram
            profile = self.services.user_service.get_user_profile(telegram_id=user_id)
            lang = (
                profile.settings.language
                if profile and profile.settings and profile.settings.language
                else (user.language_code or "en")
            )
            _, _, pgettext = use_locale(lang=lang)

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
                subscription_description = pgettext(
                    "subscription.basic_info",
                    "💡 <b>Basic Subscription</b>\n\n"
                    "You are using the basic version of the bot with core functionality.\n\n"
                    "🔗 <b>Support the project:</b>\n"
                    "• GitHub: https://github.com/your-project/lifeweeks-bot\n"
                    "• Donate: {buymeacoffee_url}\n\n"
                    "Your support helps develop the bot! 🙏",
                ).format(buymeacoffee_url=BUYMEACOFFEE_URL)
            else:
                subscription_description = pgettext(
                    "subscription.premium_content",
                    "✨ <b>Premium Content</b>\n\n"
                    "🧠 <b>Psychology of Time:</b>\n"
                    "Research shows that time visualization helps make more conscious decisions. When we see the limitation of our weeks, we begin to value each one.\n\n"
                    "📊 <b>Interesting Facts:</b>\n"
                    "• Average person spends 26 years sleeping (about 1,352 weeks)\n"
                    "• 11 years working (572 weeks)\n"
                    "• 5 years eating and cooking (260 weeks)\n"
                    "• 4 years commuting (208 weeks)\n\n"
                    "🎯 <b>Daily Tip:</b> Try doing something new every week - it will help make life more fulfilling and memorable!",
                )

            # Send current subscription message
            await self.send_message(
                update=update,
                message_text=pgettext(
                    "subscription.management",
                    "🔐 <b>Subscription Management</b>\n\n"
                    "Current subscription: <b>{subscription_type}</b>\n"
                    "{subscription_description}\n\n"
                    "Select new subscription type:",
                ).format(
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
        cmd_context = self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        user_profile = cmd_context.user_profile

        callback_data = query.data
        logger.info(
            f"{self.command_name}: [{user_id}]: Callback executed: {callback_data}"
        )

        try:
            # Resolve language
            profile = self.services.user_service.get_user_profile(telegram_id=user_id)
            lang = (
                profile.settings.language
                if profile and profile.settings and profile.settings.language
                else (user.language_code or "en")
            )
            _, _, pgettext = use_locale(lang=lang)

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
                    message_text=pgettext(
                        "subscription.already_active",
                        "ℹ️ You already have an active <b>{subscription_type}</b> subscription",
                    ).format(subscription_type=new_subscription_type.value),
                )
                return

            # Update subscription in database
            self.services.user_service.update_user_subscription(
                user_id,
                new_subscription_type,
            )

            # Prepare description for new subscription
            if new_subscription_type == SubscriptionType.BASIC:
                subscription_description = pgettext(
                    "subscription.basic_info",
                    "💡 <b>Basic Subscription</b>\n\n"
                    "You are using the basic version of the bot with core functionality.\n\n"
                    "🔗 <b>Support the project:</b>\n"
                    "• GitHub: https://github.com/your-project/lifeweeks-bot\n"
                    "• Donate: {buymeacoffee_url}\n\n"
                    "Your support helps develop the bot! 🙏",
                ).format(buymeacoffee_url=BUYMEACOFFEE_URL)
            else:
                subscription_description = pgettext(
                    "subscription.premium_content",
                    "✨ <b>Premium Content</b>\n\n"
                    "🧠 <b>Psychology of Time:</b>\n"
                    "Research shows that time visualization helps make more conscious decisions. When we see the limitation of our weeks, we begin to value each one.\n\n"
                    "📊 <b>Interesting Facts:</b>\n"
                    "• Average person spends 26 years sleeping (about 1,352 weeks)\n"
                    "• 11 years working (572 weeks)\n"
                    "• 5 years eating and cooking (260 weeks)\n"
                    "• 4 years commuting (208 weeks)\n\n"
                    "🎯 <b>Daily Tip:</b> Try doing something new every week - it will help make life more fulfilling and memorable!",
                )

            # Show success message
            await self.edit_message(
                query=query,
                message_text=pgettext(
                    "subscription.change_success",
                    "✅ <b>Subscription successfully changed!</b>\n\n"
                    "New subscription: <b>{subscription_type}</b>\n"
                    "{subscription_description}\n\n"
                    "Changes took effect immediately.",
                ).format(
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
                error_message=pgettext(
                    "subscription.change_failed",
                    "❌ Failed to change subscription. Please try again later.",
                ),
            )

        except Exception:
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=pgettext(
                    "subscription.change_error",
                    "❌ An error occurred while changing subscription",
                ),
            )
