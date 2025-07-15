"""Unit tests for the write_file tool functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
# Import the functions we want to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_file_server.main import (
    write_file as write_file_tool, 
    validate_and_sanitize_path
)

# Access the actual function from the FastMCP tool object
write_file = write_file_tool.fn


class TestWriteFile:
    """Test cases for the write_file tool function."""
    
    def test_write_new_file_success(self):
        """Test successful creation of a new file."""
        test_content = "Hello, World!\nThis is a test file."
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            
            result = write_file(str(file_path), test_content)
            
            # Check return value
            assert isinstance(result, str)
            assert "Successfully created file" in result
            
            # Check file was actually created with correct content
            assert file_path.exists()
            assert file_path.read_text(encoding='utf-8') == test_content
    
    def test_write_overwrite_existing_file_success(self):
        """Test successful overwriting of an existing file."""
        original_content = "Original content"
        new_content = "New content that replaces the original"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            
            # Create original file
            file_path.write_text(original_content, encoding='utf-8')
            assert file_path.read_text(encoding='utf-8') == original_content
            
            # Overwrite the file
            result = write_file(str(file_path), new_content)
            
            # Check return value
            assert isinstance(result, str)
            assert "Successfully overwrote file" in result
            
            # Check file was overwritten with new content
            assert file_path.exists()
            assert file_path.read_text(encoding='utf-8') == new_content
    
    def test_write_file_with_directory_creation(self):
        """Test writing file with automatic parent directory creation."""
        test_content = "Content in nested directory"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested path that doesn't exist
            file_path = Path(temp_dir) / "nested" / "deep" / "test.txt"
            
            # Ensure parent directories don't exist
            assert not file_path.parent.exists()
            
            result = write_file(str(file_path), test_content)
            
            # Check return value
            assert isinstance(result, str)
            assert "Successfully created file" in result
            
            # Check file and directories were created
            assert file_path.exists()
            assert file_path.parent.exists()
            assert file_path.read_text(encoding='utf-8') == test_content
    
    def test_write_empty_content(self):
        """Test writing empty content to a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "empty.txt"
            
            result = write_file(str(file_path), "")
            
            # Check return value
            assert isinstance(result, str)
            assert "Successfully created file" in result
            
            # Check file was created with empty content
            assert file_path.exists()
            assert file_path.read_text(encoding='utf-8') == ""
    
    def test_write_file_with_unicode_content(self):
        """Test writing file with unicode and special characters."""
        test_content = "Special chars: áéíóú ñ 中文 🚀 \n\t"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "unicode.txt"
            
            result = write_file(str(file_path), test_content)
            
            # Check return value
            assert isinstance(result, str)
            assert "Successfully created file" in result
            
            # Check file content
            assert file_path.exists()
            assert file_path.read_text(encoding='utf-8') == test_content
    
    def test_write_to_directory_raises_error(self):
        """Test that trying to write to an existing directory raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError) as exc_info:
                write_file(temp_dir, "content")
            assert "Cannot write to directory" in str(exc_info.value)
    
    def test_write_file_permission_error_parent_directory(self):
        """Test handling of permission errors when creating parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory with no write permissions
            restricted_dir = Path(temp_dir) / "restricted"
            restricted_dir.mkdir()
            os.chmod(restricted_dir, 0o444)  # Read-only
            
            file_path = restricted_dir / "nested" / "test.txt"
            
            try:
                with pytest.raises(ValueError) as exc_info:
                    write_file(str(file_path), "content")
                # The error could be either during directory creation or file writing
                # Both are permission-related, so we check for permission denied
                assert ("Permission denied" in str(exc_info.value) or 
                        "Unexpected error" in str(exc_info.value))
            finally:
                # Restore permissions for cleanup
                os.chmod(restricted_dir, 0o755)
    
    def test_write_file_permission_error_file_write(self):
        """Test handling of permission errors when writing to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "readonly.txt"
            
            # Create file and make it read-only
            file_path.write_text("original", encoding='utf-8')
            os.chmod(file_path, 0o444)  # Read-only
            
            try:
                with pytest.raises(ValueError) as exc_info:
                    write_file(str(file_path), "new content")
                assert "Permission denied writing file" in str(exc_info.value)
            finally:
                # Restore permissions for cleanup
                os.chmod(file_path, 0o644)
    
    def test_write_file_invalid_path_parameter(self):
        """Test handling of invalid path parameters."""
        with pytest.raises(ValueError) as exc_info:
            write_file("", "content")
        assert "cannot be empty" in str(exc_info.value)
    
    def test_write_file_null_byte_in_path(self):
        """Test handling of paths with null bytes."""
        with pytest.raises(ValueError) as exc_info:
            write_file("test\x00.txt", "content")
        assert "Invalid characters" in str(exc_info.value)
    
    def test_write_file_large_content(self):
        """Test writing large content to file."""
        # Create content that's reasonably large (1MB)
        large_content = "A" * (1024 * 1024)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "large.txt"
            
            result = write_file(str(file_path), large_content)
            
            # Check return value
            assert isinstance(result, str)
            assert "Successfully created file" in result
            
            # Check file content
            assert file_path.exists()
            assert file_path.read_text(encoding='utf-8') == large_content
    
    def test_write_file_with_newlines_and_tabs(self):
        """Test writing content with various whitespace characters."""
        test_content = "Line 1\nLine 2\r\nLine 3\tTabbed\n\n\tMixed whitespace"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "whitespace.txt"
            
            result = write_file(str(file_path), test_content)
            
            # Check return value
            assert isinstance(result, str)
            assert "Successfully created file" in result
            
            # Check file content - note that Python's write_text may normalize line endings
            assert file_path.exists()
            written_content = file_path.read_text(encoding='utf-8')
            # Check that the essential content is preserved (tabs and basic structure)
            assert "Line 1" in written_content
            assert "Line 2" in written_content  
            assert "Line 3\tTabbed" in written_content
            assert "\tMixed whitespace" in written_content
    
    def test_write_file_absolute_path(self):
        """Test writing file using absolute path."""
        test_content = "Content with absolute path"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir).resolve() / "absolute.txt"
            
            result = write_file(str(file_path), test_content)
            
            # Check return value
            assert isinstance(result, str)
            assert "Successfully created file" in result
            
            # Check file content
            assert file_path.exists()
            assert file_path.read_text(encoding='utf-8') == test_content
    
    def test_write_file_relative_path_with_dots(self):
        """Test writing file using relative path with dot notation."""
        test_content = "Content with relative path"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for relative path test
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                file_path = "./subdir/../test.txt"
                
                result = write_file(file_path, test_content)
                
                # Check return value
                assert isinstance(result, str)
                assert "Successfully created file" in result
                
                # Check file content
                actual_path = Path(temp_dir) / "test.txt"
                assert actual_path.exists()
                assert actual_path.read_text(encoding='utf-8') == test_content
            finally:
                os.chdir(original_cwd)
    
    def test_write_file_creates_intermediate_directories_deeply_nested(self):
        """Test creating deeply nested directory structure."""
        test_content = "Deep nesting test"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create very deep nesting
            file_path = Path(temp_dir) / "a" / "b" / "c" / "d" / "e" / "f" / "deep.txt"
            
            result = write_file(str(file_path), test_content)
            
            # Check return value
            assert isinstance(result, str)
            assert "Successfully created file" in result
            
            # Check file and all intermediate directories were created
            assert file_path.exists()
            assert file_path.read_text(encoding='utf-8') == test_content
            
            # Verify all intermediate directories exist
            current = file_path.parent
            while current != Path(temp_dir):
                assert current.exists()
                assert current.is_dir()
                current = current.parent


if __name__ == "__main__":
    pytest.main([__file__])