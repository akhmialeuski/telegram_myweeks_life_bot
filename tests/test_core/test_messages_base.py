"""Additional coverage tests for BaseMessageGenerator and MessageContext."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest

from src.core._messages.base import BaseMessageGenerator
from src.core.message_context import MessageContext, use_message_context


class DummyGenerator(BaseMessageGenerator):
    """Minimal subclass to expose BaseMessageGenerator helpers."""

    pass


def _make_user(user_id: int = 1, language_code: str = "en") -> Any:
    """Create a simple user-like mock with id and language_code."""

    user = Mock()
    user.id = user_id
    user.language_code = language_code
    user.first_name = "Test"
    return user


@pytest.mark.asyncio
async def test_base_helpers_cover_percentage_and_fallbacks() -> None:
    """Cover format_life_percentage(None), birth_date_str(None), and subscription_type_value() fallback.

    Ensures that when no explicit value is provided, the percentage is taken from
    MessageContext.life_stats, and birth_date_str(None) uses builder.not_set().
    Also verifies BASIC fallback when no profile is present.
    """

    user = _make_user()

    # Patch ServiceContainer usage inside MessageContext.from_user to avoid DB calls
    with patch("src.services.container.ServiceContainer") as mock_container:
        # Builder with get/not_set
        builder = Mock()
        builder.get.return_value = "ok"
        builder.not_set.return_value = "<not set>"
        mock_container.return_value.get_message_builder.return_value = builder
        # No profile when fetch_profile=False
        mock_container.return_value.get_user_service.return_value.get_user_profile.return_value = (
            None
        )

        with use_message_context(user_info=user, fetch_profile=False):
            # Stub life_stats to control value
            with patch.object(
                MessageContext, "life_stats", return_value={"life_percentage": 0.123}
            ):
                gen = DummyGenerator()
                assert gen.format_life_percentage() == "12.3%"

            # Birth date None -> not_set()
            gen2 = DummyGenerator()
            assert gen2.birth_date_str(None) == "<not set>"

            # No profile -> BASIC subscription fallback
            assert gen2.subscription_type_value() == "basic"


def test_message_context_require_raises_without_context() -> None:
    """Ensure MessageContext.require raises when no context is set."""

    with pytest.raises(RuntimeError):
        MessageContext.require()


def test_message_context_subscription_type_basic() -> None:
    """Ensure MessageContext.subscription_type_value returns BASIC when no profile."""

    user = _make_user()
    with patch("src.services.container.ServiceContainer") as mock_container:
        builder = Mock()
        mock_container.return_value.get_message_builder.return_value = builder
        mock_container.return_value.get_user_service.return_value.get_user_profile.return_value = (
            None
        )

        with use_message_context(user_info=user, fetch_profile=False) as ctx:
            assert ctx.subscription_type_value() == "basic"
