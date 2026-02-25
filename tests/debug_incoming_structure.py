#!/usr/bin/env python3
"""Debug incoming records structure"""

import sys
import os
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.report_service import load_digest
from incoming import simplify_incoming_records

digest = load_digest()
records = digest.get('incoming', {}).get('records', [])

print(f"Total records: {len(records)}")
print("\nFirst 5 incoming records fields:")
if records:
    sample = records[0]
    for key in sorted(sample.keys()):
        val = str(sample.get(key, ''))[:80]
        print(f"  {key:30} = {val}")

print("\n" + "="*80)
print("Sample simplified records:")
simplified = simplify_incoming_records(records)

for idx, rec in enumerate(simplified[:5], 1):
    print(f"\nRecord {idx}:")
    for key, val in rec.items():
        print(f"  {key:25} = {str(val)[:60]}")
