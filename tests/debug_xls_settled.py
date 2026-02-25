#!/usr/bin/env python3
"""Debug settled keys matching using xls_export patterns"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import from xls_export
from xls_export import _load_settled_cases

settled_by_case_id = _load_settled_cases()

print(f"Total settled cases loaded: {len(settled_by_case_id)}\n")
print("="*80)
print("Settlement Keys (first 20):")
print("="*80)

for idx, (key, val) in enumerate(sorted(settled_by_case_id.items())[:20], 1):
    settled_date = val.get('settled_date', '')
    print(f"{idx:2}. {key:20} → Settled: {settled_date}")

# Check pattern
import re
matching = [k for k in settled_by_case_id.keys() if re.match(r'^\d{4}/\d+$', k)]
print(f"\nTotal keys matching YYYY/NNNNN pattern: {len(matching)}")
print("Sample matching keys:")
for key in matching[:10]:
    print(f"  {key}")

# Now check what incoming keys we'd be looking for
print("\n" + "="*80)
print("Example incoming lookups (would be):")
print("="*80)
print("  2026/125695 (example)")
print("  2026/124212 (would exist in settled?)", "✓" if "2026/124212" in settled_by_case_id else "✗")

# List all settled for year 2026
keys_2026 = [k for k in settled_by_case_id.keys() if k.startswith("2026/")]
print(f"\nTotal settled cases for year 2026: {len(keys_2026)}")
if keys_2026:
    print("Sample:")
    for key in sorted(keys_2026)[:10]:
        print(f"  {key}")
