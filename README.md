# MCP File Server

A Model Context Protocol (MCP) server that provides secure file system operation tools. This server enables MCP clients to read files, write files, and browse directory structures through a standardized protocol interface. Built with FastMCP for simplified development and deployment.

## Features

- **File Reading**: Read text file contents with encoding detection
- **File Writing**: Create and modify files with automatic directory creation
- **Directory Browsing**: List directory contents with detailed metadata
- **Security**: Path validation and traversal attack prevention
- **Error Handling**: Comprehensive error reporting with proper MCP error codes
- **Logging**: Structured logging for debugging and monitoring
- **FastMCP Framework**: Built with FastMCP for simplified server implementation
- **Full MCP Compliance**: Implements MCP protocol standards for seamless integration

## Installation

### Using uv (Recommended)

1. Clone or download this repository
2. Install dependencies and set up the project:

```bash
# Install all dependencies including development tools
uv sync

# Install only production dependencies
uv sync --no-dev
```

### From Source (Alternative)

1. Clone or download this repository
2. Install the package in development mode:

```bash
pip install -e .
```

### Development Installation

For development with testing and linting tools using uv:

```bash
# Install all dependencies including development tools
uv sync

# The project is automatically available for development
```

For development with pip (alternative):

```bash
pip install -e ".[dev]"
```

### Requirements

- Python 3.8 or higher
- FastMCP (`fastmcp` package)

## Usage

### Running the Server

#### Command Line (with uv)

```bash
# Run the server using uv
uv run mcp-file-server

# Or run directly with Python module
uv run python -m mcp_file_server.main
```

#### Command Line (traditional)

```bash
mcp-file-server
```

#### Direct Python Execution

```bash
python -m mcp_file_server.main
```

#### Programmatic Usage

```python
from mcp_file_server.main import run_server

# Run the server
run_server()
```

### MCP Client Configuration

#### Claude Desktop Configuration

Add to your Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

**Using uv (recommended):**
```json
{
  "mcpServers": {
    "file-server": {
      "command": "uv",
      "args": ["run", "mcp-file-server"],
      "cwd": "/path/to/mcp-file-server"
    }
  }
}
```

**Traditional approach:**
```json
{
  "mcpServers": {
    "file-server": {
      "command": "mcp-file-server",
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

#### Generic MCP Client Configuration

**Using uv (recommended):**
```json
{
  "mcpServers": {
    "file-operations": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_file_server.main"],
      "cwd": "/path/to/mcp-file-server"
    }
  }
}
```

**Traditional approach:**
```json
{
  "mcpServers": {
    "file-operations": {
      "command": "python",
      "args": ["-m", "mcp_file_server.main"],
      "cwd": "/path/to/mcp-file-server",
      "env": {
        "PYTHONPATH": "/path/to/mcp-file-server/src"
      }
    }
  }
}
```

#### Testing with MCP Inspector

You can test the server using the MCP Inspector tool:

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run with your server (using uv)
mcp-inspector uv run mcp-file-server

# Run with your server (traditional)
mcp-inspector mcp-file-server
```

## Available Tools

### 1. read_file

Reads the contents of a text file.

**Parameters:**
- `file_path` (string, required): Path to the file to read

**Example Usage:**
```json
{
  "name": "read_file",
  "arguments": {
    "file_path": "/path/to/document.txt"
  }
}
```

**Response:**
Returns the file contents as text. Binary files are rejected with an appropriate error message.

**Error Conditions:**
- File not found
- Permission denied
- Binary file detected
- Invalid file path

### 2. write_file

Writes content to a file, creating parent directories if necessary.

**Parameters:**
- `file_path` (string, required): Path to the file to write
- `content` (string, required): Content to write to the file

**Example Usage:**
```json
{
  "name": "write_file",
  "arguments": {
    "file_path": "/path/to/new-document.txt",
    "content": "Hello, World!\nThis is a test file."
  }
}
```

**Response:**
Returns a success message indicating whether the file was created or overwritten.

**Behavior:**
- Creates parent directories automatically
- Overwrites existing files
- Uses UTF-8 encoding

**Error Conditions:**
- Permission denied
- Invalid file path
- Attempting to write to a directory
- Unicode encoding errors

### 3. list_directory

Lists the contents of a directory with detailed metadata.

**Parameters:**
- `directory_path` (string, required): Path to the directory to list

**Example Usage:**
```json
{
  "name": "list_directory",
  "arguments": {
    "directory_path": "/path/to/directory"
  }
}
```

**Response:**
Returns a JSON object with directory information:

```json
{
  "directory": "/path/to/directory",
  "entries": [
    {
      "name": "file.txt",
      "type": "file",
      "size": 1024,
      "modified": "2024-01-15T10:30:00.123456",
      "path": "/path/to/directory/file.txt"
    },
    {
      "name": "subdirectory",
      "type": "directory",
      "size": null,
      "modified": "2024-01-14T15:45:30.789012",
      "path": "/path/to/directory/subdirectory"
    }
  ],
  "total_entries": 2
}
```

**Error Conditions:**
- Directory not found
- Permission denied
- Path is not a directory
- Invalid directory path

## Security Considerations

