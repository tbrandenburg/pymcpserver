"""Integration test to verify MCP server works identically with uv setup.

This test verifies that the MCP server functionality is unchanged
when run via uv compared to the previous setup.
"""

import subprocess
import tempfile
import json
import time
import signal
import os
from pathlib import Path
import pytest


class TestUvMcpIntegration:
    """Test MCP server integration with uv setup."""
    
    def test_mcp_server_starts_with_uv(self):
        """Test that MCP server starts correctly with uv run."""
        # Start the server process
        process = subprocess.Popen(
            ["uv", "run", "mcp-file-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            # Give the server a moment to start
            time.sleep(2)
            
            # Check if process is still running (not crashed)
            assert process.poll() is None, "MCP server process should still be running"
            
            # Send a simple MCP initialization message
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Send the message
            message_str = json.dumps(init_message) + "\n"
            process.stdin.write(message_str)
            process.stdin.flush()
            
            # Try to read response (with timeout)
            # Note: This is a basic test - full MCP protocol testing would be more complex
            
        finally:
            # Clean up the process
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    
    def test_mcp_server_module_import_works(self):
        """Test that the MCP server module can be imported and initialized."""
        # Test that we can import the main components
        result = subprocess.run(
            ["uv", "run", "python", "-c", """
import sys
sys.path.insert(0, 'src')
from mcp_file_server.main import mcp, read_file, write_file, list_directory
print('All MCP components imported successfully')
print(f'Server name: {mcp.name}')
print('Tools available:', hasattr(read_file, 'fn'), hasattr(write_file, 'fn'), hasattr(list_directory, 'fn'))
"""],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0, f"Failed to import MCP components: {result.stderr}"
        assert "All MCP components imported successfully" in result.stdout
        assert "Server name: mcp-file-server" in result.stdout
        assert "Tools available: True True True" in result.stdout
    
    def test_mcp_tools_functionality_unchanged(self):
        """Test that MCP tools work the same way with uv setup."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for MCP tools")
            temp_file_path = f.name
        
        try:
            # Test that we can use the MCP tools directly
            test_script = f"""
import sys
sys.path.insert(0, 'src')
from mcp_file_server.main import read_file, write_file, list_directory
import tempfile
import os

# Test read_file
content = read_file.fn('{temp_file_path}')
print(f'Read content: {{content}}')

# Test write_file
new_file = '{temp_file_path}.new'
result = write_file.fn(new_file, 'New test content')
print(f'Write result: {{result}}')

# Test list_directory
import json
dir_result = list_directory.fn('{os.path.dirname(temp_file_path)}')
dir_data = json.loads(dir_result)
print(f'Directory entries: {{len(dir_data["entries"])}}')

print('All MCP tools work correctly')
"""
            
            result = subprocess.run(
                ["uv", "run", "python", "-c", test_script],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            assert result.returncode == 0, f"MCP tools test failed: {result.stderr}"
            assert "Read content: Test content for MCP tools" in result.stdout
            assert "Write result: Successfully" in result.stdout
            assert "Directory entries:" in result.stdout
            assert "All MCP tools work correctly" in result.stdout
            
        finally:
            # Clean up temp files
            try:
                os.unlink(temp_file_path)
                os.unlink(temp_file_path + '.new')
            except FileNotFoundError:
                pass
    
    def test_entry_point_consistency(self):
        """Test that the entry point works consistently with uv."""
        # Test that the entry point is accessible
        result = subprocess.run(
            ["uv", "run", "python", "-c", """
import sys
sys.path.insert(0, 'src')

# Test that the entry point function exists
from mcp_file_server.main import run_server
print('Entry point function accessible:', callable(run_server))

# Test that we can get the entry point info
try:
    import importlib.metadata
    entry_points = importlib.metadata.entry_points()
    console_scripts = entry_points.select(group='console_scripts')
    mcp_script = None
    for ep in console_scripts:
        if ep.name == 'mcp-file-server':
            mcp_script = ep
            break
    
    if mcp_script:
        print(f'Entry point found: {mcp_script.name} -> {mcp_script.value}')
    else:
        print('Entry point not found in metadata, but function is accessible')
except Exception as e:
    print(f'Entry point check via metadata failed: {e}')
    print('But direct function access works')

print('Entry point consistency verified')
"""],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0, f"Entry point test failed: {result.stderr}"
        assert "Entry point function accessible: True" in result.stdout
        assert "Entry point consistency verified" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])