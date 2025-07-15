"""Unit tests for the read_file tool functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
# Import the functions we want to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_file_server.main import (
    read_file as read_file_tool, 
    validate_and_sanitize_path, 
    is_binary_file
)

# Access the actual function from the FastMCP tool object
read_file = read_file_tool.fn


class TestValidateAndSanitizePath:
    """Test cases for path validation and sanitization."""
    
    def test_valid_relative_path(self):
        """Test validation of valid relative paths."""
        path = validate_and_sanitize_path("test.txt")
        assert isinstance(path, Path)
        assert path.name == "test.txt"
    
    def test_valid_absolute_path(self):
        """Test validation of valid absolute paths."""
        path = validate_and_sanitize_path("/tmp/test.txt")
        assert isinstance(path, Path)
        assert path.is_absolute()
    
    def test_empty_path_raises_error(self):
        """Test that empty paths raise appropriate error."""
        with pytest.raises(ValueError) as exc_info:
            validate_and_sanitize_path("")
        assert "cannot be empty" in str(exc_info.value)
    
    def test_whitespace_only_path_raises_error(self):
        """Test that whitespace-only paths raise appropriate error."""
        with pytest.raises(ValueError) as exc_info:
            validate_and_sanitize_path("   ")
        assert "cannot be empty" in str(exc_info.value)
    
    def test_null_byte_in_path_raises_error(self):
        """Test that paths with null bytes raise appropriate error."""
        with pytest.raises(ValueError) as exc_info:
            validate_and_sanitize_path("test\x00.txt")
        assert "Invalid characters" in str(exc_info.value)
    
    def test_path_traversal_logged_but_allowed(self):
        """Test that path traversal attempts are logged but allowed."""
        # This should not raise an error but should be logged
        path = validate_and_sanitize_path("../test.txt")
        assert isinstance(path, Path)


class TestIsBinaryFile:
    """Test cases for binary file detection."""
    
    def test_text_file_detection(self):
        """Test that text files are correctly identified as non-binary."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a text file with normal content.")
            temp_path = Path(f.name)
        
        try:
            assert not is_binary_file(temp_path)
        finally:
            temp_path.unlink()
    
    def test_binary_file_detection(self):
        """Test that binary files are correctly identified."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
            # Write some binary content with null bytes
            f.write(b'\x00\x01\x02\x03\x04\x05')
            temp_path = Path(f.name)
        
        try:
            assert is_binary_file(temp_path)
        finally:
            temp_path.unlink()
    
    def test_empty_file_detection(self):
        """Test that empty files are treated as text files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Create empty file
            temp_path = Path(f.name)
        
        try:
            assert not is_binary_file(temp_path)
        finally:
            temp_path.unlink()
    
    def test_nonexistent_file_treated_as_binary(self):
        """Test that non-existent files are treated as binary for safety."""
        nonexistent_path = Path("/nonexistent/file.txt")
        assert is_binary_file(nonexistent_path)


class TestReadFile:
    """Test cases for the read_file tool function."""
    
    def test_read_text_file_success(self):
        """Test successful reading of a text file."""
        test_content = "Hello, World!\nThis is a test file."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            result = read_file(str(temp_path))
            assert isinstance(result, str)
            assert result == test_content
        finally:
            temp_path.unlink()
    
    def test_read_nonexistent_file_raises_error(self):
        """Test that reading non-existent file raises appropriate error."""
        with pytest.raises(ValueError) as exc_info:
            read_file("/nonexistent/file.txt")
        assert "File not found" in str(exc_info.value)
    
    def test_read_directory_raises_error(self):
        """Test that trying to read a directory raises appropriate error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError) as exc_info:
                read_file(temp_dir)
            assert "not a file" in str(exc_info.value)
    
    def test_read_binary_file_raises_error(self):
        """Test that reading binary file raises appropriate error."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
            f.write(b'\x00\x01\x02\x03Binary content')
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                read_file(str(temp_path))
            assert "binary file" in str(exc_info.value)
        finally:
            temp_path.unlink()
    
    def test_read_file_with_unicode_decode_error(self):
        """Test handling of files that can't be decoded as UTF-8."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            # Write invalid UTF-8 sequence that contains null bytes (will be caught as binary)
            f.write(b'\xff\xfe\x00\x00Invalid UTF-8')
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                read_file(str(temp_path))
            # This will be caught as binary file due to null bytes
            assert "binary file" in str(exc_info.value)
        finally:
            temp_path.unlink()
    
    def test_read_file_with_pure_unicode_decode_error(self):
        """Test handling of files with invalid UTF-8 but no null bytes."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            # Write invalid UTF-8 sequence without null bytes
            f.write(b'\xff\xfeInvalid UTF-8 without null bytes')
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                read_file(str(temp_path))
            # This should be caught as UTF-8 decode error since no null bytes
            assert "UTF-8" in str(exc_info.value)
        finally:
            temp_path.unlink()
    
    def test_read_file_permission_error(self):
        """Test handling of permission errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            # Remove read permissions
            os.chmod(temp_path, 0o000)
            
            with pytest.raises(ValueError) as exc_info:
                read_file(str(temp_path))
            # The binary file detection will fail with permission error first
            # which gets re-raised, so we expect permission denied or binary file error
            assert ("Permission denied" in str(exc_info.value) or 
                    "binary file" in str(exc_info.value))
        finally:
            # Restore permissions and cleanup
            os.chmod(temp_path, 0o644)
            temp_path.unlink()
    
    def test_read_empty_file(self):
        """Test reading an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Create empty file
            temp_path = Path(f.name)
        
        try:
            result = read_file(str(temp_path))
            assert isinstance(result, str)
            assert result == ""
        finally:
            temp_path.unlink()
    
    def test_read_file_with_special_characters(self):
        """Test reading file with special characters and unicode."""
        test_content = "Special chars: áéíóú ñ 中文 🚀 \n\t"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            result = read_file(str(temp_path))
            assert result == test_content
        finally:
            temp_path.unlink()
    
    def test_read_file_invalid_path_parameter(self):
        """Test handling of invalid path parameters."""
        with pytest.raises(ValueError) as exc_info:
            read_file("")
        assert "cannot be empty" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])