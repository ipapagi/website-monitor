#!/usr/bin/env python3
"""Test related cases handling in Excel export"""

import sys
sys.path.insert(0, 'src')

from incoming import simplify_incoming_records
from xls_export import _format_protocol
from test_users import classify_records

# Simulate incoming data with a supplement (related case)
incoming_raw = [
    {
        'W007_P_FLD21': '125695',  # case_id
        'W007_P_FLD2': '2026-02-18',  # submission_year
        'W007_P_FLD3': '2026-02-18 10:00:00',  # submitted_at
        'W007_P_FLD13': 'ΠΑΥΛΙΔΟΥ ΟΛΓΑ',  # party
        'W007_P_FLD6': 'Αίτηση',  # subject/title
        'W007_P_FLD22': '12345',  # protocol_number
        'W007_P_FLD23': 'Διαδικασία Α',  # procedure
        'W007_P_FLD17': 'Διεύθυνση Α',  # directory
        'W007_P_FLD30': 'Αίτηση',  # document_category
    },
    {
        'W007_P_FLD21': '125696',  # case_id
        'W007_P_FLD2': '2026-02-18',  # submission_year
        'W007_P_FLD3': '2026-02-18 11:00:00',  # submitted_at
        'W007_P_FLD13': 'ΠΑΥΛΙΔΟΥ ΟΛΓΑ',  # party
        'W007_P_FLD6': 'Συμπληρωματικό Αίτημα',  # subject/title
        'W007_P_FLD7': '2026/125695',  # related_case - Αφορά Υπόθεση
        'W007_P_FLD22': '12346',  # protocol_number
        'W007_P_FLD23': 'Διαδικασία Α',  # procedure
        'W007_P_FLD17': 'Διεύθυνση Α',  # directory
        'W007_P_FLD30': 'Συμπληρωματικά',  # document_category
    }
]

print("=" * 80)
print("TEST: Related Cases (Supplements)")
print("=" * 80)

# Simplify records
simplified = simplify_incoming_records(incoming_raw)

print(f"\n📋 Simplified records: {len(simplified)}")
for i, rec in enumerate(simplified, 1):
    print(f"\n{i}. Document Type: {rec.get('document_category')}")
    print(f"   case_id: {rec.get('case_id')}")
    print(f"   related_case: {rec.get('related_case')}")
    print(f"   subject: {rec.get('subject')}")
    
    # Test _format_protocol
    protocol_str = _format_protocol(rec)
    print(f"   Protocol String: {protocol_str}")

print("\n" + "=" * 80)
print("✅ Expected Results:")
print("  Record 1 (Normal): '125695(12345)/18-02-2026'")
print("  Record 2 (Supplement): '2026/125695' (related case number)")
print("=" * 80)
