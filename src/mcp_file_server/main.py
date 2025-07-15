"""Main entry point for the MCP File Server."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from fastmcp import FastMCP


def setup_logging() -> logging.Logger:
    """Configure logging for the MCP File Server."""
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)  # Use stderr to avoid interfering with MCP stdio
        ]
    )
    
    # Create logger for this module
    logger = logging.getLogger("mcp_file_server")
    return logger


# Initialize logging
logger = setup_logging()

# Create FastMCP server instance
mcp = FastMCP("mcp-file-server")


def validate_and_sanitize_path(file_path: str) -> Path:
    """
    Validate and sanitize file path to prevent path traversal attacks.
    
    Args:
        file_path: The file path to validate
        
    Returns:
        Path: Sanitized Path object
        
    Raises:
        ValueError: If path is invalid or contains dangerous components
    """
    if not file_path or not file_path.strip():
        raise ValueError("File path cannot be empty")
    
    # Additional validation - ensure path doesn't contain null bytes (check before Path operations)
    if "\x00" in file_path:
        raise ValueError("Invalid characters in file path")
    
    try:
        # Convert to Path object and resolve to absolute path
        path = Path(file_path).resolve()
        
        # Check for path traversal attempts
        if ".." in file_path or file_path.startswith("/"):
            # Allow absolute paths but log them for security awareness
            logger.debug("Absolute path requested: %s", file_path)
            
        return path
        
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid file path: {str(e)}")


def is_binary_file(file_path: Path) -> bool:
    """
    Check if a file is binary by reading a small chunk and looking for null bytes.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if file appears to be binary, False otherwise
    """
    try:
        with open(file_path, 'rb') as f:
            # Read first 8192 bytes to check for binary content
            chunk = f.read(8192)
            # If we find null bytes, it's likely binary
            return b'\x00' in chunk
    except PermissionError:
        # Re-raise permission errors so they can be handled properly
        raise
    except Exception:
        # If we can't read the file for other reasons, assume it might be binary
        return True


@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        str: File contents as text
        
    Raises:
        ValueError: If file cannot be read or is binary
    """
    logger.debug("Reading file: %s", file_path)
    
    try:
        # Validate and sanitize the file path
        path = validate_and_sanitize_path(file_path)
        
        # Check if file exists
        if not path.exists():
            logger.warning("File not found: %s", path)
            raise ValueError(f"File not found: {file_path}")
        
        # Check if it's actually a file (not a directory)
        if not path.is_file():
            logger.warning("Path is not a file: %s", path)
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Check if file appears to be binary
        if is_binary_file(path):
            logger.warning("Binary file detected: %s", path)
            raise ValueError(f"Cannot read binary file: {file_path}. Only text files are supported.")
        
        # Read the file content
        try:
            content = path.read_text(encoding='utf-8')
            logger.debug("Successfully read file: %s (%d characters)", path, len(content))
            return content
            
        except UnicodeDecodeError:
            logger.warning("Unicode decode error for file: %s", path)
            raise ValueError(f"Cannot decode file as UTF-8: {file_path}. File may be binary or use unsupported encoding.")
        except PermissionError:
            logger.warning("Permission denied reading file: %s", path)
            raise ValueError(f"Permission denied reading file: {file_path}")
        except OSError as e:
            logger.error("OS error reading file %s: %s", path, str(e))
            raise ValueError(f"Error reading file: {str(e)}")
            
    except ValueError:
        # Re-raise ValueError as-is
        raise
    except Exception as e:
        logger.error("Unexpected error reading file %s: %s", file_path, str(e))
        raise ValueError(f"Unexpected error reading file: {str(e)}")


