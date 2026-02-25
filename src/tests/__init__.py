# Test utilities module
"""
Test suite organization guide.

All test, check, debug, and analyze scripts should be placed here.
Pattern: src/tests/<script_name>.py

Naming conventions:
- test_*.py       - Functional tests
- check_*.py      - Data validation checks
- debug_*.py      - Debugging utilities
- analyze_*.py    - Analysis scripts
- search_*.py     - Search utilities  
- deep_*.py       - Deep investigation scripts
"""

import sys
import os

# Add parent directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))

__all__ = ['project_root']
