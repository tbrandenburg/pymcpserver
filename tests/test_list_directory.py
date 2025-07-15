"""Unit tests for the list_directory functionality."""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.mcp_file_server.main import (
    list_directory as list_directory_tool, 
    validate_and_sanitize_path
)

# Access the actual function from the FastMCP tool object
list_directory = list_directory_tool.fn


class TestListDirectory:
    """Test cases for list_directory function."""

    @pytest.fixture
    def temp_dir_with_files(self):
        """Create a temporary directory with test files and subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.txt").write_text("Content of file 1")
            (temp_path / "file2.py").write_text("print('Hello World')")
            
            # Create a subdirectory
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "nested_file.md").write_text("# Nested File")
            
            # Create an empty file
            (temp_path / "empty.txt").touch()
            
            yield temp_path

    def test_list_directory_success(self, temp_dir_with_files):
        """Test successful directory listing."""
        result = list_directory(str(temp_dir_with_files))
        
        # Parse the JSON response
        response_data = json.loads(result)
        
        assert "directory" in response_data
        assert "entries" in response_data
        assert "total_entries" in response_data
        # Path resolution may add /private prefix on macOS, so check resolved path
        assert Path(response_data["directory"]).resolve() == Path(temp_dir_with_files).resolve()
        assert response_data["total_entries"] == 4  # 3 files + 1 subdirectory
        
        # Check entries are sorted by name
        entry_names = [entry["name"] for entry in response_data["entries"]]
        assert entry_names == sorted(entry_names, key=str.lower)
        
        # Verify entry structure
        for entry in response_data["entries"]:
            assert "name" in entry
            assert "type" in entry
            assert "size" in entry
            assert "modified" in entry
            assert "path" in entry
            assert entry["type"] in ["file", "directory"]
            
            # Files should have size, directories should have None
            if entry["type"] == "file":
                assert isinstance(entry["size"], int)
                assert entry["size"] >= 0
            else:
                assert entry["size"] is None
            
            # All entries should have modification time
            assert entry["modified"] is not None
            # Verify ISO format timestamp
            datetime.fromisoformat(entry["modified"])

    def test_list_directory_empty_directory(self):
        """Test listing an empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = list_directory(temp_dir)
            
            response_data = json.loads(result)
            
            assert response_data["total_entries"] == 0
            assert response_data["entries"] == []
            # Path resolution may add /private prefix on macOS, so check resolved path
            assert Path(response_data["directory"]).resolve() == Path(temp_dir).resolve()

    def test_list_directory_not_found(self):
        """Test listing a non-existent directory."""
        non_existent_path = "/path/that/does/not/exist"
        
        with pytest.raises(ValueError) as exc_info:
            list_directory(non_existent_path)
        
        assert "Directory not found" in str(exc_info.value)

    def test_list_directory_is_file(self, temp_dir_with_files):
        """Test listing a path that points to a file, not a directory."""
        file_path = temp_dir_with_files / "file1.txt"
        
        with pytest.raises(ValueError) as exc_info:
            list_directory(str(file_path))
        
        assert "Path is not a directory" in str(exc_info.value)

    def test_list_directory_empty_path(self):
        """Test listing with empty directory path."""
        with pytest.raises(ValueError) as exc_info:
            list_directory("")
        
        assert "File path cannot be empty" in str(exc_info.value)

    def test_list_directory_invalid_path(self):
        """Test listing with invalid path characters."""
        with pytest.raises(ValueError) as exc_info:
            list_directory("path/with\x00null/byte")
        
        assert "Invalid characters in file path" in str(exc_info.value)

    def test_list_directory_permission_denied(self):
        """Test listing a directory without permission."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a subdirectory and remove read permissions
            restricted_dir = temp_path / "restricted"
            restricted_dir.mkdir()
            
            try:
                # Remove read permission (this might not work on all systems)
                restricted_dir.chmod(0o000)
                
                with pytest.raises(ValueError) as exc_info:
                    list_directory(str(restricted_dir))
                
                assert "Permission denied listing directory" in str(exc_info.value)
                
            finally:
                # Restore permissions for cleanup
                try:
                    restricted_dir.chmod(0o755)
                except:
                    pass

    def test_list_directory_with_permission_errors_on_entries(self, temp_dir_with_files):
        """Test listing directory where some entries have permission issues."""
        # Mock stat to raise PermissionError for one entry
        original_stat = Path.stat
        
        def mock_stat(self, *args, **kwargs):
            if self.name == "file1.txt":
                raise PermissionError("Access denied")
            return original_stat(self, *args, **kwargs)
        
        with patch.object(Path, 'stat', mock_stat):
            result = list_directory(str(temp_dir_with_files))
            
            response_data = json.loads(result)
            
            # Should still return all entries, but problematic ones have error info
            assert response_data["total_entries"] == 4
            
            # Find the entry with permission error
            error_entry = next(
                (entry for entry in response_data["entries"] if entry["name"] == "file1.txt"),
                None
            )
            assert error_entry is not None
            assert error_entry["type"] == "unknown"
            assert error_entry["size"] is None
            assert error_entry["modified"] is None
            assert "error" in error_entry
            assert "Permission denied or access error" in error_entry["error"]

    def test_list_directory_file_types_and_sizes(self, temp_dir_with_files):
        """Test that file types and sizes are correctly identified."""
        result = list_directory(str(temp_dir_with_files))
        response_data = json.loads(result)
        
        # Find specific entries to verify
        entries_by_name = {entry["name"]: entry for entry in response_data["entries"]}
        
        # Check file entries
        file1_entry = entries_by_name["file1.txt"]
        assert file1_entry["type"] == "file"
        assert file1_entry["size"] == len("Content of file 1")
        
        empty_file_entry = entries_by_name["empty.txt"]
        assert empty_file_entry["type"] == "file"
        assert empty_file_entry["size"] == 0
        
        # Check directory entry
        subdir_entry = entries_by_name["subdir"]
        assert subdir_entry["type"] == "directory"
        assert subdir_entry["size"] is None

    def test_list_directory_path_resolution(self):
        """Test that relative paths are properly resolved."""
        # Use current directory
        result = list_directory(".")
        response_data = json.loads(result)
        
        # Should resolve to absolute path
        assert Path(response_data["directory"]).is_absolute()
        
        # All entry paths should be absolute
        for entry in response_data["entries"]:
            assert Path(entry["path"]).is_absolute()

    def test_list_directory_sorting(self, temp_dir_with_files):
        """Test that directory entries are sorted case-insensitively."""
        # Create files with mixed case names
        (temp_dir_with_files / "Zebra.txt").write_text("zebra")
        (temp_dir_with_files / "apple.txt").write_text("apple")
        (temp_dir_with_files / "Banana.txt").write_text("banana")
        
        result = list_directory(str(temp_dir_with_files))
        response_data = json.loads(result)
        
        entry_names = [entry["name"] for entry in response_data["entries"]]
        expected_sorted = sorted(entry_names, key=str.lower)
        
        assert entry_names == expected_sorted

    def test_list_directory_unexpected_error(self, temp_dir_with_files):
        """Test handling of unexpected errors during directory listing."""
        # Mock iterdir to raise an unexpected exception
        with patch.object(Path, 'iterdir', side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(ValueError) as exc_info:
                list_directory(str(temp_dir_with_files))
            
            assert "Unexpected error listing directory" in str(exc_info.value)

    def test_list_directory_json_structure(self, temp_dir_with_files):
        """Test that the JSON response has the correct structure."""
        result = list_directory(str(temp_dir_with_files))
        response_data = json.loads(result)
        
        # Verify top-level structure
        required_keys = {"directory", "entries", "total_entries"}
        assert set(response_data.keys()) == required_keys
        
        # Verify entries structure
        for entry in response_data["entries"]:
            required_entry_keys = {"name", "type", "size", "modified", "path"}
            assert required_entry_keys.issubset(set(entry.keys()))
            
            # Verify data types
            assert isinstance(entry["name"], str)
            assert isinstance(entry["type"], str)
            assert entry["size"] is None or isinstance(entry["size"], int)
            assert isinstance(entry["modified"], str)
            assert isinstance(entry["path"], str)