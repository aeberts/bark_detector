#!/usr/bin/env python3
"""
Cross-platform installation script for bark detector dependencies.
Automatically detects platform and installs the correct TensorFlow version.
"""

import platform
import subprocess
import sys
import os


def get_platform_info():
    """Get platform information."""
    system = platform.system()
    machine = platform.machine()
    python_version = platform.python_version()
    return system, machine, python_version


def create_pyproject_toml():
    """Create a minimal pyproject.toml file."""
    pyproject_content = """[project]
name = "bark_detector"
version = "3.0.0"
description = "Advanced YAMNet-based bark detection system"
requires-python = ">=3.9,<3.12"

# Dependencies managed by install.py
dependencies = []
"""
    
    with open("pyproject.toml", "w") as f:
        f.write(pyproject_content)
    print("📝 Created pyproject.toml")


def install_requirements():
    """Install requirements based on platform."""
    system, machine, python_version = get_platform_info()
    
    print(f"Detected platform: {system}-{machine}")
    print(f"Python version: {python_version}")
    
    # Check Python version compatibility
    major, minor = map(int, python_version.split('.')[:2])
    if major < 3 or (major == 3 and minor < 9):
        print(f"❌ Error: Python {python_version} is not supported. Please use Python 3.9-3.11")
        return False
    elif major == 3 and minor >= 12:
        print(f"⚠️  Warning: Python {python_version} may have compatibility issues. Python 3.9-3.11 is recommended.")
    
    # Create pyproject.toml if it doesn't exist
    if not os.path.exists("pyproject.toml"):
        create_pyproject_toml()
    
    # Determine which requirements file to use
    if system == "Darwin" and machine == "arm64":
        # Apple Silicon Mac
        requirements_file = "requirements-apple-silicon.txt"
        print("Using Apple Silicon (M1/M2) requirements...")
    else:
        # Intel Mac, Linux, Windows
        requirements_file = "requirements-intel.txt"
        print("Using Intel/x86_64 requirements...")
    
    # Check if requirements file exists
    if not os.path.exists(requirements_file):
        print(f"Error: {requirements_file} not found!")
        return False
    
    # Install using uv
    try:
        print(f"Installing dependencies from {requirements_file}...")
        result = subprocess.run([
            "uv", "add", "-r", requirements_file
        ], check=True, capture_output=True, text=True)
        
        print("✅ Dependencies installed successfully!")
        print("\nTo run the bark detector:")
        print("  uv run bd.py")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Primary installation failed: {e}")
        print(f"stderr: {e.stderr}")
        
        # Try fallback requirements
        fallback_file = "requirements-fallback.txt"
        if os.path.exists(fallback_file):
            print(f"\n🔄 Trying fallback installation with {fallback_file}...")
            try:
                result = subprocess.run([
                    "uv", "add", "-r", fallback_file
                ], check=True, capture_output=True, text=True)
                
                print("✅ Fallback installation successful!")
                print("\nTo run the bark detector:")
                print("  uv run bd.py")
                return True
                
            except subprocess.CalledProcessError as e2:
                print(f"❌ Fallback installation also failed: {e2}")
                print(f"stderr: {e2.stderr}")
        
        return False
    except FileNotFoundError:
        print("❌ Error: 'uv' not found. Please install uv first:")
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False


def main():
    """Main installation function."""
    print("🐕 Bark Detector - Cross-Platform Installation")
    print("=" * 50)
    
    success = install_requirements()
    
    if success:
        print("\n✅ Installation completed successfully!")
    else:
        print("\n❌ Installation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()