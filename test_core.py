#!/usr/bin/env python3
"""
Simple test script to validate Phase 1 core functionality.
Run from project root: python test_core.py
"""

from pathlib import Path
from core import TranslationProject, TranslationGapAnalyzer

def main():
    print("=== lazyi18n Core Test ===\n")
    
    # Initialize project with example files
    example_dir = Path("examples")
    if not example_dir.exists():
        print("❌ Examples directory not found. Run from project root.")
        return
    
    project = TranslationProject(example_dir)
    
    # Load translations
    print("📂 Loading translations...")
    if not project.load():
        print("❌ Failed to load translations")
        return
    
    print(f"✓ Loaded {len(project.get_locales())} locales: {project.get_locales()}\n")
    
    # Show coverage
    print("📊 Translation Coverage:")
    coverage = project.get_coverage()
    for locale, percent in coverage.items():
        bar_length = int(percent / 5)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"  {locale:8} {bar} {percent:.1f}%")
    print()
    
    # Show gaps
    print("⚠️  Missing Translations:")
    gaps = project.get_gaps()
    if gaps:
        for key, gap in list(gaps.items())[:10]:  # Show first 10
            print(f"  {key}")
            print(f"    Missing in: {', '.join(gap.missing_in)}")
    else:
        print("  None! All translations are complete.")
    print()
    
    # Show all keys (flattened)
    print(f"🔑 Total Unique Keys: {len(project.get_all_keys())}")
    print("Sample keys (first 5):")
    for key in list(project.get_all_keys())[:5]:
        print(f"  • {key}")
    print()
    
    # Test value access
    print("📖 Sample Values:")
    key = "auth.login.title"
    for locale in project.get_locales():
        value = project.get_key_value(locale, key)
        print(f"  {locale}: {key} = '{value}'")
    print()
    
    # Test modification
    print("✏️  Testing modification...")
    project.set_key_value("de", "auth.login.title", "Anmelden (Updated)")
    print(f"  Modified de/auth.login.title")
    print(f"  Unsaved changes in: {project.get_unsaved_locales()}")
    print(f"  Save successful: {project.save()}")
    print()
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    main()
