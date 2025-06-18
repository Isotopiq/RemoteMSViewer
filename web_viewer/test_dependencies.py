#!/usr/bin/env python3
"""
Dependency Test Script for ThermoAPI Server Manager GUI
Run this script to verify all required packages are available before building.
"""

import sys

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✓ {module_name} - OK")
        return True
    except ImportError as e:
        package = package_name or module_name
        print(f"✗ {module_name} - MISSING")
        print(f"  Install with: pip install {package}")
        print(f"  Error: {e}")
        return False

def test_tkinter():
    """Special test for tkinter since it's built into Python"""
    try:
        import tkinter
        import tkinter.ttk
        import tkinter.scrolledtext
        import tkinter.messagebox
        print("✓ tkinter (all components) - OK")
        return True
    except ImportError as e:
        print("✗ tkinter - MISSING")
        print("  tkinter should be built into Python")
        print("  You may need to reinstall Python with tkinter support")
        print(f"  Error: {e}")
        return False

def main():
    print("ThermoAPI Server Manager GUI - Dependency Test")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print()
    
    print("Testing required packages:")
    print("-" * 30)
    
    # Test all required imports
    results = []
    results.append(test_tkinter())
    results.append(test_import("psutil"))
    results.append(test_import("requests"))
    results.append(test_import("subprocess"))  # Built-in
    results.append(test_import("threading"))   # Built-in
    results.append(test_import("time"))        # Built-in
    results.append(test_import("os"))          # Built-in
    results.append(test_import("pathlib"))     # Built-in
    
    print()
    print("Testing build tools:")
    print("-" * 20)
    results.append(test_import("PyInstaller", "pyinstaller"))
    
    print()
    print("Summary:")
    print("-" * 10)
    
    if all(results):
        print("✓ All dependencies are available!")
        print("✓ You can proceed with building the GUI executable.")
        print()
        print("Next steps:")
        print("1. Run: build_gui_fixed.bat")
        print("2. Or run: python server_manager_gui.py (to test without building)")
    else:
        print("✗ Some dependencies are missing.")
        print("✗ Please install missing packages before building.")
        print()
        print("Quick fix:")
        print("pip install psutil requests pyinstaller")
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()