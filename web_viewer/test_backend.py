#!/usr/bin/env python3
"""
Test script to diagnose backend startup issues
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def test_backend_startup():
    """Test backend startup and report detailed diagnostics"""
    print("=== Backend Startup Diagnostics ===")
    
    # Get current directory info
    current_dir = Path.cwd()
    script_dir = Path(__file__).parent
    backend_dir = script_dir / "backend"
    
    print(f"Current directory: {current_dir}")
    print(f"Script directory: {script_dir}")
    print(f"Backend directory: {backend_dir}")
    print(f"Backend directory exists: {backend_dir.exists()}")
    
    # Check Python environment
    print(f"\nPython executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
    
    # Check backend files
    main_py = backend_dir / "main.py"
    requirements_txt = backend_dir / "requirements.txt"
    
    print(f"\nBackend files:")
    print(f"  main.py exists: {main_py.exists()}")
    print(f"  requirements.txt exists: {requirements_txt.exists()}")
    
    if backend_dir.exists():
        backend_files = list(backend_dir.iterdir())
        print(f"  Backend directory contents: {[f.name for f in backend_files]}")
    
    # Test Python import capabilities
    print(f"\nTesting Python imports:")
    required_modules = ['flask', 'flask_socketio', 'flask_cors', 'clr']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  [OK] {module} - OK")
        except ImportError as e:
            print(f"  [FAIL] {module} - FAILED: {e}")
    
    # Test backend startup
    if main_py.exists():
        print(f"\nTesting backend startup...")
        # Test with different Python commands
        python_commands = ["python", "python.exe", "py", "py.exe", sys.executable]
        
        for python_cmd in python_commands:
            print(f"\nTrying {python_cmd}:")
            try:
                # Test version first
                version_result = subprocess.run(
                    [python_cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if version_result.returncode == 0:
                    print(f"  Version: {version_result.stdout.strip()}")
                    
                    # Test import check
                    import_test = subprocess.run(
                        [python_cmd, "-c", "import flask; import flask_socketio; import flask_cors; print('Imports OK')"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=str(backend_dir)
                    )
                    
                    if import_test.returncode == 0:
                        print(f"  Import test: [OK] {import_test.stdout.strip()}")
                        
                        # Test main.py syntax
                        syntax_test = subprocess.run(
                            [python_cmd, "-m", "py_compile", "main.py"],
                            capture_output=True,
                            text=True,
                            timeout=10,
                            cwd=str(backend_dir)
                        )
                        
                        if syntax_test.returncode == 0:
                            print(f"  Syntax test: [OK] main.py compiles OK")
                        else:
                            print(f"  Syntax test: [FAIL] {syntax_test.stderr}")
                            
                    else:
                        print(f"  Import test: [FAIL] {import_test.stderr}")
                else:
                    print(f"  Version check failed: {version_result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"  Timeout with {python_cmd}")
            except FileNotFoundError:
                print(f"  {python_cmd} not found")
            except Exception as e:
                print(f"  Error with {python_cmd}: {e}")
    
    print(f"\n=== Diagnostics Complete ===")

if __name__ == "__main__":
    test_backend_startup()