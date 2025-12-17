"""
Machine translation support for lazyi18n.
Currently supports Google Translate API via deep-translator.
"""

from typing import Optional, Dict
from deep_translator import GoogleTranslator


class TranslationError(Exception):
    """Raised when translation fails."""

    pass


class Translator:
    """Handles machine translation for missing keys."""

    def __init__(self):
        """
        Initialize translator.
        """
        pass

    def translate(
        self, text: str, source_locale: str, target_locale: str
    ) -> Optional[str]:
        """
        Translate text from source locale to target locale.
        
        Args:
            text: Text to translate
            source_locale: Source language code (e.g., 'en')
            target_locale: Target language code (e.g., 'de')
            
        Returns:
            Translated text or None if translation fails
        """
        if not text:
            return None

        try:
            # Convert locale codes to language codes (e.g., 'en-US' -> 'en')
            src_lang = source_locale.split("-")[0].lower()
            dest_lang = target_locale.split("-")[0].lower()
            
            translator = GoogleTranslator(source=src_lang, target=dest_lang)
            return translator.translate(text)
        except Exception as e:
            raise TranslationError(f"Translation failed: {e}")

    def detect_source_locale(self, project, key: str) -> Optional[str]:
        """
        Detect the best source locale for a key.
        Returns the first locale that has a value for the key.
        
        Args:
            project: TranslationProject instance
            key: Translation key
            
        Returns:
            Locale code or None if key not found in any locale
        """
        for locale in project.get_locales():
            value = project.get_key_value(locale, key)
            if value:
                return locale
        return None

    def translate_missing(
        self,
        project,
        key: str,
        source_locale: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Translate a key for all missing locales.
        
        Args:
            project: TranslationProject instance
            key: Translation key to translate
            source_locale: Source locale to translate from. If None, auto-detect.
            
        Returns:
            Dictionary mapping locale -> translated text for missing locales
        """
        # Auto-detect source locale if not provided
        if not source_locale:
            source_locale = self.detect_source_locale(project, key)
            if not source_locale:
                raise TranslationError(f"No source text found for key: {key}")

        # Get source text
        source_text = project.get_key_value(source_locale, key)
        if not source_text:
            raise TranslationError(f"No text found in {source_locale} for key: {key}")

        # Find missing locales
        gaps = project.get_gaps()
        missing_locales = []
        if key in gaps:
            missing_locales = gaps[key].missing_in

        # Translate for each missing locale
        translations = {}
        for target_locale in missing_locales:
            try:
                translated = self.translate(source_text, source_locale, target_locale)
                if translated:
                    translations[target_locale] = translated
            except TranslationError as e:
                print(f"Warning: Failed to translate {key} to {target_locale}: {e}")

        return translations

    def translate_all_missing(self, project, source_locale: Optional[str] = None):
        """
        Translate all missing keys across all locales.
        
        Args:
            project: TranslationProject instance
            source_locale: Preferred source locale. If None, auto-detect per key.
            
        Returns:
            Dictionary mapping (locale, key) -> translated text
        """
        gaps = project.get_gaps()
        all_translations = {}

        for key, gap in gaps.items():
            try:
                translations = self.translate_missing(project, key, source_locale)
                for locale, text in translations.items():
                    all_translations[(locale, key)] = text
            except TranslationError as e:
                print(f"Warning: Failed to translate {key}: {e}")

        return all_translations
