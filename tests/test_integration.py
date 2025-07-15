"""Integration tests for the MCP File Server.

These tests verify tool functionality, multi-tool workflows,
and error handling in the FastMCP implementation.
"""

import asyncio
import json
import tempfile
import pytest
from pathlib import Path
from typing import Any, Dict, List
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_file_server.main import (
    mcp,
    setup_logging, 
    read_file as read_file_tool,
    write_file as write_file_tool,
    list_directory as list_directory_tool
)

# Access the actual functions from the FastMCP tool objects
read_file = read_file_tool.fn
write_file = write_file_tool.fn
list_directory = list_directory_tool.fn


class TestMCPIntegration:
    """Integration tests for FastMCP tool functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with test files and directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            
            # Create test files
            (workspace / "test.txt").write_text("Hello, World!")
            (workspace / "data.json").write_text('{"key": "value"}')
            (workspace / "empty.txt").touch()
            
            # Create subdirectories
            subdir = workspace / "subdir"
            subdir.mkdir()
            (subdir / "nested.md").write_text("# Nested File")
            
            # Create binary file
            (workspace / "binary.bin").write_bytes(b'\x00\x01\x02\x03')
            
            yield workspace
    
    def test_server_initialization(self):
        """Test that FastMCP server initializes correctly."""
        # Verify server name
        assert mcp.name == "mcp-file-server"
        
        # Verify tools are registered (FastMCP automatically registers decorated functions)
        # We can't directly access the tools list in FastMCP, but we can test that the functions exist
        assert callable(read_file)
        assert callable(write_file)
        assert callable(list_directory)
    
    def test_read_file_tool_invocation(self, temp_workspace):
        """Test read_file tool invocation."""
        test_file = temp_workspace / "test.txt"
        
        # Test tool invocation directly
        result = read_file(str(test_file))
        
        assert result == "Hello, World!"
    
    def test_write_file_tool_invocation(self, temp_workspace):
        """Test write_file tool invocation."""
        new_file = temp_workspace / "new_file.txt"
        test_content = "This is new content"
        
        # Test tool invocation directly
        result = write_file(str(new_file), test_content)
        
        assert "Successfully created file" in result
        
        # Verify file was actually created
        assert new_file.exists()
        assert new_file.read_text() == test_content
    
    def test_list_directory_tool_invocation(self, temp_workspace):
        """Test list_directory tool invocation."""
        # Test tool invocation directly
        result = list_directory(str(temp_workspace))
        
        # Parse JSON response
        response_data = json.loads(result)
        assert "directory" in response_data
        assert "entries" in response_data
        assert "total_entries" in response_data
        
        # Should have our test files
        entry_names = {entry["name"] for entry in response_data["entries"]}
        expected_names = {"test.txt", "data.json", "empty.txt", "subdir", "binary.bin"}
        assert expected_names.issubset(entry_names)
    
    def test_multi_tool_workflow(self, temp_workspace):
        """Test a workflow that uses multiple tools in sequence."""
        # Step 1: List directory to see initial state
        list_result = list_directory(str(temp_workspace))
        initial_data = json.loads(list_result)
        initial_count = initial_data["total_entries"]
        
        # Step 2: Create a new file
        new_file_path = str(temp_workspace / "workflow_test.txt")
        write_content = "Content created in workflow"
        
        write_result = write_file(new_file_path, write_content)
        assert "Successfully created file" in write_result
        
        # Step 3: Read the file back to verify content
        read_result = read_file(new_file_path)
        assert read_result == write_content
        
        # Step 4: List directory again to verify file was added
        list_result2 = list_directory(str(temp_workspace))
        final_data = json.loads(list_result2)
        final_count = final_data["total_entries"]
        
        assert final_count == initial_count + 1
        
        # Verify the new file appears in the listing
        entry_names = {entry["name"] for entry in final_data["entries"]}
        assert "workflow_test.txt" in entry_names
        
        # Step 5: Overwrite the file with new content
        new_content = "Updated content in workflow"
        write_result2 = write_file(new_file_path, new_content)
        assert "Successfully overwrote file" in write_result2
        
        # Step 6: Read the updated content
        read_result2 = read_file(new_file_path)
        assert read_result2 == new_content
    
    def test_nested_directory_workflow(self, temp_workspace):
        """Test workflow with nested directory operations."""
        # Step 1: Create nested directory structure through file creation
        nested_file_path = str(temp_workspace / "deep" / "nested" / "structure" / "file.txt")
        content = "Deep nested content"
        
        write_result = write_file(nested_file_path, content)
        assert "Successfully created file" in write_result
        
        # Step 2: List the root directory to see new structure
        list_result = list_directory(str(temp_workspace))
        root_data = json.loads(list_result)
        entry_names = {entry["name"] for entry in root_data["entries"]}
        assert "deep" in entry_names
        
        # Step 3: Navigate through nested directories
        deep_dir = temp_workspace / "deep"
        list_deep = list_directory(str(deep_dir))
        deep_data = json.loads(list_deep)
        assert len(deep_data["entries"]) == 1
        assert deep_data["entries"][0]["name"] == "nested"
        assert deep_data["entries"][0]["type"] == "directory"
        
        # Step 4: Read the deeply nested file
        read_result = read_file(nested_file_path)
        assert read_result == content
    
    def test_error_propagation_file_operations(self, temp_workspace):
        """Test error propagation for file operation errors."""
        # Test reading non-existent file
        with pytest.raises(ValueError) as exc_info:
            read_file("/nonexistent/file.txt")
        
        assert "File not found" in str(exc_info.value)
        
        # Test reading binary file
        binary_file = temp_workspace / "binary.bin"
        with pytest.raises(ValueError) as exc_info:
            read_file(str(binary_file))
        
        assert "binary file" in str(exc_info.value)
        
        # Test listing non-existent directory
        with pytest.raises(ValueError) as exc_info:
            list_directory("/nonexistent/directory")
        
        assert "Directory not found" in str(exc_info.value)
    
    def test_error_propagation_invalid_paths(self):
        """Test error propagation for invalid path parameters."""
        # Test empty path
        with pytest.raises(ValueError) as exc_info:
            read_file("")
        
        assert "cannot be empty" in str(exc_info.value)
        
        # Test path with null bytes
        with pytest.raises(ValueError) as exc_info:
            write_file("test\x00.txt", "content")
        
        assert "Invalid characters" in str(exc_info.value)
    
    def test_concurrent_tool_operations(self, temp_workspace):
        """Test concurrent tool operations to verify thread safety."""
        # Create multiple files concurrently
        import concurrent.futures
        
        def create_file(i):
            file_path = str(temp_workspace / f"concurrent_{i}.txt")
            content = f"Concurrent content {i}"
            return write_file(file_path, content)
        
        # Execute concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_file, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all operations succeeded
        for result in results:
            assert "Successfully created file" in result
        
        # Verify all files were created
        for i in range(5):
            file_path = temp_workspace / f"concurrent_{i}.txt"
            assert file_path.exists()
            assert file_path.read_text() == f"Concurrent content {i}"
    
    def test_large_file_operations(self, temp_workspace):
        """Test operations with large files to verify performance and memory handling."""
        # Create large content (1MB)
        large_content = "A" * (1024 * 1024)
        large_file_path = str(temp_workspace / "large_file.txt")
        
        # Write large file
        write_result = write_file(large_file_path, large_content)
        assert "Successfully created file" in write_result
        
        # Read large file back
        read_result = read_file(large_file_path)
        assert read_result == large_content
        
        # List directory containing large file
        list_result = list_directory(str(temp_workspace))
        list_data = json.loads(list_result)
        
        # Find the large file entry
        large_file_entry = next(
            (entry for entry in list_data["entries"] if entry["name"] == "large_file.txt"),
            None
        )
        assert large_file_entry is not None
        assert large_file_entry["size"] == len(large_content)
        assert large_file_entry["type"] == "file"
    
    def test_unicode_content_handling(self, temp_workspace):
        """Test handling of unicode content across all tools."""
        # Unicode content with various character sets
        unicode_content = "Unicode test: áéíóú ñ 中文 🚀 العربية русский ελληνικά"
        unicode_file_path = str(temp_workspace / "unicode_test.txt")
        
        # Write unicode content
        write_result = write_file(unicode_file_path, unicode_content)
        assert "Successfully created file" in write_result
        
        # Read unicode content back
        read_result = read_file(unicode_file_path)
        assert read_result == unicode_content
        
        # List directory and verify unicode filename handling
        unicode_filename = "测试文件.txt"
        unicode_file2_path = str(temp_workspace / unicode_filename)
        
        write_file(unicode_file2_path, "Unicode filename test")
        
        list_result = list_directory(str(temp_workspace))
        list_data = json.loads(list_result)
        
        entry_names = {entry["name"] for entry in list_data["entries"]}
        assert unicode_filename in entry_names
    
    def test_directory_edge_cases(self, temp_workspace):
        """Test edge cases in directory operations."""
        # Test empty directory
        empty_dir = temp_workspace / "empty_dir"
        empty_dir.mkdir()
        
        list_result = list_directory(str(empty_dir))
        list_data = json.loads(list_result)
        assert list_data["total_entries"] == 0
        assert list_data["entries"] == []
        
        # Test directory with many files
        many_files_dir = temp_workspace / "many_files"
        many_files_dir.mkdir()
        
        # Create 50 files
        for i in range(50):
            (many_files_dir / f"file_{i:03d}.txt").write_text(f"Content {i}")
        
        list_result = list_directory(str(many_files_dir))
        list_data = json.loads(list_result)
        assert list_data["total_entries"] == 50
        
        # Verify sorting
        entry_names = [entry["name"] for entry in list_data["entries"]]
        expected_sorted = sorted(entry_names, key=str.lower)
        assert entry_names == expected_sorted
    
    def test_file_overwrite_scenarios(self, temp_workspace):
        """Test various file overwrite scenarios."""
        test_file = temp_workspace / "overwrite_test.txt"
        
        # Create initial file
        initial_content = "Initial content"
        write_result1 = write_file(str(test_file), initial_content)
        assert "Successfully created file" in write_result1
        
        # Overwrite with longer content
        longer_content = "This is much longer content that should completely replace the original"
        write_result2 = write_file(str(test_file), longer_content)
        assert "Successfully overwrote file" in write_result2
        
        # Verify content was completely replaced
        read_result = read_file(str(test_file))
        assert read_result == longer_content
        
        # Overwrite with shorter content
        shorter_content = "Short"
        write_result3 = write_file(str(test_file), shorter_content)
        assert "Successfully overwrote file" in write_result3
        
        # Verify content was completely replaced (not appended)
        read_result2 = read_file(str(test_file))
        assert read_result2 == shorter_content
        
        # Overwrite with empty content
        write_result4 = write_file(str(test_file), "")
        assert "Successfully overwrote file" in write_result4
        
        # Verify file is now empty
        read_result3 = read_file(str(test_file))
        assert read_result3 == ""


class TestMCPServerLifecycle:
    """Test MCP server lifecycle and initialization."""
    
    def test_server_initialization(self):
        """Test that server initializes correctly with proper configuration."""
        # Verify server name
        assert mcp.name == "mcp-file-server"
        
        # Verify tools are registered (we can test that the functions exist)
        assert callable(read_file)
        assert callable(write_file)
        assert callable(list_directory)
    
    def test_logging_setup(self):
        """Test that logging is properly configured."""
        logger = setup_logging()
        assert logger.name == "mcp_file_server"
        assert logger.level <= 20  # INFO level or lower
        
        # Verify handlers are configured
        assert len(logger.handlers) > 0 or len(logger.parent.handlers) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])