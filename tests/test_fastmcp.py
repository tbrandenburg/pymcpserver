#!/usr/bin/env python3
"""Quick test script to verify FastMCP refactoring works correctly."""

import pytest
from src.mcp_file_server.main import mcp

@pytest.mark.asyncio
async def test_fastmcp_server():
    """Test that FastMCP server is properly configured."""
    print("Testing FastMCP refactored server...")
    
    # Test 1: Check server name
    print(f"1. Server name: {mcp.name}")
    assert mcp.name == "mcp-file-server"
    
    # Test 2: Check available tools
    tools = await mcp.get_tools()
    tool_names = list(tools.keys())
    print(f"2. Available tools: {tool_names}")
    
    expected_tools = ["read_file", "write_file", "list_directory"]
    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Missing tool: {expected_tool}"
    
    print("✅ FastMCP server configured correctly!")
    print(f"✅ All {len(tools)} tools are available: {tool_names}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_fastmcp_server())