import sys

try:
    from PySide2 import QtGui as _QtGui, QtCore, QtWidgets
    
    # Create a combined QtGui module that includes QtWidgets
    class CombinedQtGui:
        pass
        
    QtGui = CombinedQtGui()
    
    # Populate with QtGui members
    for name in dir(_QtGui):
        if not name.startswith('_'):
            setattr(QtGui, name, getattr(_QtGui, name))
            
    # Populate with QtWidgets members
    for name in dir(QtWidgets):
        if not name.startswith('_'):
            setattr(QtGui, name, getattr(QtWidgets, name))
    
    # Add compatibility for PySide1 code that uses UnicodeUTF8
    # In Qt5/PySide2, this encoding parameter is ignored (always UTF8)
    if hasattr(QtGui, 'QApplication') and not hasattr(QtGui.QApplication, 'UnicodeUTF8'):
        QtGui.QApplication.UnicodeUTF8 = -1  # Dummy value for compatibility
    
    # Export Qt namespace
    Qt = QtCore.Qt
            
except ImportError:
    try:
        from PySide import QtGui, QtCore
        Qt = QtCore.Qt
    except ImportError:
        raise ImportError("Neither PySide2 nor PySide found. Please install PySide2.")
