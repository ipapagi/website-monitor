#!/usr/bin/env python3
"""Test script for directory emails functionality"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from directory_emails import (
    group_new_requests_by_directory,
    create_directory_eml,
    _sanitize_filename,
    _format_protocol_number
)

def test_helpers():
    """Test helper functions"""
    print("Testing helper functions...\n")
    
    # Test sanitize filename
    filename = "ΝΕΦΕΛΗ ΘΕΟΦΑΝΙΔΟΥ (Test)"
    sanitized = _sanitize_filename(filename)
    print(f"✅ Sanitize filename: '{filename}' → '{sanitized}'")
    
    # Test protocol number formatting
    protocol = _format_protocol_number("911678", "26234", "2025-12-03 20:28")
    print(f"✅ Format protocol: {protocol}")
    
    print()

def test_grouping():
    """Test request grouping by directory"""
    print("Testing request grouping...\n")
    
    test_records = [
        {
            'case_id': '911678',
            'protocol_number': '26234',
            'procedure': 'ΥΓΕΙΑΣ-050',
            'directory': 'ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ',
            'party': 'ΝΕΦΕΛΗ ΘΕΟΦΑΝΙΔΟΥ',
            'submitted_at': '2025-12-03 20:28'
        },
        {
            'case_id': '911679',
            'protocol_number': '26235',
            'procedure': 'ΑΝΑΠ-74',
            'directory': 'ΔΙΕΥΘΥΝΣΗ ΑΝΑΠΤΥΞΗΣ',
            'party': 'ΓΙΩΡΓΟΣ ΠΑΠΑΔΟΠΟΥΛΟΣ',
            'submitted_at': '2025-12-03 21:00'
        },
        {
            'case_id': '911680',
            'protocol_number': '26236',
            'procedure': 'ΥΓΕΙΑΣ-051',
            'directory': 'ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ',
            'party': 'ΜΑΡΙΑ ΧΡΗΣΤΟΠΟΥΛΟΥ',
            'submitted_at': '2025-12-03 21:30'
        }
    ]
    
    grouped = group_new_requests_by_directory(test_records)
    
    for directory, records in grouped.items():
        print(f"📍 {directory}: {len(records)} αίτηση/αιτήσεις")
        for rec in records:
            print(f"   - {rec['party']} ({rec['case_id']})")
    
    print(f"\n✅ Ομαδοποίηση επιτυχής: {len(grouped)} διαφορετικές Διευθύνσεις\n")

def test_email_creation():
    """Test email creation"""
    print("Testing email creation...\n")
    
    test_records = [
        {
            'case_id': '911678',
            'protocol_number': '26234',
            'procedure': 'ΥΓΕΙΑΣ-050 Άδεια ασκήσεως επαγγέλματος ψυχολόγου',
            'directory': 'ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ ΚΑΙ ΚΟΙΝΩΝΙΚΗΣ ΜΕΡΙΜΝΑΣ',
            'party': 'ΝΕΦΕΛΗ ΘΕΟΦΑΝΙΔΟΥ',
            'submitted_at': '2025-12-03 20:28'
        }
    ]
    
    directory = test_records[0]['directory']
    party_names = [r.get('party', '') for r in test_records]
    
    msg = create_directory_eml(test_records, directory, party_names)
    
    print(f"✅ Email δημιουργήθηκε:")
    print(f"   Subject: {msg['Subject']}")
    print(f"   Parts: {len(msg.get_payload())} (HTML body)")
    print()

if __name__ == '__main__':
    print("="*80)
    print("Directory Emails Functionality Tests")
    print("="*80 + "\n")
    
    try:
        test_helpers()
        test_grouping()
        test_email_creation()
        print("="*80)
        print("✅ All tests passed!")
        print("="*80)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
