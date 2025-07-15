import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.mcp_file_server.main import mcp

async def test():
    tools = await mcp.get_tools()
    print('Tools type:', type(tools))
    print('Tool names:', list(tools.keys()))
    
    expected_tools = ["read_file", "write_file", "list_directory"]
    for tool_name in expected_tools:
        if tool_name in tools:
            print(f'✅ {tool_name} tool found')
        else:
            print(f'❌ {tool_name} tool missing')
    
    print(f'✅ FastMCP server has {len(tools)} tools configured correctly!')

asyncio.run(test())