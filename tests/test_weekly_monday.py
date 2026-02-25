#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test weekly report with Monday adjustment."""

import sys
import os
sys.path.insert(0, 'src')

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from datetime import datetime, timedelta
from monitor import PKMMonitor
from utils import load_config
from charges import fetch_charges_combined, add_charge_info_from_combined
from incoming import simplify_incoming_records

# Test date: Wednesday 2026-02-18
input_date = "2026-02-18"
parts = input_date.split('-')
parsed_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))

print("=" * 80)
print("Test: Weekly Report with Monday Adjustment")
print("=" * 80)
print()

# Day names
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
print(f"Input date: {input_date} ({day_names[parsed_date.weekday()]})")

# Adjust to Monday
if parsed_date.weekday() != 0:
    days_to_subtract = parsed_date.weekday()
    parsed_date = parsed_date - timedelta(days=days_to_subtract)
    print(f"Adjusted to: {parsed_date.strftime('%Y-%m-%d')} ({day_names[parsed_date.weekday()]})")
    print()
    
    # Calculate week boundaries
    monday = parsed_date
    sunday = parsed_date + timedelta(days=6)
    print(f"Week: {monday.strftime('%Y-%m-%d')} (Monday) → {sunday.strftime('%Y-%m-%d')} (Sunday)")
else:
    print("Already Monday, no adjustment needed")

print()
print("=" * 80)
