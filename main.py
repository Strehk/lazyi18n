#!/usr/bin/env python3
"""
lazyi18n - A TUI for managing i18next translation files.
"""

import sys
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

try:
    __version__ = version("lazyi18n")
except PackageNotFoundError:
    __version__ = "unknown"

from ui.app import LazyI18nTUI
from core.config import Config
from core.translator import Translator, TranslationError
from core.project import TranslationProject


def handle_config_command(args):
    """Handle config subcommand."""
    config = Config(Path(args.directory) if args.local else None)

    if args.config_action == "view":
        # View all config or specific key
        if args.key:
            value = config.get(args.key)
            if value is not None:
                print(f"{args.key} = {value}")
            else:
                print(f"Config key '{args.key}' not found")
                sys.exit(1)
        else:
            # Show all config
            all_config = config.list_all()
            if all_config:
                import tomli_w

                print(tomli_w.dumps(all_config))
            else:
                print("No configuration set")

    elif args.config_action == "set":
        # Set a config value
        if not args.key or args.value is None:
            print("Error: Both --key and --value are required for 'set'")
            sys.exit(1)

        # Parse value (try to convert to appropriate type)
        value = args.value
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        elif value.replace(".", "", 1).isdigit():
            value = float(value)

        if config.set(args.key, value, local=args.local):
            scope = "local" if args.local else "global"
            print(f"Set {scope} config: {args.key} = {value}")
        else:
            print("Error: Failed to save configuration")
            sys.exit(1)

    elif args.config_action == "delete":
        # Delete a config value
        if not args.key:
            print("Error: --key is required for 'delete'")
            sys.exit(1)

        if config.delete(args.key, local=args.local):
            scope = "local" if args.local else "global"
            print(f"Deleted {scope} config key: {args.key}")
        else:
            print(f"Error: Config key '{args.key}' not found")
            sys.exit(1)


def handle_translate_command(args):
    """Handle translate subcommand."""
    project = TranslationProject(args.directory)

    print("Loading translations...")
    if not project.load():
        print("Error: Failed to load translations from", args.directory)
        sys.exit(1)

    # Load config to get API key
    config = Config(Path(args.directory))
    api_key = config.get("translator.api_key")

    translator = Translator(api_key=api_key)

    try:
        print("Translating missing keys...")
        translations = translator.translate_all_missing(
            project, source_locale=args.source
        )

        if not translations:
            print("No missing translations found")
            return

        # Apply translations to project
        count = 0
        for (locale, key), text in translations.items():
            project.set_key_value(locale, key, text)
            count += 1
            print(f"  [{locale}] {key}: {text}")

        print(f"\nTranslated {count} keys")

        # Save if requested
        if args.save:
            print("Saving translations...")
            if project.save():
                print("Saved successfully")
            else:
                print("Error: Failed to save translations")
                sys.exit(1)
        else:
            print("\nChanges not saved. Use --save to persist translations.")

    except TranslationError as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="lazyi18n - TUI for managing i18next translations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # TUI command (default)
    tui_parser = subparsers.add_parser(
        "tui", help="Launch the TUI (default)", add_help=False
    )
    tui_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Path to directory with translation files (default: current directory)",
    )
    tui_parser.add_argument(
        "-e",
        "--edit",
        help="Start in edit mode for a specific key (creates it if missing)",
        metavar="KEY",
    )

    # Config command
    config_parser = subparsers.add_parser(
        "config", help="View or modify configuration"
    )
    config_parser.add_argument(
        "config_action",
        choices=["view", "set", "delete"],
        help="Action to perform: view config, set a value, or delete a key",
    )
    config_parser.add_argument(
        "-k", "--key", help="Configuration key (supports dot notation, e.g., translator.api_key)"
    )
    config_parser.add_argument("-v", "--value", help="Value to set (for 'set' action)")
    config_parser.add_argument(
        "-l",
        "--local",
        action="store_true",
        help="Use local config (project-specific) instead of global",
    )
    config_parser.add_argument(
        "-d",
        "--directory",
        default=".",
        help="Project directory for local config (default: current directory)",
    )

    # Translate command
    translate_parser = subparsers.add_parser(
        "translate", help="Machine translate missing keys"
    )
    translate_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Path to directory with translation files (default: current directory)",
    )
    translate_parser.add_argument(
        "-s",
        "--source",
        help="Source locale to translate from (auto-detected if not specified)",
    )
    translate_parser.add_argument(
        "--save",
        action="store_true",
        help="Save translations immediately (default: only stage changes)",
    )

    # Global arguments
    parser.add_argument(
        "--version",
        action="version",
        version=f"lazyi18n {__version__}",
        help="Show version information and exit",
    )

    # Parse arguments
    args = parser.parse_args()

    # Handle subcommands
    if args.command == "config":
        handle_config_command(args)
    elif args.command == "translate":
        handle_translate_command(args)
    else:
        # Default to TUI (either explicit 'tui' command or no command)
        if args.command is None:
            # No subcommand, parse as TUI with backward compatibility
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

        tui = LazyI18nTUI(args.directory, initial_key=getattr(args, "edit", None))
        app = tui.create_app()
        app.run()


if __name__ == "__main__":
    main()

