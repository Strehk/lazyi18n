"""
Core module initialization.
"""

from .loader import TranslationFileLoader, LocaleFile
from .flatten import flatten_json, unflatten_json, get_nested_value, set_nested_value
from .analyzer import TranslationGapAnalyzer, TranslationGap
from .writer import TranslationWriter
from .project import TranslationProject, ProjectChange

__all__ = [
    "TranslationFileLoader",
    "LocaleFile",
    "flatten_json",
    "unflatten_json",
    "get_nested_value",
    "set_nested_value",
    "TranslationGapAnalyzer",
    "TranslationGap",
    "TranslationWriter",
    "TranslationProject",
    "ProjectChange",
]
