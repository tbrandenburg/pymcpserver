#!/usr/bin/env python3
"""
Simple test to verify MCP File Server works with basic MCP client.
Run this to test the server before trying the OpenAI Agent SDK integration.

Usage:
    # Run with uv (recommended):
    uv run python examples/simple_test.py
    
    # Traditional Python (if uv not available):
    python examples/simple_test.py
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def simple_test():
    """Simple test of MCP File Server functionality."""
    
    print("Testing MCP File Server...")
    
    server_params = StdioServerParameters(
        command="mcp-file-server",
        # Alternative with uv (recommended for development):
        # command="uv",
        # args=["run", "mcp-file-server"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test basic functionality
                result = await session.call_tool("write_file", {
                    "file_path": "simple_test_output.txt",
                    "content": "Hello from MCP File Server!"
                })
                print(f"✅ Write test: {result.content[0].text}")
                
                result = await session.call_tool("read_file", {
                    "file_path": "simple_test_output.txt"
                })
                print(f"✅ Read test: {result.content[0].text}")
                
                print("✅ MCP File Server is working correctly!")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(simple_test())
    exit(0 if success else 1)