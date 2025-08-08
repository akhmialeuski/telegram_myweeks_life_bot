"""Tests ensuring translation files are complete."""

from pathlib import Path
from typing import Dict, List, Optional

from src.utils.localization import LANGUAGES, LOCALE_DIR


def _unquote(text: str) -> str:
    """Unquote a PO file string."""
    return bytes(text[1:-1], "utf-8").decode("unicode_escape")


def _parse_po(path: Path) -> List[Dict[str, object]]:
    """Parse a PO file into a list of entries."""
    entries: List[Dict[str, object]] = []
    context: Optional[str] = None
    msgid: Optional[str] = None
    msgid_plural: Optional[str] = None
    msgstrs: Dict[int, str] = {}
    state: Optional[str] = None

    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line.startswith("#") or line == "":
                if msgid is not None:
                    entries.append(
                        {
                            "context": context,
                            "msgid": msgid,
                            "msgid_plural": msgid_plural,
                            "msgstrs": msgstrs,
                        }
                    )
                context = None
                msgid = None
                msgid_plural = None
                msgstrs = {}
                state = None
                continue
            if line.startswith("msgctxt"):
                context = _unquote(line[7:].strip())
                state = "msgctxt"
                continue
            if line.startswith("msgid_plural"):
                msgid_plural = _unquote(line[len("msgid_plural"):].strip())
                state = "msgid_plural"
                continue
            if line.startswith("msgid"):
                msgid = _unquote(line[5:].strip())
                state = "msgid"
                continue
            if line.startswith("msgstr["):
                idx = int(line.split("[")[1].split("]")[0])
                msgstrs[idx] = _unquote(line.split(" ", 1)[1].strip())
                state = f"msgstr[{idx}]"
                continue
            if line.startswith("msgstr"):
                msgstrs[0] = _unquote(line[6:].strip())
                state = "msgstr"
                continue
            if line.startswith('"'):
                text = _unquote(line)
                if state == "msgctxt":
                    context = (context or "") + text
                elif state == "msgid":
                    msgid = (msgid or "") + text
                elif state == "msgid_plural":
                    msgid_plural = (msgid_plural or "") + text
                elif state and state.startswith("msgstr"):
                    idx = 0 if state == "msgstr" else int(state[7])
                    msgstrs[idx] = msgstrs.get(idx, "") + text
        if msgid is not None:
            entries.append(
                {
                    "context": context,
                    "msgid": msgid,
                    "msgid_plural": msgid_plural,
                    "msgstrs": msgstrs,
                }
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
