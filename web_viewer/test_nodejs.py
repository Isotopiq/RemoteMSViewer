#!/usr/bin/env python3
"""
Node.js and npm Test Script for ThermoAPI Server Manager GUI
Run this script to verify Node.js and npm are properly installed and accessible.
"""

import subprocess
import sys
import os
from pathlib import Path

def test_command(cmd_list, description):
    """Test if a command can be executed"""
    for cmd in cmd_list:
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✓ {description} ({cmd}) - Version: {result.stdout.strip()}")
                return True, cmd
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            print(f"✗ {description} ({cmd}) - Error: {e}")
            continue
    
    return False, None

def test_frontend_directory():
    """Test if frontend directory exists and has package.json"""
    script_dir = Path(__file__).parent
    frontend_dir = script_dir / "frontend"
    
    print(f"\nTesting frontend directory: {frontend_dir}")
    
    if not frontend_dir.exists():
        print(f"✗ Frontend directory not found: {frontend_dir}")
        return False
    
    print(f"✓ Frontend directory exists: {frontend_dir}")
    
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print(f"✗ package.json not found: {package_json}")
        return False
    
    print(f"✓ package.json exists: {package_json}")
    
    # Check if node_modules exists
    node_modules = frontend_dir / "node_modules"
    if node_modules.exists():
        print(f"✓ node_modules directory exists: {node_modules}")
    else:
        print(f"⚠ node_modules directory not found: {node_modules}")
        print("  You may need to run 'npm install' in the frontend directory")
    
    return True

def test_npm_scripts():
    """Test if npm scripts can be listed"""
    script_dir = Path(__file__).parent
    frontend_dir = script_dir / "frontend"
    
    if not frontend_dir.exists():
        return False
    
    npm_commands = ["npm", "npm.cmd", "npm.exe"]
    
    for npm_cmd in npm_commands:
        try:
            result = subprocess.run(
                [npm_cmd, "run"],
                cwd=str(frontend_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"\n✓ npm scripts available ({npm_cmd}):")
                print(result.stdout)
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            continue
    
    print("\n✗ Could not list npm scripts")
    return False

def main():
    print("ThermoAPI Server Manager GUI - Node.js/npm Test")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print()
    
    print("Testing Node.js and npm availability:")
    print("-" * 40)
    
    # Test Node.js
    node_success, node_cmd = test_command(
        ["node", "node.exe"],
        "Node.js"
    )
    
    # Test npm
    npm_success, npm_cmd = test_command(
        ["npm", "npm.cmd", "npm.exe"],
        "npm"
    )
    
    # Test frontend directory
    frontend_success = test_frontend_directory()
    
    # Test npm scripts
    if npm_success and frontend_success:
        scripts_success = test_npm_scripts()
    else:
        scripts_success = False
    
    print()
    print("Summary:")
    print("-" * 10)
    
    if node_success and npm_success and frontend_success:
        print("✓ All Node.js/npm requirements are met!")
        print("✓ The GUI should be able to start the frontend server.")
        
        if not scripts_success:
            print("⚠ Consider running 'npm install' in the frontend directory")
        
        print()
        print("Next steps:")
        print("1. Run the GUI: python server_manager_gui.py")
        print("2. Or build executable: build_gui_path_fix.bat")
    else:
        print("✗ Some requirements are missing.")
        print()
        print("Required fixes:")
        
        if not node_success:
            print("- Install Node.js from https://nodejs.org")
        
        if not npm_success:
            print("- npm should come with Node.js installation")
            print("- Check if Node.js was installed correctly")
        
        if not frontend_success:
            print("- Ensure frontend directory and package.json exist")
            print("- Run 'npm install' in the frontend directory")
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()