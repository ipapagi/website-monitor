#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check specific case IDs from Excel export for enrichment."""

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
from charges import enrich_charge_with_employee
from incoming import simplify_incoming_records

# Case IDs από το Excel (sample)
target_cases = [
    '793923', '821346', '821421', '821562', '821576',
    '861485', '864888', '877554', '879020', '879026',
    '117648', '117649', '121913', '125695', '128916'
]

print("=" * 80)
print("CHECK: Specific Case IDs from Excel Export")
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
    print("❌ Failed to login")
    sys.exit(1)

print("✅ Login successful\n")

# Fetch ALL incoming records to find these cases
print("📥 Fetching incoming records (limit=200)...")
params = {'queryId': 6, 'limit': 200}
incoming_data = monitor.fetch_data(params)
incoming_records = incoming_data.get('data', []) if incoming_data else []
simplified = simplify_incoming_records(incoming_records)

print(f"   Found {len(simplified)} records")
print()

# Find target cases in records
found_cases = {}
for rec in simplified:
    case_id = rec.get('case_id')
    if case_id in target_cases:
        found_cases[case_id] = rec

print(f"✅ Found {len(found_cases)}/{len(target_cases)} target cases in incoming records")
print()

# Try enrichment for found cases
print("-" * 80)
print("ENRICHMENT TEST")
print("-" * 80)

enriched_success = 0
enriched_failed = 0

for case_id in target_cases:
    if case_id not in found_cases:
        print(f"❌ Case {case_id}: NOT FOUND in incoming records")
        continue
    
    rec = found_cases[case_id]
    doc_id = rec.get('doc_id')
    party = rec.get('party', 'N/A')[:40]
    
    if not doc_id:
        print(f"⚠️  Case {case_id}: No doc_id")
        enriched_failed += 1
        continue
    
    # Try enrichment
    employee = enrich_charge_with_employee(monitor, doc_id)
    
    if employee:
        print(f"✅ Case {case_id} (doc_id: {doc_id}): {employee}")
        enriched_success += 1
    else:
        print(f"❌ Case {case_id} (doc_id: {doc_id}): No employee found")
        enriched_failed += 1

print()
print("=" * 80)
print(f"Summary:")
print(f"  - Target cases: {len(target_cases)}")
print(f"  - Found in incoming: {len(found_cases)}")
print(f"  - Enriched successfully: {enriched_success}")
print(f"  - Failed enrichment: {enriched_failed}")
print(f"  - Success rate: {100*enriched_success/len(found_cases):.1f}%" if found_cases else "  - N/A")
print("=" * 80)
