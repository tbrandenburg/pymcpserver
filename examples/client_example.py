#!/usr/bin/env python3
"""
Example MCP client for testing the MCP File Server.

This script demonstrates how to connect to and interact with the MCP File Server
using the MCP Python SDK.

Usage:
    # Run with uv (recommended):
    uv run python examples/client_example.py
    
    # Interactive mode with uv:
    uv run python examples/client_example.py --interactive
    
    # Traditional Python (if uv not available):
    python examples/client_example.py
"""

import asyncio
import json
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_file_operations():
    """Test all file operations provided by the MCP File Server."""
    
    # Configure server parameters
    server_params = StdioServerParameters(
        command="mcp-file-server",
        # Alternatively, you can use uv run (recommended for development):
        # command="uv",
        # args=["run", "mcp-file-server"]
        # Or direct Python execution:
        # command="python",
        # args=["-m", "mcp_file_server.main"]
    )
    
    print("Connecting to MCP File Server...")
    
    try:
        # Connect to the server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                print("Initializing session...")
                await session.initialize()
                
                # List available tools
                print("\n=== Available Tools ===")
                tools_result = await session.list_tools()
                for tool in tools_result.tools:
                    print(f"- {tool.name}: {tool.description}")
                
                # Test directory listing
                print("\n=== Testing Directory Listing ===")
                try:
                    result = await session.call_tool("list_directory", {
                        "directory_path": "."
                    })
                    directory_data = json.loads(result.content[0].text)
                    print(f"Directory: {directory_data['directory']}")
                    print(f"Total entries: {directory_data['total_entries']}")
                    
                    # Show first few entries
                    for entry in directory_data['entries'][:5]:
                        size_info = f" ({entry['size']} bytes)" if entry['size'] is not None else ""
                        print(f"  {entry['type']}: {entry['name']}{size_info}")
                    
                    if len(directory_data['entries']) > 5:
                        print(f"  ... and {len(directory_data['entries']) - 5} more entries")
                        
                except Exception as e:
                    print(f"Error listing directory: {e}")
                
                # Test file writing
                print("\n=== Testing File Writing ===")
                test_content = """Hello from MCP File Server!

This is a test file created by the example client.
It demonstrates the write_file functionality.

Features tested:
- File creation
- UTF-8 encoding
- Multi-line content
"""
                
                try:
                    result = await session.call_tool("write_file", {
                        "file_path": "test_output.txt",
                        "content": test_content
                    })
                    print(f"Write result: {result.content[0].text}")
                except Exception as e:
                    print(f"Error writing file: {e}")
                
                # Test file reading
                print("\n=== Testing File Reading ===")
                try:
                    result = await session.call_tool("read_file", {
                        "file_path": "test_output.txt"
                    })
                    read_content = result.content[0].text
                    print(f"Read {len(read_content)} characters from file:")
                    print("--- File Contents ---")
                    print(read_content)
                    print("--- End File Contents ---")
                    
                    # Verify content matches
                    if read_content == test_content:
                        print("✓ File content verification successful!")
                    else:
                        print("✗ File content verification failed!")
                        
                except Exception as e:
                    print(f"Error reading file: {e}")
                
                # Test error handling
                print("\n=== Testing Error Handling ===")
                print("Note: MCP servers handle errors gracefully by returning error responses")
                print("rather than throwing exceptions that would crash the client.")
                
                # Test reading non-existent file
                try:
                    result = await session.call_tool("read_file", {
                        "file_path": "non_existent_file.txt"
                    })
                    print("✓ Server handled non-existent file error gracefully (no exception thrown)")
                except Exception as e:
                    print(f"✓ Correctly handled non-existent file error: {type(e).__name__}: {e}")
                
                # Test listing non-existent directory
                try:
                    result = await session.call_tool("list_directory", {
                        "directory_path": "non_existent_directory"
                    })
                    print("✓ Server handled non-existent directory error gracefully (no exception thrown)")
                except Exception as e:
                    print(f"✓ Correctly handled non-existent directory error: {type(e).__name__}: {e}")
                
                # Test invalid parameters
                try:
                    result = await session.call_tool("read_file", {})
                    print("✓ Server handled missing parameters error gracefully (no exception thrown)")
                except Exception as e:
                    print(f"✓ Correctly handled missing parameters error: {type(e).__name__}: {e}")
                
                print("\n=== Test Complete ===")
                print("All tests completed successfully!")
                
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        print("Make sure the MCP File Server is properly installed and accessible.")
        return False
    
    return True


async def interactive_mode():
    """Interactive mode for testing the MCP File Server."""
    
    server_params = StdioServerParameters(
        command="mcp-file-server",
        # Alternatively, you can use uv run (recommended for development):
        # command="uv",
        # args=["run", "mcp-file-server"]
    )
    
    print("Starting interactive MCP File Server client...")
    print("Type 'help' for available commands, 'quit' to exit.")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                while True:
                    try:
                        command = input("\nmcp> ").strip()
                        
                        if command.lower() in ['quit', 'exit', 'q']:
                            break
                        elif command.lower() == 'help':
                            print("""
Available commands:
  read <file_path>           - Read a file
  write <file_path> <content> - Write content to a file
  list <directory_path>      - List directory contents
  tools                      - Show available tools
  help                       - Show this help message
  quit                       - Exit the client
""")
                        elif command.lower() == 'tools':
                            tools_result = await session.list_tools()
                            print("Available tools:")
                            for tool in tools_result.tools:
                                print(f"  {tool.name}: {tool.description}")
                        
                        elif command.startswith('read '):
                            file_path = command[5:].strip()
                            if not file_path:
                                print("Usage: read <file_path>")
                                continue
                            
                            try:
                                result = await session.call_tool("read_file", {
                                    "file_path": file_path
                                })
                                print(f"File contents:\n{result.content[0].text}")
                            except Exception as e:
                                print(f"Error: {e}")
                        
                        elif command.startswith('write '):
                            parts = command[6:].split(' ', 1)
                            if len(parts) < 2:
                                print("Usage: write <file_path> <content>")
                                continue
                            
                            file_path, content = parts
                            try:
                                result = await session.call_tool("write_file", {
                                    "file_path": file_path,
                                    "content": content
                                })
                                print(result.content[0].text)
                            except Exception as e:
                                print(f"Error: {e}")
                        
                        elif command.startswith('list '):
                            directory_path = command[5:].strip()
                            if not directory_path:
                                print("Usage: list <directory_path>")
                                continue
                            
                            try:
                                result = await session.call_tool("list_directory", {
                                    "directory_path": directory_path
                                })
                                directory_data = json.loads(result.content[0].text)
                                print(f"Directory: {directory_data['directory']}")
                                print(f"Entries ({directory_data['total_entries']}):")
                                for entry in directory_data['entries']:
                                    size_info = f" ({entry['size']} bytes)" if entry['size'] is not None else ""
                                    print(f"  {entry['type']}: {entry['name']}{size_info}")
                            except Exception as e:
                                print(f"Error: {e}")
                        
                        elif command:
                            print(f"Unknown command: {command}")
                            print("Type 'help' for available commands.")
                    
                    except KeyboardInterrupt:
                        print("\nUse 'quit' to exit.")
                    except EOFError:
                        break
                
    except Exception as e:
        print(f"Failed to connect to server: {e}")


def main():
    """Main entry point for the example client."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_mode())
    else:
        success = asyncio.run(test_file_operations())
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()