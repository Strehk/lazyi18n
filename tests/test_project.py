"""Pytest tests for core/project.py"""

import pytest
from core.project import TranslationProject


class TestTranslationProject:
    """Test TranslationProject class."""

    def test_load(self, temp_translations):
        """Test loading translations."""
        project = TranslationProject(temp_translations)
        success = project.load()

        assert success is True
        locales = project.get_locales()
        assert "en" in locales
        assert "de" in locales

    def test_get_all_keys(self, temp_translations):
        """Test getting all keys across locales."""
        project = TranslationProject(temp_translations)
        project.load()
        keys = project.get_all_keys()

        expected_keys = {"auth.login", "auth.logout", "dashboard.welcome"}
        assert set(keys) == expected_keys

    def test_get_key_value(self, temp_translations):
        """Test getting value for specific key and locale."""
        project = TranslationProject(temp_translations)
        project.load()

        value = project.get_key_value("en", "auth.login")
        assert value == "Sign In"

        value = project.get_key_value("de", "auth.login")
        assert value == "Anmelden"

    def test_set_key_value(self, temp_translations):
        """Test setting value for specific key and locale."""
        project = TranslationProject(temp_translations)
        project.load()

        success = project.set_key_value("de", "auth.logout", "Abmelden")
        assert success is True

        value = project.get_key_value("de", "auth.logout")
        assert value == "Abmelden"

    def test_get_gaps(self, temp_translations):
        """Test gap detection."""
        project = TranslationProject(temp_translations)
        project.load()
        gaps = project.get_gaps()

        # auth.logout is missing in de
        assert "auth.logout" in gaps
        gap = gaps["auth.logout"]
        assert gap.missing_in == ["de"]

    def test_get_coverage(self, temp_translations):
        """Test coverage calculation."""
        project = TranslationProject(temp_translations)
        project.load()
        coverage = project.get_coverage()

        assert coverage["en"] == 100.0
        # de has 2 out of 3 keys
        assert coverage["de"] == pytest.approx(66.67, abs=0.1)

    def test_unsaved_changes_tracking(self, temp_translations):
        """Test tracking of unsaved changes."""
        project = TranslationProject(temp_translations)
        project.load()

        assert project.has_unsaved_changes() is False

        project.set_key_value("de", "auth.logout", "Abmelden")

        assert project.has_unsaved_changes() is True
        assert "de" in project.get_unsaved_locales()

    def test_save(self, temp_translations):
        """Test saving changes to disk."""
        project = TranslationProject(temp_translations)
        project.load()

        project.set_key_value("de", "auth.logout", "Abmelden")
        success = project.save()
        assert success is True

        # Verify changes were written
        import json

        with open(temp_translations / "de.json", "r") as f:
            saved_data = json.load(f)

        assert saved_data["auth"]["logout"] == "Abmelden"

        # Unsaved changes should be cleared
        assert project.has_unsaved_changes() is False

    def test_reload(self, temp_translations):
        """Test reloading from disk."""
        project = TranslationProject(temp_translations)
        project.load()

        # Make unsaved change
        project.set_key_value("de", "auth.logout", "Temp")
        assert project.has_unsaved_changes() is True

        # Reload should discard changes
        success = project.reload()
        assert success is True
        assert project.has_unsaved_changes() is False

        # Value should be reset
        value = project.get_key_value("de", "auth.logout")
        assert value is None
