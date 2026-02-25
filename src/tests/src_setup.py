#!/usr/bin/env python3
"""
Setup module for test scripts.

This module configures the Python path so that test scripts can import
from the src/ directory regardless of where they're run from.

Usage in any test script:
    from src_setup import *
    from monitor import PKMMonitor
    from charges import fetch_charges
"""

import sys
import os

# Configure path: Add src/ to sys.path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_script_dir))
_src_dir = os.path.join(_project_root, 'src')

if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Now all imports from src/ will work
__all__ = []
