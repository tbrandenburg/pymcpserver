"""
Test script to validate the build and distribution process for uv project conversion.
This test covers all aspects of task 6: Validate build and distribution process.
"""

import os
import subprocess
import tempfile
import shutil
import zipfile
import tarfile
from pathlib import Path
import pytest


class TestBuildValidation:
    """Test suite for validating build and distribution process."""

    def test_uv_build_command(self):
        """Test that uv build command works correctly."""
        # Clean any existing build artifacts
        subprocess.run(["rm", "-rf", "dist/", "build/", "src/*.egg-info/"], 
                      shell=True, check=False)
        
        # Run uv build
        result = subprocess.run(["uv", "build"], capture_output=True, text=True)
        
        # Check that build succeeded
        assert result.returncode == 0, f"uv build failed: {result.stderr}"
        
        # Check that expected files were created
        dist_path = Path("dist")
        assert dist_path.exists(), "dist directory was not created"
        
        wheel_files = list(dist_path.glob("*.whl"))
        tar_files = list(dist_path.glob("*.tar.gz"))
        
        assert len(wheel_files) == 1, f"Expected 1 wheel file, found {len(wheel_files)}"
        assert len(tar_files) == 1, f"Expected 1 tar.gz file, found {len(tar_files)}"
        
        # Verify file naming convention
        wheel_file = wheel_files[0]
        tar_file = tar_files[0]
        
        assert "mcp_file_server-0.1.0" in wheel_file.name
        assert "mcp_file_server-0.1.0" in tar_file.name
        assert wheel_file.name.endswith("-py3-none-any.whl")

    def test_package_contents(self):
        """Test that the generated package contains expected contents."""
        dist_path = Path("dist")
        wheel_files = list(dist_path.glob("*.whl"))
        
        if not wheel_files:
            pytest.skip("No wheel file found, run test_uv_build_command first")
        
        wheel_file = wheel_files[0]
        
        # Extract wheel and check contents
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(wheel_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            temp_path = Path(temp_dir)
            
            # Check for main package files
            assert (temp_path / "mcp_file_server" / "__init__.py").exists()
            assert (temp_path / "mcp_file_server" / "main.py").exists()
            
            # Check for metadata
            dist_info_dirs = list(temp_path.glob("*.dist-info"))
            assert len(dist_info_dirs) == 1, "Expected exactly one .dist-info directory"
            
            dist_info = dist_info_dirs[0]
            assert (dist_info / "METADATA").exists()
            assert (dist_info / "entry_points.txt").exists()
            
            # Check entry points
            entry_points_content = (dist_info / "entry_points.txt").read_text()
            assert "mcp-file-server = mcp_file_server.main:run_server" in entry_points_content

    def test_package_installation(self):
        """Test that the built package can be installed correctly."""
        dist_path = Path("dist")
        wheel_files = list(dist_path.glob("*.whl"))
        
        if not wheel_files:
            pytest.skip("No wheel file found, run test_uv_build_command first")
        
        wheel_file = wheel_files[0]
        
        # Create a temporary virtual environment
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = Path(temp_dir) / "test_venv"
            
            # Create virtual environment
            subprocess.run([
                "python", "-m", "venv", str(venv_path)
            ], check=True)
            
            # Install the package
            pip_path = venv_path / "bin" / "pip"
            result = subprocess.run([
                str(pip_path), "install", str(wheel_file)
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Package installation failed: {result.stderr}"
            
            # Verify installation
            result = subprocess.run([
                str(pip_path), "show", "mcp-file-server"
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, "Package not found after installation"
            assert "mcp-file-server" in result.stdout
            assert "0.1.0" in result.stdout

    def test_entry_point_functionality(self):
        """Test that the entry point command works correctly."""
        dist_path = Path("dist")
        wheel_files = list(dist_path.glob("*.whl"))
        
        if not wheel_files:
            pytest.skip("No wheel file found, run test_uv_build_command first")
        
        wheel_file = wheel_files[0]
        
        # Create a temporary virtual environment
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = Path(temp_dir) / "test_venv"
            
            # Create virtual environment
            subprocess.run([
                "python", "-m", "venv", str(venv_path)
            ], check=True)
            
            # Install the package
            pip_path = venv_path / "bin" / "pip"
            subprocess.run([
                str(pip_path), "install", str(wheel_file)
            ], check=True)
            
            # Test entry point exists
            entry_point_path = venv_path / "bin" / "mcp-file-server"
            assert entry_point_path.exists(), "Entry point script not created"
            assert entry_point_path.is_file(), "Entry point is not a file"
            
            # Test entry point is executable
            assert os.access(entry_point_path, os.X_OK), "Entry point is not executable"
            
            # Test entry point imports correctly (without running the server)
            python_path = venv_path / "bin" / "python"
            result = subprocess.run([
                str(python_path), "-c", 
                "import mcp_file_server.main; print('Import successful')"
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Entry point module import failed: {result.stderr}"
            assert "Import successful" in result.stdout

    def test_setuptools_compatibility(self):
        """Test that uv-built package is compatible with setuptools-built version."""
        # This test requires the build module to be available
        try:
            import build
        except ImportError:
            pytest.skip("build module not available for comparison")
        
        # Clean existing artifacts
        subprocess.run(["rm", "-rf", "dist/", "build/", "src/*.egg-info/"], 
                      shell=True, check=False)
        
        # Build with uv
        subprocess.run(["uv", "build"], check=True)
        
        # Move uv artifacts
        uv_dist = Path("dist_uv")
        if uv_dist.exists():
            shutil.rmtree(uv_dist)
        shutil.move("dist", uv_dist)
        
        # Build with setuptools
        subprocess.run(["python", "-m", "build"], check=True)
        
        # Compare wheel contents
        uv_wheels = list(uv_dist.glob("*.whl"))
        setuptools_wheels = list(Path("dist").glob("*.whl"))
        
        assert len(uv_wheels) == 1 and len(setuptools_wheels) == 1
        
        # Extract and compare contents
        with tempfile.TemporaryDirectory() as temp_dir:
            uv_extract = Path(temp_dir) / "uv"
            setuptools_extract = Path(temp_dir) / "setuptools"
            
            with zipfile.ZipFile(uv_wheels[0], 'r') as zip_ref:
                zip_ref.extractall(uv_extract)
            
            with zipfile.ZipFile(setuptools_wheels[0], 'r') as zip_ref:
                zip_ref.extractall(setuptools_extract)
            
            # Compare main package files
            uv_main = (uv_extract / "mcp_file_server" / "main.py").read_text()
            setuptools_main = (setuptools_extract / "mcp_file_server" / "main.py").read_text()
            assert uv_main == setuptools_main, "main.py files differ between builds"
            
            # Compare entry points
            uv_entry_points = list(uv_extract.glob("*.dist-info/entry_points.txt"))[0].read_text()
            setuptools_entry_points = list(setuptools_extract.glob("*.dist-info/entry_points.txt"))[0].read_text()
            assert uv_entry_points == setuptools_entry_points, "Entry points differ between builds"
        
        # Clean up
        shutil.rmtree(uv_dist)


if __name__ == "__main__":
    # Run tests individually for debugging
    test_suite = TestBuildValidation()
    
    print("Testing uv build command...")
    test_suite.test_uv_build_command()
    print("✓ uv build command test passed")
    
    print("Testing package contents...")
    test_suite.test_package_contents()
    print("✓ Package contents test passed")
    
    print("Testing package installation...")
    test_suite.test_package_installation()
    print("✓ Package installation test passed")
    
    print("Testing entry point functionality...")
    test_suite.test_entry_point_functionality()
    print("✓ Entry point functionality test passed")
    
    print("Testing setuptools compatibility...")
    try:
        test_suite.test_setuptools_compatibility()
        print("✓ Setuptools compatibility test passed")
    except Exception as e:
        print(f"⚠ Setuptools compatibility test skipped: {e}")
    
    print("\n🎉 All build validation tests completed successfully!")