@mcp.tool()
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        
    Returns:
        str: Success message
        
    Raises:
        ValueError: If file cannot be written
    """
    logger.debug("Writing file: %s (%d characters)", file_path, len(content))
    
    try:
        # Validate and sanitize the file path
        path = validate_and_sanitize_path(file_path)
        
        # Check if the path points to an existing directory
        if path.exists() and path.is_dir():
            logger.warning("Cannot write to directory: %s", path)
            raise ValueError(f"Cannot write to directory: {file_path}")
        
        # Create parent directories if they don't exist
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug("Created parent directories for: %s", path)
        except PermissionError:
            logger.warning("Permission denied creating parent directories for: %s", path)
            raise ValueError(f"Permission denied creating parent directories for: {file_path}")
        except OSError as e:
            logger.error("OS error creating parent directories for %s: %s", path, str(e))
            raise ValueError(f"Error creating parent directories: {str(e)}")
        
        # Write the file content
        try:
            # Check if file exists for logging purposes
            file_exists = path.exists()
            action = "Overwriting" if file_exists else "Creating"
            logger.debug("%s file: %s", action, path)
            
            path.write_text(content, encoding='utf-8')
            
            success_message = f"Successfully {'overwrote' if file_exists else 'created'} file: {file_path}"
            logger.debug(success_message)
            return success_message
            
        except PermissionError:
            logger.warning("Permission denied writing file: %s", path)
            raise ValueError(f"Permission denied writing file: {file_path}")
        except OSError as e:
            logger.error("OS error writing file %s: %s", path, str(e))
            raise ValueError(f"Error writing file: {str(e)}")
        except UnicodeEncodeError as e:
            logger.warning("Unicode encode error for file %s: %s", path, str(e))
            raise ValueError(f"Cannot encode content as UTF-8: {str(e)}")
            
    except ValueError:
        # Re-raise ValueError as-is
        raise
    except Exception as e:
        logger.error("Unexpected error writing file %s: %s", file_path, str(e))
        raise ValueError(f"Unexpected error writing file: {str(e)}")


@mcp.tool()
def list_directory(directory_path: str) -> str:
    """
    List the contents of a directory with file metadata.
    
    Args:
        directory_path: Path to the directory to list
        
    Returns:
        str: Directory contents as JSON with file metadata
        
    Raises:
        ValueError: If directory cannot be listed
    """
    logger.debug("Listing directory: %s", directory_path)
    
    try:
        # Validate and sanitize the directory path
        path = validate_and_sanitize_path(directory_path)
        
        # Check if directory exists
        if not path.exists():
            logger.warning("Directory not found: %s", path)
            raise ValueError(f"Directory not found: {directory_path}")
        
        # Check if it's actually a directory (not a file)
        if not path.is_dir():
            logger.warning("Path is not a directory: %s", path)
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        # List directory contents
        try:
            entries = []
            
            # Iterate through directory contents
            for entry in path.iterdir():
                try:
                    # Get basic file information
                    stat_info = entry.stat()
                    
                    # Determine entry type
                    entry_type = "directory" if entry.is_dir() else "file"
                    
                    # Get file size (only for files, not directories)
                    size = stat_info.st_size if entry.is_file() else None
                    
                    # Get modification time in ISO format
                    modified_timestamp = datetime.fromtimestamp(stat_info.st_mtime)
                    modified_iso = modified_timestamp.isoformat()
                    
                    # Create entry dictionary
                    entry_dict = {
                        "name": entry.name,
                        "type": entry_type,
                        "size": size,
                        "modified": modified_iso,
                        "path": str(entry)
                    }
                    
                    entries.append(entry_dict)
                    
                except (OSError, PermissionError) as e:
                    # Log individual entry errors but continue processing other entries
                    logger.warning("Error accessing entry %s: %s", entry, str(e))
                    # Add entry with limited information
                    entries.append({
                        "name": entry.name,
                        "type": "unknown",
                        "size": None,
                        "modified": None,
                        "path": str(entry),
                        "error": "Permission denied or access error"
                    })
            
            # Sort entries by name for consistent output
            entries.sort(key=lambda x: x["name"].lower())
            
            # Create response structure
            response_data = {
                "directory": str(path),
                "entries": entries,
                "total_entries": len(entries)
            }
            
            # Convert to JSON string
            json_response = json.dumps(response_data, indent=2)
            
            logger.debug("Successfully listed directory: %s (%d entries)", path, len(entries))
            return json_response
            
        except PermissionError:
            logger.warning("Permission denied listing directory: %s", path)
            raise ValueError(f"Permission denied listing directory: {directory_path}")
        except OSError as e:
            logger.error("OS error listing directory %s: %s", path, str(e))
            raise ValueError(f"Error listing directory: {str(e)}")
            
    except ValueError:
        # Re-raise ValueError as-is
        raise
    except Exception as e:
        logger.error("Unexpected error listing directory %s: %s", directory_path, str(e))
        raise ValueError(f"Unexpected error listing directory: {str(e)}")


def run_server() -> None:
    """Entry point for running the server."""
    logger.info("Starting MCP File Server...")
    logger.info("Server name: %s", mcp.name)
    
    try:
        logger.info("MCP File Server initialized successfully")
        logger.info("Server ready to accept connections via stdio transport")
        
        # Run the FastMCP server
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping MCP File Server...")
    except Exception as e:
        logger.error("Error running MCP File Server: %s", str(e))
        raise
    finally:
        logger.info("MCP File Server shutdown complete")


if __name__ == "__main__":
    run_server()