#!/usr/bin/env python3
"""Check test vs real record case_id values."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.report_service import load_digest

digest = load_digest()
incoming = digest.get('incoming', {})

print("=== Real Records (first 10) ===")
real_rows = incoming.get('records', []) or []
print(f"Total real records: {len(real_rows)}")

for rec in real_rows[:10]:
    case_id = rec.get('case_id', 'N/A')
    submission_year = rec.get('submission_year', 'N/A')
    doc_type = rec.get('document_category', 'N/A')
    proto = rec.get('protocol_num', 'N/A')
    print(f"  case_id={case_id}, year={submission_year}, type={doc_type}, proto={proto}")

print("\n=== Test Records (first 10) ===")
try:
    from test_users import classify_records
    real_records, test_rows = classify_records(real_rows)
    print(f"Total test records: {len(test_rows)}")
    
    for rec in test_rows[:10]:
        case_id = rec.get('case_id', 'N/A')
        submission_year = rec.get('submission_year', 'N/A')
        doc_type = rec.get('document_category', 'N/A')
        proto = rec.get('protocol_num', 'N/A')
        print(f"  case_id={case_id}, year={submission_year}, type={doc_type}, proto={proto}")
except Exception as e:
    print(f"Error: {e}")
