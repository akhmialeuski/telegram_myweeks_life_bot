#!/usr/bin/env python3
"""Script to compile .po files to .mo files for gettext localization.

This script compiles all .po files in the locales directory to .mo files
for use with the gettext system. It relies on the standard ``msgfmt``
utility available in GNU gettext.
"""

import subprocess
import sys
from pathlib import Path


def compile_po_files():
    """Compile all .po files to .mo files."""
    # Get the project root directory
    project_root = Path(__file__).resolve().parent.parent
    locales_dir = project_root / "locales"

    if not locales_dir.exists():
        print(f"Locales directory not found: {locales_dir}")
        return False

    # Find all .po files
    po_files = list(locales_dir.rglob("*.po"))

    if not po_files:
        print("No .po files found in locales directory")
        return False

    print(f"Found {len(po_files)} .po files to compile")

    success_count = 0
    error_count = 0

    for po_file in po_files:
        # Create .mo file path
        mo_file = po_file.with_suffix(".mo")

        try:
            subprocess.run(
                ["msgfmt", str(po_file), "-o", str(mo_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            print(
                f"✓ Compiled {po_file.relative_to(project_root)} -> {mo_file.relative_to(project_root)}"
            )
            success_count += 1
        except subprocess.CalledProcessError as exc:
            print(
                f"✗ Failed to compile {po_file.relative_to(project_root)}: {exc.stderr.strip()}"
            )
            error_count += 1

    print(f"\nCompilation complete: {success_count} successful, {error_count} failed")
    return error_count == 0


if __name__ == "__main__":
    success = compile_po_files()
    sys.exit(0 if success else 1)
