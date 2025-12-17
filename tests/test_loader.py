"""Pytest tests for core/loader.py"""

import pytest
from core.loader import TranslationFileLoader


class TestTranslationFileLoader:
    """Test TranslationFileLoader class."""

    def test_discover_locales(self, temp_translations):
        """Test discovering locale files."""
        loader = TranslationFileLoader(temp_translations)
        locales = loader.discover_locales()

        assert "en" in locales
        assert "de" in locales
        assert len(locales) == 2

    def test_load_all_locales(self, temp_translations):
        """Test loading all locale files."""
        loader = TranslationFileLoader(temp_translations)
        locale_files = loader.load()

        assert "en" in locale_files
        assert "de" in locale_files
        assert locale_files["en"].data["auth"]["login"] == "Sign In"
        assert locale_files["de"].data["auth"]["login"] == "Anmelden"

    def test_load_single_locale(self, temp_translations):
        """Test loading a single locale."""
        loader = TranslationFileLoader(temp_translations)
        data = loader.load_single("en")

        assert data["auth"]["login"] == "Sign In"

    def test_invalid_json(self, temp_translations):
        """Test handling of invalid JSON."""
        # Create invalid JSON file
        (temp_translations / "invalid.json").write_text("{invalid json")

        loader = TranslationFileLoader(temp_translations)
        locale_files = loader.load()

        # Should load valid files and skip invalid
        assert "en" in locale_files
        assert "de" in locale_files
        assert "invalid" not in locale_files

    def test_nonexistent_directory(self):
        """Test handling of non-existent directory."""
        with pytest.raises(FileNotFoundError):
            TranslationFileLoader("/nonexistent/path")
