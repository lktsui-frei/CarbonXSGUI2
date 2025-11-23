#!/usr/bin/env python
"""
Verify that all required packages are installed and importable.
Run this after installing requirements.txt to check your environment.
"""

import sys

def check_import(module_name, package_name=None):
    """Try to import a module and report status."""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✓ {package_name}")
        return True
    except ImportError as e:
        print(f"✗ {package_name}: {e}")
        return False

print("Checking required packages...\n")
print(f"Python version: {sys.version}\n")

success = True
success &= check_import("numpy")
success &= check_import("scipy")
success &= check_import("matplotlib")
success &= check_import("ujson")
success &= check_import("appdirs")

print("\nChecking Qt (PySide2)...")
pyside_ok = True
try:
    from PySide2 import QtGui, QtCore, QtWidgets
    print("✓ PySide2 - basic import")
except ImportError as e:
    print(f"✗ PySide2 - basic import: {e}")
    pyside_ok = False
    success = False

if pyside_ok:
    try:
        from qt_compat import QtGui, QtCore, Qt
        print("✓ PySide2 - qt_compat module")
    except Exception as e:
        print(f"✗ PySide2 - qt_compat module: {e}")
        success = False

print("\nChecking CarbonXS modules...")
success &= check_import("carbonxs_core")
success &= check_import("carbonxs_fit")

if success:
    print("\n✓ All packages installed successfully!")
    print("\nYou can now run: python CarbonXS_GUI.py")
    sys.exit(0)
else:
    print("\n✗ Some packages are missing or broken.")
    print("\nTroubleshooting:")
    print("1. Make sure you've activated your virtual environment")
    print("2. Run: pip install -r requirements.txt")
    print("3. If using conda: conda install -c conda-forge pyside2")
    print("4. Check the README.md for installation instructions")
    sys.exit(1)
