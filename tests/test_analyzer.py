"""Pytest tests for core/analyzer.py"""

from core.analyzer import TranslationGapAnalyzer


class TestTranslationGapAnalyzer:
    """Test TranslationGapAnalyzer class."""

    def test_no_gaps(self):
        """Test when all locales have all keys."""
        locale_data = {
            "en": {"auth.login": "Sign In", "auth.logout": "Sign Out"},
            "de": {"auth.login": "Anmelden", "auth.logout": "Abmelden"},
        }
        gaps = TranslationGapAnalyzer.analyze(locale_data)
        assert gaps == {}

    def test_one_missing_key(self):
        """Test when one locale is missing a key."""
        locale_data = {
            "en": {"auth.login": "Sign In", "auth.logout": "Sign Out"},
            "de": {"auth.login": "Anmelden"},  # Missing logout
        }
        gaps = TranslationGapAnalyzer.analyze(locale_data)

        assert "auth.logout" in gaps
        gap = gaps["auth.logout"]
        assert gap.missing_in == ["de"]
        assert gap.present_in == ["en"]

    def test_multiple_missing_keys(self):
        """Test multiple missing keys across locales."""
        locale_data = {
            "en": {"key1": "v1", "key2": "v2", "key3": "v3"},
            "de": {"key1": "v1", "key3": "v3"},  # Missing key2
            "fr": {"key1": "v1"},  # Missing key2, key3
        }
        gaps = TranslationGapAnalyzer.analyze(locale_data)

        assert len(gaps) == 2  # key2 and key3 have gaps
        assert "key2" in gaps
        assert "key3" in gaps

    def test_get_missing_keys_for_locale(self):
        """Test getting missing keys for specific locale."""
        locale_data = {
            "en": {"key1": "v1", "key2": "v2"},
            "de": {"key1": "v1"},
        }
        missing = TranslationGapAnalyzer.get_missing_keys_for_locale(locale_data, "de")
        assert missing == ["key2"]

    def test_get_complete_keys(self):
        """Test getting keys present in all locales."""
        locale_data = {
            "en": {"key1": "v1", "key2": "v2"},
            "de": {"key1": "v1"},
        }
        complete = TranslationGapAnalyzer.get_complete_keys(locale_data)
        assert complete == ["key1"]

    def test_coverage_percentage(self):
        """Test coverage percentage calculation."""
        locale_data = {
            "en": {"key1": "v1", "key2": "v2", "key3": "v3", "key4": "v4"},
            "de": {"key1": "v1", "key2": "v2"},  # 50% coverage
        }
        coverage = TranslationGapAnalyzer.get_coverage_percentage(locale_data)

        assert coverage["en"] == 100.0
        assert coverage["de"] == 50.0

    def test_empty_locale_data(self):
        """Test with empty locale data."""
        gaps = TranslationGapAnalyzer.analyze({})
        assert gaps == {}

        coverage = TranslationGapAnalyzer.get_coverage_percentage({})
        assert coverage == {}