### Path Validation

The server implements several security measures:

- **Path Sanitization**: All file paths are validated and sanitized
- **Path Traversal Prevention**: Attempts to access parent directories using `..` are logged and monitored
- **Null Byte Protection**: File paths containing null bytes are rejected
- **Permission Respect**: File system permissions are honored and enforced

### File Size Limits

While not currently implemented, consider adding file size limits for production use:

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
```

### Binary File Handling

- Binary files are detected and rejected for read operations
- Only UTF-8 encoded text files are supported for reading
- Write operations always use UTF-8 encoding

### Logging and Monitoring

- All file operations are logged with appropriate detail levels
- Security-relevant events (path traversal attempts, permission errors) are logged as warnings
- Error conditions are logged with full context for debugging

## Best Practices

### For MCP Client Developers

1. **Error Handling**: Always handle MCP errors gracefully
2. **Path Validation**: Validate file paths on the client side before sending requests
3. **File Size Awareness**: Be mindful of file sizes when reading large files
4. **Permission Handling**: Implement appropriate user feedback for permission errors

### For Server Deployment

1. **Logging Configuration**: Configure appropriate log levels for your environment
2. **File System Permissions**: Run the server with minimal required permissions
3. **Resource Monitoring**: Monitor file system usage and server performance
4. **Security Updates**: Keep the MCP SDK and dependencies updated

### Example Client Code

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def example_usage():
    # Connect to the MCP server (using uv)
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp-file-server"]
    )
    
    # Alternative: Connect to the MCP server (traditional)
    # server_params = StdioServerParameters(
    #     command="mcp-file-server"
    # )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [tool.name for tool in tools.tools])
            
            # Read a file
            result = await session.call_tool("read_file", {
                "file_path": "example.txt"
            })
            print("File contents:", result.content[0].text)
            
            # Write a file
            await session.call_tool("write_file", {
                "file_path": "output.txt",
                "content": "Hello from MCP!"
            })
            
            # List directory
            result = await session.call_tool("list_directory", {
                "directory_path": "."
            })
            print("Directory listing:", result.content[0].text)

# Run the example
asyncio.run(example_usage())
```

## Troubleshooting

### Common Issues

#### Server Won't Start

**Problem**: Server fails to start with import errors
**Solution**: 
- With uv: Ensure dependencies are installed: `uv sync`
- With pip: Ensure FastMCP is installed: `pip install fastmcp`
- Check Python version (3.8+ required)
- With uv: Dependencies are automatically managed
- With pip: Verify installation: `pip install -e .`

#### Permission Denied Errors

**Problem**: File operations fail with permission errors
**Solutions**:
- Check file system permissions
- Ensure the server process has appropriate access rights
- On Unix systems, check file ownership and permissions with `ls -la`

#### Binary File Errors

**Problem**: "Cannot read binary file" errors
**Solutions**:
- Verify the file is actually a text file
- Check file encoding (only UTF-8 is supported)
- Use a text editor to confirm file contents

#### Path Not Found Errors

**Problem**: Files or directories not found
**Solutions**:
- Verify the path exists and is spelled correctly
- Use absolute paths to avoid confusion
- Check that the path is accessible from the server's working directory

#### MCP Protocol Errors

**Problem**: Client cannot connect or communicate with server
**Solutions**:
- Verify MCP client configuration
- Check server logs for startup errors
- Ensure stdio transport is working correctly
- Test with MCP Inspector tool

### Debugging

#### Enable Debug Logging

Modify the logging configuration in `main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
```

#### Test Server Manually

**Using uv (recommended):**
```bash
# Test server startup
uv run python -m mcp_file_server.main

# Test with MCP Inspector
mcp-inspector uv run mcp-file-server
```

**Traditional approach:**
```bash
# Test server startup
python -m mcp_file_server.main

# Test with MCP Inspector
mcp-inspector mcp-file-server
```

#### Common Error Codes

- `INVALID_PARAMS`: Missing or invalid parameters
- `INVALID_REQUEST`: File/directory not found or invalid operation
- `INTERNAL_ERROR`: Permission denied or system errors

### Getting Help

1. Check the server logs for detailed error messages
2. Verify your MCP client configuration
3. Test with minimal examples before complex operations
4. Ensure all dependencies are properly installed

## Development

### Running Tests

**Using uv (recommended):**
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/mcp_file_server

# Run specific test file
uv run pytest tests/test_integration.py
```

**Traditional approach:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mcp_file_server

# Run specific test file
pytest tests/test_integration.py
```

### Code Formatting

**Using uv (recommended):**
```bash
# Format code
uv run black src/ tests/

# Sort imports
uv run isort src/ tests/

# Type checking
uv run mypy src/
```

**Traditional approach:**
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/
```

### Project Structure

```
mcp-file-server/
├── src/
│   └── mcp_file_server/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── test_integration.py
│   ├── test_list_directory.py
│   ├── test_read_file.py
│   └── test_write_file.py
├── pyproject.toml
└── README.md
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Changelog

### Version 0.1.0
- Initial release
- Basic file operations (read, write, list)
- MCP protocol compliance
- Security features and path validation
- Comprehensive error handling and logging