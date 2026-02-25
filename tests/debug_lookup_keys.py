#!/usr/bin/env python3
"""Debug settlement matching - simple version"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.report_service import load_digest
from incoming import simplify_incoming_records

# Load and simplify
digest = load_digest()
records = digest.get('incoming', {}).get('records', [])
simplified = simplify_incoming_records(records)

print("="*80)
print("INCOMING RECORDS - Lookup Keys")
print("="*80)

for idx, rec in enumerate(simplified[:10], 1):
    case_id = rec.get('case_id', '')
    submission_year = rec.get('submission_year', '')
    lookup_key = f"{submission_year}/{case_id}" if submission_year and case_id else "NO_KEY"
    doc_type = rec.get('document_category', '')
    print(f"{idx:2}. Year={submission_year} CaseID={case_id:6} → Lookup={lookup_key:15} | Type={doc_type}")

print("\n" + "="*80)
print("SETTLED CASES - Keys to match")
print("="*80)

# Check W007_P_FLD2 from one incoming record to see what it contains
if records:
    sample = records[0]
    print(f"\nAll fields in first incoming record:")
    for field in sorted(sample.keys()):
        val = sample.get(field, '')
        val_str = str(val)[:80] if val else "(empty)"
        print(f"  {field:30} = {val_str}")
