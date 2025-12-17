"""
Translation file loader - handles discovering and loading i18next JSON files.
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class LocaleFile:
    """Represents a single locale's translation file."""

    locale: str
    path: Path
    data: Dict


class TranslationFileLoader:
    """Scans and loads translation JSON files from a directory."""

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)
        if not self.directory.exists():
            raise FileNotFoundError(f"Directory not found: {self.directory}")

    def discover_locales(self) -> List[str]:
        """
        Discover all locale files in the directory.
        Supports patterns:
        - en.json, de.json, fr.json (flat structure)
        - locales/en.json, locales/de.json (nested in locales folder)
        """
        locales = []

        def _is_locale_name(name: str) -> bool:
            # Accept simple locale codes like en, de, fr, en-US, pt-BR
            return re.match(r"^[A-Za-z]{2,5}(-[A-Za-z]{2,5})?$", name) is not None

        ignored_dirs = {".venv", "node_modules", ".git"}

        for file in self.directory.glob("**/*.json"):
            if any(part in ignored_dirs for part in file.parts):
                continue
            locale = file.stem
            if _is_locale_name(locale):
                locales.append(locale)

        return sorted(set(locales))

    def load(self) -> Dict[str, LocaleFile]:
        """Load all translation files from the directory."""
        locale_files = {}
        locales = self.discover_locales()

        for locale in locales:
            try:
                # Try common patterns
                file_path = self.directory / f"{locale}.json"
                if not file_path.exists():
                    file_path = self.directory / "locales" / f"{locale}.json"
                if not file_path.exists():
                    # Try recursive search
                    matches = list(self.directory.glob(f"**/{locale}.json"))
                    if matches:
                        file_path = matches[0]
                    else:
                        continue

                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Only accept object-based locale files
                if not isinstance(data, dict):
                    print(f"Warning: Skipping {file_path} (expected JSON object)")
                    continue

                locale_files[locale] = LocaleFile(
                    locale=locale, path=file_path, data=data
                )
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load {locale}.json: {e}")

        return locale_files

    def load_single(self, locale: str) -> Optional[Dict]:
        """Load a single locale file."""
        locales = self.discover_locales()
        if locale not in locales:
            return None

        locale_file = self.load().get(locale)
        return locale_file.data if locale_file else None
