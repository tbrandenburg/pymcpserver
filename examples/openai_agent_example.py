#!/usr/bin/env python3
"""
Example OpenAI Agent SDK integration with MCP File Server.

This script demonstrates how to integrate the MCP File Server with an OpenAI Agent SDK agent,
allowing the agent to perform file operations through the MCP protocol.
"""

import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio


async def demo_file_operations():
    """Demonstrate file operations using OpenAI Agent SDK with MCP File Server."""
    
    print("=== OpenAI Agent SDK + MCP File Server Demo ===\n")
    
    # Connect to the MCP File Server
    server = MCPServerStdio(params={
        "command": "mcp-file-server",
        # Alternative: "command": "python", "args": ["-m", "mcp_file_server.main"]
    })
    
    await server.connect()
    
    try:
        # Create an agent that can perform file operations with MCP servers
        agent = Agent(
            name="FileOperationAgent",
            instructions="""You are a helpful assistant that can perform file operations.
            Use the available MCP tools to read files, write files, and list directory contents.
            Always provide clear and helpful responses about the file operations you perform.""",
            mcp_servers=[server]
        )
        
        # Demo 1: List current directory
        print("Demo 1: List current directory")
        result = await Runner.run(agent, "List the contents of the current directory")
        print(f"🗂️  Result: {result.final_output}\n")
        
        # Demo 2: Create a test file
        print("Demo 2: Create a test file")
        test_content = """# OpenAI Agent SDK + MCP Integration Demo

This file was created by an OpenAI Agent SDK agent using the MCP File Server.

## Features Demonstrated:
- File creation through MCP protocol
- Integration with OpenAI Agent SDK
- Simple and clean implementation

## Technical Details:
- MCP Server: File operations (read, write, list)
- Agent SDK: agents library
- Protocol: Model Context Protocol (MCP)
"""
        
        result = await Runner.run(agent, f"Create a file called 'agent_demo_output.md' with this content: {test_content}")
        print(f"📝 Result: {result.final_output}\n")
        
        # Demo 3: Read the created file
        print("Demo 3: Read the created file")
        result = await Runner.run(agent, "Read the contents of the file 'agent_demo_output.md'")
        print(f"📖 Result: {result.final_output}\n")
        
        # Demo 4: File management task
        print("Demo 4: File management task")
        result = await Runner.run(agent, "Check if there are any .py files in the examples directory and tell me about them")
        print(f"🔍 Result: {result.final_output}\n")
        
        print("=== Demo Complete ===")
        print("The agent successfully used the MCP File Server for file operations!")
        
    except Exception as e:
        print(f"Demo error: {e}")
    
    finally:
        # Clean up the server connection
        await server.cleanup()


async def interactive_agent_mode():
    """Interactive mode for the OpenAI Agent SDK + MCP integration."""
    
    print("=== Interactive OpenAI Agent SDK + MCP Mode ===")
    print("Ask the agent to perform file operations in natural language.")
    print("Examples:")
    print("- 'Read the README.md file'")
    print("- 'List all files in the src directory'")
    print("- 'Create a new file called test.txt with some content'")
    print("Type 'quit' to exit.\n")
    
    # Connect to the MCP File Server
    server = MCPServerStdio(params={
        "command": "mcp-file-server"
    })
    
    await server.connect()
    
    try:
        # Create the agent with MCP servers
        agent = Agent(
            name="FileOperationAgent",
            instructions="""You are a helpful file management assistant.
            Use the available MCP tools to help users with file operations.
            Be clear about what operations you're performing and provide helpful feedback.""",
            mcp_servers=[server]
        )
        
        while True:
            try:
                user_input = input("\nagent> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_input:
                    print("Processing request...")
                    result = await Runner.run(agent, user_input)
                    print(f"\n🤖 Agent: {result.final_output}")
            
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit.")
            except EOFError:
                break
    
    except Exception as e:
        print(f"Interactive mode error: {e}")
    
    finally:
        await server.cleanup()


def main():
    """Main entry point for the OpenAI Agent SDK example."""
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_agent_mode())
    else:
        asyncio.run(demo_file_operations())


if __name__ == "__main__":
    main()