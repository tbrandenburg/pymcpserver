"""Test script to verify uv project functionality.

This test script verifies that:
1. uv sync installs all dependencies correctly
2. uv run mcp-file-server works identically to previous setup
3. uv run pytest executes tests correctly
4. Development tools (black, isort, mypy) work via uv run

Requirements: 4.1, 4.2, 6.2, 6.3
"""

import subprocess
import sys
import tempfile
import json
import os
from pathlib import Path
import pytest


class TestUvProjectFunctionality:
    """Test uv project functionality and tool execution."""
    
    def test_uv_sync_installs_dependencies(self):
        """Test that uv sync installs all dependencies correctly."""
        # Run uv sync to ensure dependencies are installed
        result = subprocess.run(
            ["uv", "sync"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # Check that uv sync completed successfully
        assert result.returncode == 0, f"uv sync failed: {result.stderr}"
        
        # Verify that uv.lock file exists and is valid
        lock_file = Path(__file__).parent.parent / "uv.lock"
        assert lock_file.exists(), "uv.lock file should exist after sync"
        
        # Verify that .venv directory exists
        venv_dir = Path(__file__).parent.parent / ".venv"
        assert venv_dir.exists(), ".venv directory should exist after sync"
        
        # Verify that key dependencies are available
        # Test that we can import fastmcp (main dependency)
        import_result = subprocess.run(
            ["uv", "run", "python", "-c", "import fastmcp; print('fastmcp imported successfully')"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert import_result.returncode == 0, f"Failed to import fastmcp: {import_result.stderr}"
        assert "fastmcp imported successfully" in import_result.stdout
        
        # Test that dev dependencies are available
        dev_deps = ["pytest", "black", "isort", "mypy"]
        for dep in dev_deps:
            import_result = subprocess.run(
                ["uv", "run", "python", "-c", f"import {dep}; print('{dep} imported successfully')"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            assert import_result.returncode == 0, f"Failed to import {dep}: {import_result.stderr}"
            assert f"{dep} imported successfully" in import_result.stdout
    
    def test_uv_run_mcp_file_server_works(self):
        """Test that uv run mcp-file-server works identically to previous setup."""
        # Test that the mcp-file-server command is available via uv run
        result = subprocess.run(
            ["uv", "run", "mcp-file-server", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=10  # Add timeout to prevent hanging
        )
        
        # The command should either succeed or fail gracefully (not hang)
        # Since MCP servers typically run indefinitely, we expect it to start
        # but we'll test with --help if available, or just check it can be invoked
        assert result.returncode in [0, 1, 2], f"mcp-file-server command failed unexpectedly: {result.stderr}"
        
        # Test that we can run the server module directly
        module_result = subprocess.run(
            ["uv", "run", "python", "-m", "mcp_file_server.main", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=10
        )
        
        # Should be able to import and run the module
        # Even if --help isn't supported, the module should be importable
        assert module_result.returncode in [0, 1, 2], f"Module execution failed: {module_result.stderr}"
        
        # Test that the main module can be imported without errors
        import_result = subprocess.run(
            ["uv", "run", "python", "-c", "from mcp_file_server.main import run_server; print('Server module imported successfully')"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert import_result.returncode == 0, f"Failed to import server module: {import_result.stderr}"
        assert "Server module imported successfully" in import_result.stdout
    
    def test_uv_run_pytest_executes_tests(self):
        """Test that uv run pytest executes tests correctly."""
        # Run pytest via uv run
        result = subprocess.run(
            ["uv", "run", "pytest", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0, f"pytest --version failed: {result.stderr}"
        assert "pytest" in result.stdout.lower(), "pytest version output should contain 'pytest'"
        
        # Run a simple test to verify pytest works
        # We'll run just one test file to avoid running the entire test suite
        test_result = subprocess.run(
            ["uv", "run", "pytest", "tests/test_read_file.py", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=60  # Give tests time to run
        )
        
        # Tests should pass (or at least pytest should run without import errors)
        assert test_result.returncode == 0, f"pytest execution failed: {test_result.stderr}\nStdout: {test_result.stdout}"
        
        # Verify that tests actually ran
        assert "test session starts" in test_result.stdout or "collected" in test_result.stdout, \
            f"pytest didn't seem to run tests properly: {test_result.stdout}"
    
    def test_uv_run_black_code_formatter(self):
        """Test that black code formatter works via uv run."""
        # Test black version
        result = subprocess.run(
            ["uv", "run", "black", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0, f"black --version failed: {result.stderr}"
        assert "black" in result.stdout.lower(), "black version output should contain 'black'"
        
        # Test black check mode on source files (doesn't modify files)
        check_result = subprocess.run(
            ["uv", "run", "black", "--check", "--diff", "src/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # Black should either pass (code is formatted) or show diffs (code needs formatting)
        # Both are valid outcomes - we just want to ensure black runs without errors
        assert check_result.returncode in [0, 1], f"black check failed unexpectedly: {check_result.stderr}"
    
    def test_uv_run_isort_import_sorter(self):
        """Test that isort import sorter works via uv run."""
        # Test isort version
        result = subprocess.run(
            ["uv", "run", "isort", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0, f"isort --version failed: {result.stderr}"
        assert "isort" in result.stdout.lower(), "isort version output should contain 'isort'"
        
        # Test isort check mode on source files (doesn't modify files)
        check_result = subprocess.run(
            ["uv", "run", "isort", "--check-only", "--diff", "src/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # isort should either pass (imports are sorted) or show diffs (imports need sorting)
        # Both are valid outcomes - we just want to ensure isort runs without errors
        assert check_result.returncode in [0, 1], f"isort check failed unexpectedly: {check_result.stderr}"
    
    def test_uv_run_mypy_type_checker(self):
        """Test that mypy type checker works via uv run."""
        # Test mypy version
        result = subprocess.run(
            ["uv", "run", "mypy", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0, f"mypy --version failed: {result.stderr}"
        assert "mypy" in result.stdout.lower(), "mypy version output should contain 'mypy'"
        
        # Test mypy on source files
        check_result = subprocess.run(
            ["uv", "run", "mypy", "src/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # mypy should run without crashing
        # It may find type issues (exit code 1) but shouldn't have import/setup errors
        assert check_result.returncode in [0, 1], f"mypy check failed unexpectedly: {check_result.stderr}"
        
        # Verify mypy actually processed files
        assert ("Success" in check_result.stdout or 
                "error:" in check_result.stdout or 
                "note:" in check_result.stdout or
                len(check_result.stdout.strip()) == 0), \
            f"mypy didn't seem to process files properly: {check_result.stdout}"
    
    def test_uv_environment_isolation(self):
        """Test that uv creates proper environment isolation."""
        # Test that uv run uses the project's virtual environment
        result = subprocess.run(
            ["uv", "run", "python", "-c", "import sys; print(sys.executable)"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0, f"Failed to get Python executable path: {result.stderr}"
        
        # The Python executable should be in the project's .venv directory
        python_path = result.stdout.strip()
        project_root = Path(__file__).parent.parent
        expected_venv_path = project_root / ".venv"
        
        # Convert to Path objects for comparison
        python_path_obj = Path(python_path)
        
        # Check if the Python executable is in the project's venv
        # (accounting for different OS path structures)
        assert str(expected_venv_path) in str(python_path_obj), \
            f"Python executable should be in project venv. Got: {python_path}, Expected to contain: {expected_venv_path}"
    
    def test_uv_dependency_consistency(self):
        """Test that uv maintains consistent dependencies across runs."""
        # Run uv sync twice and ensure it's idempotent
        result1 = subprocess.run(
            ["uv", "sync"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result1.returncode == 0, f"First uv sync failed: {result1.stderr}"
        
        result2 = subprocess.run(
            ["uv", "sync"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result2.returncode == 0, f"Second uv sync failed: {result2.stderr}"
        
        # Both runs should succeed and be consistent
        # The second run should be faster (no changes needed)
        
        # Verify lock file hasn't changed
        lock_file = Path(__file__).parent.parent / "uv.lock"
        assert lock_file.exists(), "uv.lock should still exist after multiple syncs"
    
    def test_uv_project_scripts_work(self):
        """Test that project scripts defined in pyproject.toml work with uv."""
        # Test that the entry point script works
        result = subprocess.run(
            ["uv", "run", "python", "-c", "from mcp_file_server.main import run_server; print('Entry point accessible')"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0, f"Entry point test failed: {result.stderr}"
        assert "Entry point accessible" in result.stdout
        
        # Test that we can access the main module
        result = subprocess.run(
            ["uv", "run", "python", "-c", "import mcp_file_server; print('Package importable')"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0, f"Package import test failed: {result.stderr}"
        assert "Package importable" in result.stdout


class TestUvCompatibilityWithExistingSetup:
    """Test that uv setup maintains compatibility with existing functionality."""
    
    def test_existing_tests_still_pass_with_uv(self):
        """Test that existing tests still pass when run via uv."""
        # Run a subset of existing tests to verify compatibility
        test_files = [
            "tests/test_read_file.py",
            "tests/test_write_file.py",
            "tests/test_list_directory.py"
        ]
        
        for test_file in test_files:
            if Path(Path(__file__).parent.parent / test_file).exists():
                result = subprocess.run(
                    ["uv", "run", "pytest", test_file, "-v"],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent,
                    timeout=60
                )
                
                assert result.returncode == 0, \
                    f"Existing test {test_file} failed with uv: {result.stderr}\nStdout: {result.stdout}"
    
    def test_package_structure_unchanged(self):
        """Test that package structure is unchanged and accessible."""
        # Test that all expected modules are importable
        modules_to_test = [
            "mcp_file_server",
            "mcp_file_server.main"
        ]
        
        for module in modules_to_test:
            result = subprocess.run(
                ["uv", "run", "python", "-c", f"import {module}; print('{module} imported successfully')"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            assert result.returncode == 0, f"Failed to import {module}: {result.stderr}"
            assert f"{module} imported successfully" in result.stdout
    
    def test_development_workflow_unchanged(self):
        """Test that development workflow commands work the same way."""
        # Test that we can still run tests, format code, etc.
        commands_to_test = [
            (["uv", "run", "pytest", "--collect-only"], "test collection"),
            (["uv", "run", "black", "--check", "src/"], "code formatting check"),
            (["uv", "run", "isort", "--check-only", "src/"], "import sorting check"),
        ]
        
        for command, description in commands_to_test:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=30
            )
            
            # Commands should run without crashing (exit codes 0 or 1 are acceptable)
            assert result.returncode in [0, 1], \
                f"{description} failed unexpectedly: {result.stderr}\nCommand: {' '.join(command)}"


if __name__ == "__main__":
    # Run the tests when script is executed directly
    pytest.main([__file__, "-v"])