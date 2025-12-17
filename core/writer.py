"""
Safe JSON writer - handles saving translation files with proper formatting.
"""

import json
from pathlib import Path
from typing import Dict, Any


class TranslationWriter:
    """Safely writes translation JSON files."""

    def __init__(self, indent: int = 2):
        """
        Initialize writer with formatting preferences.

        Args:
            indent: Number of spaces for JSON indentation
        """
        self.indent = indent

    def write(
        self,
        data: Dict[str, Any],
        path: Path | str,
        create_backup: bool = True,
    ) -> bool:
        """
        Write translation data to a JSON file.

        Args:
            data: Dictionary to write
            path: Path to write to
            create_backup: Whether to create a backup before writing

        Returns:
            True if successful, False otherwise
        """
        path = Path(path)

        try:
            # Create backup if requested and file exists
            if create_backup and path.exists():
                backup_path = path.with_suffix(".json.bak")
                with open(path, "r", encoding="utf-8") as f:
                    backup_data = f.read()
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(backup_data)

            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write JSON with formatting
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=self.indent,
                    ensure_ascii=False,
                    sort_keys=False,
                )
                f.write("\n")  # Add trailing newline

            return True

        except Exception as e:
            print(f"Error writing {path}: {e}")
            return False

    def write_atomic(
        self,
        data: Dict[str, Any],
        path: Path | str,
    ) -> bool:
        """
        Write with atomic operation (write to temp file, then move).
        Safer for preventing data loss if write is interrupted.

        Args:
            data: Dictionary to write
            path: Path to write to

        Returns:
            True if successful, False otherwise
        """
        import tempfile
        import shutil

        path = Path(path)

        try:
            # Create temporary file in same directory (same filesystem)
            temp_dir = path.parent
            temp_dir.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=temp_dir,
                suffix=".json",
                delete=False,
                encoding="utf-8",
            ) as temp_file:
                temp_path = Path(temp_file.name)
                json.dump(
                    data,
                    temp_file,
                    indent=self.indent,
                    ensure_ascii=False,
                )
                temp_file.write("\n")

            # Move temp file to final location
            shutil.move(str(temp_path), str(path))
            return True

        except Exception as e:
            print(f"Error writing {path} atomically: {e}")
            return False
