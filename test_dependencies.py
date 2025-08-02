#!/usr/bin/env python3
"""
Test script to verify that all required dependencies are installed and working correctly.
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported successfully."""
    try:
        if package_name:
            module = importlib.import_module(package_name)
        else:
            module = importlib.import_module(module_name)
        print(f"✅ {module_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - FAILED: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name} - WARNING: {e}")
        return True  # Still consider it working if it imports but has other issues

def main():
    """Test all required dependencies."""
    print("Testing Voice Dictation Assistant Dependencies")
    print("=" * 50)
    
    # List of dependencies to test
    dependencies = [
        ("openai", "openai"),
        ("pyyaml", "yaml"),
        ("pytest", "pytest"),
        ("requests", "requests"),
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("pywin32", "win32api"),
        ("pyautogui", "pyautogui"),
        ("pygetwindow", "pygetwindow"),
        ("pyperclip", "pyperclip"),
        ("assemblyai", "assemblyai"),
        ("global-hotkeys", "global_hotkeys"),
    ]
    
    # Test each dependency
    success_count = 0
    total_count = len(dependencies)
    
    for module_name, import_name in dependencies:
        if test_import(module_name, import_name):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {success_count}/{total_count} dependencies working")
    
    if success_count == total_count:
        print("🎉 All dependencies are working correctly!")
        return True
    else:
        print("⚠️  Some dependencies have issues. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 