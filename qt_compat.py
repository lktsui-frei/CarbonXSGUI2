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
            
except ImportError:
    try:
        from PySide import QtGui, QtCore
    except ImportError:
        raise ImportError("Neither PySide2 nor PySide found. Please install PySide2.")
