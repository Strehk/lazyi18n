"""
Core data model - TranslationProject orchestrates everything.
"""

from pathlib import Path
from typing import Dict, Set, Optional
from dataclasses import dataclass

from .loader import TranslationFileLoader, LocaleFile
from .flatten import flatten_json, unflatten_json
from .analyzer import TranslationGapAnalyzer
from .writer import TranslationWriter


@dataclass
class ProjectChange:
    """Represents a single change made to a translation."""

    locale: str
    key: str
    old_value: Optional[str]
    new_value: Optional[str]


class TranslationProject:
    """
    Main orchestrator for translation file management.
    Manages loading, analyzing, modifying, and saving translation files.
    """

    def __init__(self, directory: Path | str):
        """Initialize project with a directory of translation files."""
        self.directory = Path(directory)
        self.loader = TranslationFileLoader(self.directory)
        self.writer = TranslationWriter(indent=2)

        # State
        self.locale_files: Dict[str, LocaleFile] = {}
        self.flattened: Dict[str, Dict] = {}
        self.changes: Dict[str, ProjectChange] = {}
        self.unsaved_changes: Set[str] = set()

    def load(self) -> bool:
        """Load all translation files."""
        try:
            self.locale_files = self.loader.load()
            self._flatten_all()
            return bool(self.locale_files)
        except Exception as e:
            print(f"Error loading translations: {e}")
            return False

    def _flatten_all(self) -> None:
        """Flatten all loaded locale files."""
        self.flattened = {}
        for locale, locale_file in self.locale_files.items():
            self.flattened[locale] = flatten_json(locale_file.data)

    def get_all_keys(self) -> set:
        """Get all translation keys across all locales."""
        all_keys = set()
        for data in self.flattened.values():
            all_keys.update(data.keys())
        return sorted(all_keys)

    def get_key_value(self, locale: str, key: str) -> Optional[str]:
        """Get the value of a key in a specific locale."""
        if locale not in self.flattened:
            return None
        return self.flattened[locale].get(key)

    def set_key_value(self, locale: str, key: str, value: str) -> bool:
        """
        Set the value of a key in a specific locale.
        Records the change for later saving.
        """
        if locale not in self.flattened:
            return False

        old_value = self.flattened[locale].get(key)
        self.flattened[locale][key] = value

        change_id = f"{locale}:{key}"
        self.changes[change_id] = ProjectChange(
            locale=locale,
            key=key,
            old_value=old_value,
            new_value=value,
        )
        self.unsaved_changes.add(locale)
        return True

    def delete_key_value(self, locale: str, key: str) -> bool:
        """Delete a translation value for a key in a specific locale."""
        if locale not in self.flattened:
            return False
        old_value = self.flattened[locale].get(key)
        if key in self.flattened[locale]:
            del self.flattened[locale][key]
        
        change_id = f"{locale}:{key}"
        self.changes[change_id] = ProjectChange(
            locale=locale,
            key=key,
            old_value=old_value,
            new_value=None,
        )
        self.unsaved_changes.add(locale)
        return True

    def discard_key_changes(self, key: str) -> bool:
        """
        Discard all unsaved changes for a specific key.
        Reverts values to their original state.
        """
        changes_to_discard = [
            (cid, change) for cid, change in self.changes.items() 
            if change.key == key
        ]
        
        if not changes_to_discard:
            return False
            
        for change_id, change in changes_to_discard:
            locale = change.locale
            
            # Revert value
            if change.old_value is None:
                # It was a new key, so remove it
                if locale in self.flattened and key in self.flattened[locale]:
                    del self.flattened[locale][key]
            else:
                # Restore old value
                if locale in self.flattened:
                    self.flattened[locale][key] = change.old_value
            
            # Remove change record
            del self.changes[change_id]
            
            # Check if locale still has changes
            locale_has_changes = any(c.locale == locale for c in self.changes.values())
            if not locale_has_changes:
                self.unsaved_changes.discard(locale)
                
        return True

    def get_gaps(self) -> Dict:
        """Get all translation gaps."""
        return TranslationGapAnalyzer.analyze(self.flattened)

    def get_coverage(self) -> Dict[str, float]:
        """Get translation coverage percentage per locale."""
        return TranslationGapAnalyzer.get_coverage_percentage(self.flattened)

    def get_locales(self) -> list:
        """Get list of all loaded locales."""
        return sorted(self.locale_files.keys())

    def get_changed_keys(self) -> Set[str]:
        """Get set of keys that have unsaved changes."""
        return {change.key for change in self.changes.values()}

    def save(self, locale: Optional[str] = None) -> bool:
        """
        Save changes to disk.

        Args:
            locale: If provided, only save this locale. Otherwise save all.

        Returns:
            True if successful
        """
        if not self.unsaved_changes:
            return True

        locales_to_save = [locale] if locale else list(self.unsaved_changes)
        all_success = True

        for loc in locales_to_save:
            if loc not in self.locale_files:
                continue

            # Unflatten back to nested structure
            nested_data = unflatten_json(self.flattened[loc])

            # Write to file
            locale_file = self.locale_files[loc]
            if self.writer.write_atomic(nested_data, locale_file.path):
                self.unsaved_changes.discard(loc)
                # Remove changes for this locale
                keys_to_remove = [k for k, v in self.changes.items() if v.locale == loc]
                for k in keys_to_remove:
                    del self.changes[k]
            else:
                all_success = False

        return all_success

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return bool(self.unsaved_changes)

    def get_unsaved_locales(self) -> list:
        """Get list of locales with unsaved changes."""
        return sorted(self.unsaved_changes)

    def reload(self) -> bool:
        """Reload all files from disk (discarding unsaved changes)."""
        self.changes.clear()
        self.unsaved_changes.clear()
        return self.load()
