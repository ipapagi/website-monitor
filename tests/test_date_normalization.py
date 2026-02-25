#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test date normalization."""

import sys
import os
sys.path.insert(0, 'src')

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from datetime import datetime

def test_date_normalization(date_str):
    """Test date normalization logic."""
    parsed_date = None
    
    # Try standard format
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass
    
    # Try manual parsing for formats like 2026-2-9
    if not parsed_date:
        parts = date_str.split('-')
        if len(parts) == 3:
            try:
                parsed_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                pass
    
    if not parsed_date:
        return f"ERROR: Invalid date format"
    
    normalized = parsed_date.strftime("%Y-%m-%d")
    return normalized

# Test cases
test_cases = [
    '2026-02-09',   # Already normalized
    '2026-2-9',     # No leading zeros
    '2026-2-19',    # No leading zero on month
    '2026-12-5',    # No leading zero on day
]

print("Date Normalization Test")
print("=" * 50)

for date_input in test_cases:
    normalized = test_date_normalization(date_input)
    print(f"Input:  {date_input}")
    print(f"Output: {normalized}")
    print()
