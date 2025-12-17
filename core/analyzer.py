"""
Gap analysis for translation files - identifies missing translations.
"""

from typing import Dict, Set, List
from dataclasses import dataclass


@dataclass
class TranslationGap:
    """Represents a missing translation."""

    key: str
    missing_in: List[str]  # Locales where this key is missing
    present_in: List[str]  # Locales where this key exists


class TranslationGapAnalyzer:
    """Analyzes translation gaps across multiple locales."""

    @staticmethod
    def analyze(locale_data: Dict[str, Dict]) -> Dict[str, TranslationGap]:
        """
        Analyze gaps in translations.

        Args:
            locale_data: {locale_name: flattened_dict, ...}

        Returns:
            Dictionary of gaps keyed by translation key
        """
        gaps = {}
        all_keys: Set[str] = set()

        # Collect all keys from all locales
        for locale, data in locale_data.items():
            all_keys.update(data.keys())

        # Find which locales have each key
        for key in all_keys:
            present_in = []
            missing_in = []

            for locale, data in locale_data.items():
                if key in data:
                    present_in.append(locale)
                else:
                    missing_in.append(locale)

            if missing_in:  # Only record if there's a gap
                gaps[key] = TranslationGap(
                    key=key,
                    missing_in=missing_in,
                    present_in=present_in,
                )

        return gaps

    @staticmethod
    def get_missing_keys_for_locale(
        locale_data: Dict[str, Dict],
        locale: str,
    ) -> List[str]:
        """Get all keys missing in a specific locale."""
        gaps = TranslationGapAnalyzer.analyze(locale_data)
        return [key for key, gap in gaps.items() if locale in gap.missing_in]

    @staticmethod
    def get_complete_keys(locale_data: Dict[str, Dict]) -> List[str]:
        """Get keys that exist in all locales."""
        gaps = TranslationGapAnalyzer.analyze(locale_data)
        all_keys = set()
        for data in locale_data.values():
            all_keys.update(data.keys())

        return [key for key in all_keys if key not in gaps]

    @staticmethod
    def get_coverage_percentage(locale_data: Dict[str, Dict]) -> Dict[str, float]:
        """Get translation coverage percentage per locale."""
        all_keys = set()
        for data in locale_data.values():
            all_keys.update(data.keys())

        if not all_keys:
            return {}

        coverage = {}
        for locale, data in locale_data.items():
            present = len([k for k in all_keys if k in data])
            coverage[locale] = (present / len(all_keys)) * 100

        return coverage
