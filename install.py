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
    return system, machine


def install_requirements():
    """Install requirements based on platform."""
    system, machine = get_platform_info()
    
    print(f"Detected platform: {system}-{machine}")
    
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
        print(f"❌ Error installing dependencies: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
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