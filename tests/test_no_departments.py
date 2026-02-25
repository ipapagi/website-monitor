#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test that departments are not showing in charge info."""

import sys
import os
sys.path.insert(0, 'src')

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from monitor import PKMMonitor
from utils import load_config
from charges import fetch_charges_combined, add_charge_info_from_combined
from incoming import simplify_incoming_records

print("=" * 80)
print("TEST: Verify NO departments in charge employee field")
print("=" * 80)
print()

# Load config and create monitor
config = load_config('config/config.yaml')
monitor = PKMMonitor(
    base_url=config['base_url'],
    urls=config['urls'],
    username=config['username'],
    password=config['password']
)

if not monitor.login():
    print("❌ Login failed")
    sys.exit(1)

print("✅ Login successful\n")

# Fetch incoming records
params = {'queryId': 6, 'limit': 50}
incoming_data = monitor.fetch_data(params)
incoming_records = incoming_data.get('data', []) if incoming_data else []
records = simplify_incoming_records(incoming_records)

print(f"📥 Fetched {len(records)} incoming records")

# Fetch charges (combined)
print("📋 Fetching charges (combined)...")
charges_records, charges_by_pkm = fetch_charges_combined(monitor)
print(f"   Found {len(charges_records)} charges from combined sources")
print()

# Add charge info WITH enrichment
print("🔄 Adding charge info with enrichment...")
enriched_records = add_charge_info_from_combined(records, charges_by_pkm, monitor=monitor, enrich_missing=True)

# Check for departments (keywords that indicate department instead of employee name)
department_keywords = [
    'ΤΜΗΜΑ', 'ΔΙΕΥΘΥΝΣΗ', 'ΥΓΕΙΑΣ', 'ΑΓΡΟΤΙΚΗΣ', 'ΟΙΚΟΝΟΜΙΑΣ',
    'ΜΕΡΙΜΝΑΣ', 'ΠΕΡΙΒΑΛΛΟΝΤΟΣ', 'ΑΝΑΠΤΥΞΗΣ', 'ΔΙΟΙΚΗΤΙΚΟ'
]

charged_count = 0
enriched_count = 0
department_issues = []

for rec in enriched_records:
    charge_info = rec.get('_charge', {})
    if charge_info.get('charged'):
        employee = charge_info.get('employee', '')
        
        if charge_info.get('enriched'):
            enriched_count += 1
        
        charged_count += 1
        
        # Check if employee contains department keywords
        if employee:
            for keyword in department_keywords:
                if keyword in employee.upper():
                    department_issues.append({
                        'case_id': rec.get('case_id'),
                        'employee': employee,
                        'enriched': charge_info.get('enriched', False)
                    })
                    break

print()
print("=" * 80)
print("RESULTS:")
print(f"  - Total records: {len(enriched_records)}")
print(f"  - Charged records: {charged_count}")
print(f"  - Enriched via API: {enriched_count}")
print()

if department_issues:
    print(f"❌ FOUND {len(department_issues)} DEPARTMENT ISSUES:")
    for issue in department_issues[:10]:
        print(f"  - Case {issue['case_id']}: '{issue['employee']}' (enriched={issue['enriched']})")
else:
    print("✅ NO DEPARTMENTS FOUND - All employees are proper names!")

print("=" * 80)
