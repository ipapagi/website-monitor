import os
import sys

def setup_test_path():
    """Setup Python path for test files to find src modules."""
    # Get the src directory path
    # Tests are in: website-monitor/tests/
    # Src is in: website-monitor/src/
    src_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'src'
    )
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    return src_path
