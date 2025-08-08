"""Tests ensuring translation files are complete."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.utils.localization import LANGUAGES, LOCALE_DIR


def _unquote(text: str) -> str:
    """Unquote a PO file string."""
    return bytes(text[1:-1], "utf-8").decode("unicode_escape")


def _is_separator_line(line: str) -> bool:
    """Check whether a line separates PO entries.

    A separator line is either a comment line starting with '#'
    or an empty line. Such lines indicate the end of the current
    entry and the start of a new one.

    :param line: Line content stripped of surrounding whitespace
    :type line: str
    :returns: True if the line is a separator, otherwise False
    :rtype: bool
    """
    return line.startswith("#") or line == ""


def _flush_current_entry(
    *,
    entries: List[Dict[str, object]],
    context: Optional[str],
    msgid: Optional[str],
    msgid_plural: Optional[str],
    msgstrs: Dict[int, str],
) -> None:
    """Append the current entry to entries if it is populated.

    :param entries: Collection where parsed entries are accumulated
    :type entries: List[Dict[str, object]]
    :param context: Current msgctxt value
    :type context: Optional[str]
    :param msgid: Current msgid value
    :type msgid: Optional[str]
    :param msgid_plural: Current msgid_plural value
    :type msgid_plural: Optional[str]
    :param msgstrs: Accumulated msgstr values indexed by plural form
    :type msgstrs: Dict[int, str]
    :returns: None
    :rtype: None
    """
    if msgid is not None:
        entries.append(
            {
                "context": context,
                "msgid": msgid,
                "msgid_plural": msgid_plural,
                "msgstrs": msgstrs,
            }
        )


def _reset_entry_state() -> (
    Tuple[
        Optional[str],
        Optional[str],
        Optional[str],
        Dict[int, str],
        Optional[str],
    ]
):
    """Return a new, clean state tuple for PO entry parsing.

    :returns: Tuple of (context, msgid, msgid_plural, msgstrs, state)
    :rtype: Tuple[Optional[str], Optional[str], Optional[str], Dict[int, str], Optional[str]]
    """
    return None, None, None, {}, None


def _apply_continuation(
    *,
    state: Optional[str],
    text: str,
    context: Optional[str],
    msgid: Optional[str],
    msgid_plural: Optional[str],
    msgstrs: Dict[int, str],
) -> Tuple[Optional[str], Optional[str], Optional[str], Dict[int, str]]:
    """Apply a continued string line to the correct field based on state.

    :param state: Current parser state (e.g., 'msgid', 'msgstr', 'msgstr[1]')
    :type state: Optional[str]
    :param text: Unquoted text to append
    :type text: str
    :param context: Current context value
    :type context: Optional[str]
    :param msgid: Current msgid value
    :type msgid: Optional[str]
    :param msgid_plural: Current msgid_plural value
    :type msgid_plural: Optional[str]
    :param msgstrs: Current msgstr dictionary
    :type msgstrs: Dict[int, str]
    :returns: Updated (context, msgid, msgid_plural, msgstrs)
    :rtype: Tuple[Optional[str], Optional[str], Optional[str], Dict[int, str]]
    """
    if state == "msgctxt":
        context = (context or "") + text
    elif state == "msgid":
        msgid = (msgid or "") + text
    elif state == "msgid_plural":
        msgid_plural = (msgid_plural or "") + text
    elif state and state.startswith("msgstr"):
        if state == "msgstr":
            idx: int = 0
        else:
            start: int = state.find("[") + 1
            end: int = state.find("]")
            idx = int(state[start:end])
        msgstrs[idx] = msgstrs.get(idx, "") + text
    return context, msgid, msgid_plural, msgstrs


def _process_po_line(
    *,
    line: str,
    state: Optional[str],
    context: Optional[str],
    msgid: Optional[str],
    msgid_plural: Optional[str],
    msgstrs: Dict[int, str],
) -> Tuple[Optional[str], Optional[str], Optional[str], Dict[int, str], Optional[str]]:
    """Process a single non-separator PO line and update parsing state.

    :param line: The current line content (stripped)
    :type line: str
    :param state: Current parser state
    :type state: Optional[str]
    :param context: Current context value
    :type context: Optional[str]
    :param msgid: Current msgid value
    :type msgid: Optional[str]
    :param msgid_plural: Current msgid_plural value
    :type msgid_plural: Optional[str]
    :param msgstrs: Current msgstr dictionary
    :type msgstrs: Dict[int, str]
    :returns: Updated (context, msgid, msgid_plural, msgstrs, state)
    :rtype: Tuple[Optional[str], Optional[str], Optional[str], Dict[int, str], Optional[str]]
    """
    if line.startswith("msgctxt"):
        context = _unquote(line[7:].strip())
        return context, msgid, msgid_plural, msgstrs, "msgctxt"
    if line.startswith("msgid_plural"):
        msgid_plural = _unquote(line[len("msgid_plural") :].strip())
        return context, msgid, msgid_plural, msgstrs, "msgid_plural"
    if line.startswith("msgid"):
        msgid = _unquote(line[5:].strip())
        return context, msgid, msgid_plural, msgstrs, "msgid"
    if line.startswith("msgstr["):
        idx_str: str = line.split("[", 1)[1].split("]", 1)[0]
        idx = int(idx_str)
        msgstrs[idx] = _unquote(line.split(" ", 1)[1].strip())
        return context, msgid, msgid_plural, msgstrs, f"msgstr[{idx}]"
    if line.startswith("msgstr"):
        msgstrs[0] = _unquote(line[6:].strip())
        return context, msgid, msgid_plural, msgstrs, "msgstr"
    if line.startswith('"'):
        text: str = _unquote(line)
        context, msgid, msgid_plural, msgstrs = _apply_continuation(
            state=state,
            text=text,
            context=context,
            msgid=msgid,
            msgid_plural=msgid_plural,
            msgstrs=msgstrs,
        )
        return context, msgid, msgid_plural, msgstrs, state
    return context, msgid, msgid_plural, msgstrs, state


def _parse_po(path: Path) -> List[Dict[str, object]]:
    """Parse a PO file into a list of entries.

    The parser performs a lightweight state-machine pass over the file,
    producing a list of dictionaries with keys: 'context', 'msgid',
    'msgid_plural', and 'msgstrs'.

    :param path: Path to a .po file
    :type path: Path
    :returns: Parsed entries
    :rtype: List[Dict[str, object]]
    """
    entries: List[Dict[str, object]] = []
    context: Optional[str] = None
    msgid: Optional[str] = None
    msgid_plural: Optional[str] = None
    msgstrs: Dict[int, str] = {}
    state: Optional[str] = None

    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if _is_separator_line(line):
                _flush_current_entry(
                    entries=entries,
                    context=context,
                    msgid=msgid,
                    msgid_plural=msgid_plural,
                    msgstrs=msgstrs,
                )
                context, msgid, msgid_plural, msgstrs, state = _reset_entry_state()
                continue
            context, msgid, msgid_plural, msgstrs, state = _process_po_line(
                line=line,
                state=state,
                context=context,
                msgid=msgid,
                msgid_plural=msgid_plural,
                msgstrs=msgstrs,
            )
        _flush_current_entry(
            entries=entries,
            context=context,
            msgid=msgid,
            msgid_plural=msgid_plural,
            msgstrs=msgstrs,
        )
    return entries


def test_all_po_entries_have_translations() -> None:
    """Ensure every msgid in .po files has a corresponding translation."""
    for lang in LANGUAGES:
        po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "messages.po"
        for entry in _parse_po(po_path):
            if not entry["msgid"]:
                continue
            if entry["msgid_plural"]:
                assert all(entry["msgstrs"].values()), f"Missing plural forms in {lang}"
            else:
                assert entry["msgstrs"].get(0), f"Missing translation in {lang}"
