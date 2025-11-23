import sys
import os
import pytest

# Add the project root to sys.path so we can import carbonxs_core and carbonxs_fit
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
