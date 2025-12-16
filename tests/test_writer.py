"""Pytest tests for core/writer.py"""

import pytest
import tempfile
import json
from pathlib import Path
from core.writer import TranslationWriter


class TestTranslationWriter:
    """Test TranslationWriter class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def writer(self):
        """Create writer instance."""
        return TranslationWriter(indent=2)
    
    def test_write_simple_dict(self, temp_dir, writer):
        """Test writing simple dictionary."""
        data = {"auth": {"login": "Sign In"}}
        file_path = temp_dir / "test.json"
        
        success = writer.write(data, file_path, create_backup=False)
        assert success is True
        
        # Verify content
        with open(file_path, "r") as f:
            loaded = json.load(f)
        assert loaded == data
    
    def test_write_creates_directory(self, temp_dir, writer):
        """Test that write creates parent directories."""
        data = {"key": "value"}
        file_path = temp_dir / "subdir" / "test.json"
        
        success = writer.write(data, file_path, create_backup=False)
        assert success is True
        assert file_path.exists()
    
    def test_backup_creation(self, temp_dir, writer):
        """Test that backup is created when enabled."""
        data = {"key": "value"}
        file_path = temp_dir / "test.json"
        
        # Write initial file
        writer.write(data, file_path, create_backup=False)
        
        # Write again with backup
        new_data = {"key": "new_value"}
        writer.write(new_data, file_path, create_backup=True)
        
        # Check backup exists
        backup_path = file_path.with_suffix(".json.bak")
        assert backup_path.exists()
        
        # Verify backup has old data
        with open(backup_path, "r") as f:
            backup_content = json.load(f)
        assert backup_content == data
    
    def test_write_atomic(self, temp_dir, writer):
        """Test atomic write operation."""
        data = {"auth": {"login": "Sign In"}}
        file_path = temp_dir / "test.json"
        
        success = writer.write_atomic(data, file_path)
        assert success is True
        
        # Verify content
        with open(file_path, "r") as f:
            loaded = json.load(f)
        assert loaded == data
    
    def test_formatting_preserved(self, temp_dir, writer):
        """Test that formatting (indentation) is preserved."""
        data = {"auth": {"login": "Sign In", "logout": "Sign Out"}}
        file_path = temp_dir / "test.json"
        
        writer.write(data, file_path, create_backup=False)
        
        # Read raw content to check formatting
        content = file_path.read_text()
        
        # Should have indentation
        assert "  " in content  # 2-space indent
        # Should have trailing newline
        assert content.endswith("\n")
