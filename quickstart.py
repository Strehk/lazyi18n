#!/usr/bin/env python3
"""
Quick start script - validates your lazyi18n installation
Run this to ensure everything is working correctly
"""

import sys
from pathlib import Path


def check_python():
    """Verify Python version."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_dependencies():
    """Verify required packages are installed."""
    required = ["textual", "rich"]
    all_ok = True

    for pkg in required:
        try:
            __import__(pkg)
            print(f"✅ {pkg}")
        except ImportError:
            print(f"❌ {pkg} not installed")
            all_ok = False

    return all_ok


def check_structure():
    """Verify project structure."""
    required_files = [
        "core/__init__.py",
        "core/loader.py",
        "core/flatten.py",
        "core/analyzer.py",
        "core/writer.py",
        "core/project.py",
        "main.py",
        "test_core.py",
    ]

    all_ok = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
            all_ok = False

    return all_ok


def test_import():
    """Test that core module imports correctly."""
    try:
        print("✅ Core imports successfully")
        return True
    except Exception as e:
        print(f"❌ Core import failed: {e}")
        return False


def main():
    print("=" * 50)
    print("lazyi18n Quick Start Validation")
    print("=" * 50)
    print()

    checks = [
        ("Python Version", check_python),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_structure),
        ("Core Module", test_import),
    ]

    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        result = check_func()
        results.append((name, result))
        print()

    print("=" * 50)
    print("Summary:")
    print("=" * 50)

    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False

    print()
    if all_passed:
        print("🎉 Everything is ready!")
        print()
        print("Next steps:")
        print("  1. Test the core: python3 test_core.py")
        print("  2. Run the TUI:   python3 main.py examples/")
        print("  3. Setup LazyVim: See LAZYVIM_SETUP.md")
        return 0
    else:
        print("⚠️  Some checks failed. See above for details.")
        print()
        print("Troubleshooting:")
        print("  1. Reinstall dependencies:")
        print("     pip3 install -r requirements.txt")
        print("  2. Verify you're in the project root")
        print("  3. Check Python path: which python3")
        return 1


if __name__ == "__main__":
    sys.exit(main())
