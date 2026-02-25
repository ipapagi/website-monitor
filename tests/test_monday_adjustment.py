#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Monday adjustment logic."""

import sys
import os
sys.path.insert(0, 'src')

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from datetime import datetime, timedelta

def test_monday_adjustment(date_str):
    """Test if date gets adjusted to previous Monday."""
    # Parse date
    parts = date_str.split('-')
    parsed_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    
    # Get day name
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_name = day_names[parsed_date.weekday()]
    
    # Adjust if not Monday
    original_date = parsed_date
    if parsed_date.weekday() != 0:
        days_to_subtract = parsed_date.weekday()
        parsed_date = parsed_date - timedelta(days=days_to_subtract)
    
    adjusted_date = parsed_date.strftime("%Y-%m-%d")
    adjusted_day = day_names[parsed_date.weekday()]
    
    return {
        'input': date_str,
        'input_day': day_name,
        'output': adjusted_date,
        'output_day': adjusted_day,
        'adjusted': original_date.weekday() != 0
    }

# Test cases
test_cases = [
    '2026-02-16',  # Monday - should stay same
    '2026-02-17',  # Tuesday - should go to 2026-02-16
    '2026-02-18',  # Wednesday - should go to 2026-02-16
    '2026-02-19',  # Thursday - should go to 2026-02-16
    '2026-02-20',  # Friday - should go to 2026-02-16
    '2026-02-21',  # Saturday - should go to 2026-02-16
    '2026-02-22',  # Sunday - should go to 2026-02-16
    '2026-02-23',  # Monday - should stay same
]

print("=" * 80)
print("Test: Monday Adjustment Logic")
print("=" * 80)
print()

for date_input in test_cases:
    result = test_monday_adjustment(date_input)
    
    status = "ADJUST" if result['adjusted'] else "KEEP"
    arrow = "→" if result['adjusted'] else "="
    
    print(f"{result['input']} ({result['input_day']:<10}) {arrow} {result['output']} ({result['output_day']:<10})  [{status}]")

print()
print("=" * 80)
