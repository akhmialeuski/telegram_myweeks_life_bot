from __future__ import annotations

import pathlib
import re
from typing import Iterable

ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[1]


# mapping: old function -> "Class().method("
CALL_MAP: dict[str, str] = {
    "generate_message_week(": "WeeksMessages().generate(",
    "generate_message_visualize(": "VisualizeMessages().generate(",
    "generate_message_help(": "SystemMessages().help(",
    "generate_message_unknown_command(": "SystemMessages().unknown(",
    "generate_message_start_welcome_existing(": "SystemMessages().welcome_existing(",
    "generate_message_start_welcome_new(": "SystemMessages().welcome_new(",
    "generate_message_registration_success(": "RegistrationMessages().success(",
    "generate_message_registration_error(": "RegistrationMessages().error(",
    "generate_message_cancel_success(": "CancelMessages().success(",
    "generate_message_cancel_error(": "CancelMessages().error(",
    "generate_message_subscription_current(": "SubscriptionMessages().current(",
    "generate_message_subscription_invalid_type(": "SubscriptionMessages().invalid_type(",
    "generate_message_subscription_profile_error(": "SubscriptionMessages().profile_error(",
    "generate_message_subscription_already_active(": "SubscriptionMessages().already_active(",
    "generate_message_subscription_change_success(": "SubscriptionMessages().change_success(",
    "generate_message_subscription_change_failed(": "SubscriptionMessages().change_failed(",
    "generate_message_subscription_change_error(": "SubscriptionMessages().change_error(",
    "generate_message_settings_basic(": "SettingsMessages().basic(",
    "generate_message_settings_premium(": "SettingsMessages().premium(",
    "generate_message_change_birth_date(": "SettingsMessages().change_birth_date(",
    "generate_message_change_language(": "SettingsMessages().change_language(",
    "generate_message_change_life_expectancy(": "SettingsMessages().change_life_expectancy(",
    "generate_message_birth_date_updated(": "SettingsMessages().birth_date_updated(",
    "generate_message_language_updated(": "SettingsMessages().language_updated(",
    "generate_message_life_expectancy_updated(": "SettingsMessages().life_expectancy_updated(",
    "generate_message_invalid_life_expectancy(": "SettingsMessages().invalid_life_expectancy(",
    "generate_message_settings_error(": "SettingsMessages().settings_error(",
    "generate_settings_buttons(": "SettingsMessages().buttons(",
    "generate_message_birth_date_future_error(": "SettingsMessages().birth_date_future_error(",
    "generate_message_birth_date_old_error(": "SettingsMessages().birth_date_old_error(",
    "generate_message_birth_date_format_error(": "SettingsMessages().birth_date_format_error(",
}


CLASS_IMPORTS = {
    "WeeksMessages",
    "VisualizeMessages",
    "SystemMessages",
    "RegistrationMessages",
    "CancelMessages",
    "SubscriptionMessages",
    "SettingsMessages",
}


def iter_py_files(paths: Iterable[pathlib.Path]) -> Iterable[pathlib.Path]:
    for p in paths:
        if p.is_dir():
            yield from iter_py_files(p.iterdir())
        elif p.suffix == ".py":
            yield p


def rewrite_imports(src: str) -> str:
    # Multi-line from-import
    pat = re.compile(r"from\s+src\.core\.messages\s+import\s+\((.*?)\)", re.DOTALL)

    def repl(m: re.Match[str]) -> str:
        names = [n.strip() for n in m.group(1).split(",") if n.strip()]
        keep = [n for n in names if n in CLASS_IMPORTS or n == "get_user_language"]
        if any(
            n.startswith("generate_message_") or n == "generate_settings_buttons"
            for n in names
        ):
            keep = sorted(set(keep).union(CLASS_IMPORTS))
        return "from src.core.messages import (" + ", ".join(keep) + ")"

    src = pat.sub(repl, src)

    # Single-line from-import
    pat2 = re.compile(r"from\s+src\.core\.messages\s+import\s+([^\n]+)")

    def repl2(m: re.Match[str]) -> str:
        names = [n.strip() for n in m.group(1).split(",")]
        keep = [n for n in names if n in CLASS_IMPORTS or n == "get_user_language"]
        if any(
            n.startswith("generate_message_") or n == "generate_settings_buttons"
            for n in names
        ):
            keep = sorted(set(keep).union(CLASS_IMPORTS))
        return "from src.core.messages import " + ", ".join(keep)

    src = pat2.sub(repl2, src)
    return src


def rewrite_calls(src: str) -> str:
    for old, new in CALL_MAP.items():
        src = src.replace(old, new)
    return src


def main() -> None:
    targets = [ROOT / "src", ROOT / "tests"]
    for file in iter_py_files(targets):
        text = file.read_text(encoding="utf-8")
        new_text = rewrite_imports(text)
        new_text = rewrite_calls(new_text)
        if new_text != text:
            file.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
