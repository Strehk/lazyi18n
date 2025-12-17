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
        help="Path to directory with translation files",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"lazyi18n {__version__}",
        help="Show version information and exit",
    )
    
    args = parser.parse_args()
    
    tui = LazyI18nTUI(args.directory)
    
    if not tui.load():
        print("Error: Failed to load translations from", args.directory)
        sys.exit(1)
    
    app = tui.create_app()
    app.run()


if __name__ == "__main__":
    main()
