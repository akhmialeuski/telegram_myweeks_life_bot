"""Message generation public API (class-based)."""

from __future__ import annotations

from ._messages.base import BaseMessageGenerator
from ._messages.cancel import CancelMessages
from ._messages.registration import RegistrationMessages
from ._messages.settings import SettingsMessages
from ._messages.subscription import SubscriptionMessages
from ._messages.system import SystemMessages
from ._messages.utils import get_user_language
from ._messages.visualize import VisualizeMessages
from ._messages.week import WeeksMessages

__all__ = [
    "BaseMessageGenerator",
    "WeeksMessages",
    "VisualizeMessages",
    "RegistrationMessages",
    "CancelMessages",
    "SubscriptionMessages",
    "SettingsMessages",
    "SystemMessages",
    "get_user_language",
]
