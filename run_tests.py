#!/usr/bin/env python3
"""Simple test runner to check specific test files."""

import os
import subprocess
import sys


def main():
    """Run specific tests and show results."""
    os.chdir(
        "/mnt/c/Users/Anatol_Khmialeuski/PycharmProjects/telegram_myweeks_life_bot"
    )

    test_files = [
        "tests/test_bot/test_scheduler.py",
        "tests/test_bot/test_application.py",
    ]

    cmd = [sys.executable, "-m", "pytest"] + test_files + ["-v", "--tb=short", "-x"]

    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print(f"Return code: {result.returncode}")
        return result.returncode
    except subprocess.TimeoutExpired:
        print("Tests timed out after 60 seconds")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
