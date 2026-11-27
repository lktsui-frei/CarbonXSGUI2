#!/usr/bin/env python
"""
Test that all required packages are installed and importable.
This test verifies the environment setup is correct.
"""

import pytest
import sys
import os


def test_numpy_import():
    """Test that numpy can be imported."""
    import numpy
    assert numpy is not None


def test_scipy_import():
    """Test that scipy can be imported."""
    import scipy
    assert scipy is not None


def test_matplotlib_import():
    """Test that matplotlib can be imported."""
    import matplotlib
    assert matplotlib is not None


def test_ujson_import():
    """Test that ujson can be imported."""
    import ujson
    assert ujson is not None


def test_appdirs_import():
    """Test that appdirs can be imported."""
    import appdirs
    assert appdirs is not None


@pytest.mark.skipif(
    os.getenv('CI') is not None and not os.getenv('QT_QPA_PLATFORM'),
    reason="Qt tests skipped in headless CI without QT_QPA_PLATFORM configured"
)
def test_pyside6_basic_import():
    """Test that PySide6 basic modules can be imported."""
    from PySide6 import QtGui, QtCore, QtWidgets
    assert QtGui is not None
    assert QtCore is not None
    assert QtWidgets is not None


@pytest.mark.skipif(
    os.getenv('CI') is not None and not os.getenv('QT_QPA_PLATFORM'),
    reason="Qt tests skipped in headless CI without QT_QPA_PLATFORM configured"
)
def test_qt_compat_import():
    """Test that qt_compat module works correctly."""
    from qt_compat import QtGui, QtCore, Qt
    assert QtGui is not None
    assert QtCore is not None
    assert Qt is not None


def test_carbonxs_core_import():
    """Test that carbonxs_core module can be imported."""
    import carbonxs_core
    assert carbonxs_core is not None


def test_carbonxs_fit_import():
    """Test that carbonxs_fit module can be imported."""
    import carbonxs_fit
    assert carbonxs_fit is not None


def test_python_version():
    """Test that Python version is 3.6+."""
    assert sys.version_info >= (3, 6), f"Python 3.6+ required, got {sys.version}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
