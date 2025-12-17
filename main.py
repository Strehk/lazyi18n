#!/usr/bin/env python3
"""
lazyi18n - A TUI for managing i18next translation files.
"""

import sys
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("lazyi18n")
except PackageNotFoundError:
    __version__ = "unknown"

from ui.app import LazyI18nTUI


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="lazyi18n - TUI for managing i18next translations"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Path to directory with translation files",
    )
    parser.add_argument(
        "-e",
        "--edit",
        help="Start in edit mode for a specific key (creates it if missing)",
        metavar="KEY",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"lazyi18n {__version__}",
        help="Show version information and exit",
    )

    args = parser.parse_args()

    tui = LazyI18nTUI(args.directory, initial_key=args.edit)

    app = tui.create_app()
    app.run()


if __name__ == "__main__":
    main()
