#!/usr/bin/env python
"""Test script to verify date range logic"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from incoming import get_all_incoming_dates, load_incoming_snapshot

# Test: 2025-12-02 should load until next snapshot (2025-12-09 is next, so load only 2025-12-02)
test_date = "2025-12-02"
all_dates = sorted(get_all_incoming_dates())

print(f"Available dates: {len(all_dates)}")
print(f"Looking for: {test_date}")

try:
    start_idx = all_dates.index(test_date)
    print(f"Start index: {start_idx} ({all_dates[start_idx]})")
    
    if start_idx + 1 < len(all_dates):
        next_date = all_dates[start_idx + 1]
        print(f"Next date: {next_date} (will NOT be included)")
        dates_to_load = all_dates[start_idx:start_idx + 1]
    else:
        print(f"No next date (end of list)")
        dates_to_load = all_dates[start_idx:]
    
    print(f"\nDates to load: {dates_to_load}")
    
    # Count records in range
    total_records = 0
    for date_str in dates_to_load:
        snap = load_incoming_snapshot(date_str)
        if snap:
            count = len(snap.get('records', []))
            total_records += count
            print(f"  {date_str}: {count} records")
    
    print(f"\n✓ Total records to process: {total_records}")
    
except ValueError as e:
    print(f"✗ Date not found: {e}")
