#!/usr/bin/env python3
"""
lazyi18n - A TUI for managing i18next translation files.

Enhanced version v3 with:
- Inline editing
- Single-key shortcuts
- Search/filter functionality
- New key creation wizard
"""

__version__ = "3.0.0"

import sys

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
