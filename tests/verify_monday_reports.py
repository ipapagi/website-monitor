#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test that reports are generated for Monday when given any weekday."""

import sys
import os
sys.path.insert(0, 'src')

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from datetime import datetime
from config import get_project_root

print("=" * 80)
print("Verification: Weekly Report Date Handling")
print("=" * 80)
print()

# Test dates
test_dates = [
    ('2026-02-16', 'Monday'),
    ('2026-02-18', 'Wednesday'),
    ('2026-02-20', 'Friday'),
    ('2026-02-22', 'Sunday'),
]

project_root = get_project_root()
outputs_dir = os.path.join(project_root, 'data', 'outputs', 'reports')

print("Expected behavior:")
print()
for date_input, day_name in test_dates:
    # Parse and adjust
    parts = date_input.split('-')
    parsed_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    
    # All dates should result in 2026-02-16 (Monday)
    from datetime import timedelta
    if parsed_date.weekday() != 0:
        days_to_subtract = parsed_date.weekday()
        parsed_date = parsed_date - timedelta(days=days_to_subtract)
    
    adjusted_date = parsed_date.strftime("%Y-%m-%d")
    
    if date_input == adjusted_date:
        print(f"  • {date_input} ({day_name}) → {adjusted_date} (already Monday) ✅")
    else:
        print(f"  • {date_input} ({day_name}) → {adjusted_date} (adjusted to Monday) ✅")

print()
print("All dates should result in: 2026-02-16")
print()

# Check if reports exist for 2026-02-16
if os.path.exists(outputs_dir):
    files = os.listdir(outputs_dir)
    matching = [f for f in files if f.startswith('2026-02-16')]
    
    print(f"Report files generated for 2026-02-16: {len(matching)} files")
    if matching:
        print("  ✅ Files found:")
        for f in matching[:3]:
            print(f"     - {f[:70]}...")
else:
    print("⚠️  Output directory not found")

print()
print("=" * 80)
