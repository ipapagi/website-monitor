#!/usr/bin/env python3
"""Trace the Excel generation to see what data goes where."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.report_service import load_digest
from test_users import classify_records

digest = load_digest()
incoming = digest.get("incoming", {})

records = incoming.get("records", []) or []
print(f"Total records in digest: {len(records)}")

real_rows, test_rows = classify_records(records)
print(f"After classify: real={len(real_rows)}, test={len(test_rows)}")

# Look at what's in each sheet
print("\n=== First 3 TEST ROWS ===")
for i, rec in enumerate(test_rows[:3]):
    case_id = rec.get('case_id', 'N/A')
    submission_year = rec.get('submission_year', 'N/A')
    directory = rec.get('directory_name', 'N/A')[:40] if rec.get('directory_name') else 'N/A'
    print(f"  Row {i}: case_id={case_id}, year={submission_year}")
    print(f"    directory={directory}...")

print("\n=== First 3 REAL ROWS ===")
for i, rec in enumerate(real_rows[:3]):
    case_id = rec.get('case_id', 'N/A')
    submission_year = rec.get('submission_year', 'N/A')
    directory = rec.get('directory_name', 'N/A')[:40] if rec.get('directory_name') else 'N/A'
    print(f"  Row {i}: case_id={case_id}, year={submission_year}")
    print(f"    directory={directory}...")

# Now check what protocol_num looks like in the digest
print("\n=== Protocol Numbers in records ===")
print(f"real_rows[0] protocol_num: {real_rows[0].get('protocol_num', 'N/A')}")
print(f"test_rows[0] protocol_num: {test_rows[0].get('protocol_num', 'N/A')}")
