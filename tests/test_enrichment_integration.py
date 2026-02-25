#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test enrichment integration - όλες οι υποθέσεις χωρίς χρέωση."""

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
from charges import fetch_charges, add_charge_info
from incoming import simplify_incoming_records

print("=" * 80)
print("TEST: Enrichment Integration - Υποθέσεις χωρίς χρέωση")
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

# Fetch incoming records (more to find cases without charges)
params = {'queryId': 6, 'limit': 50}
incoming_data = monitor.fetch_data(params)
incoming_records = incoming_data.get('data', []) if incoming_data else []
simplified = simplify_incoming_records(incoming_records)

print(f"📥 Fetched {len(simplified)} incoming records")
print()

# Fetch charges
print("📋 Fetching charges...")
charges_records, charges_by_pkm = fetch_charges(monitor)
print(f"   Found {len(charges_records)} charges")
print()

# Test WITHOUT enrichment
print("-" * 80)
print("TEST 1: WITHOUT enrichment (enrich_missing=False)")
print("-" * 80)
records_without = add_charge_info(simplified, charges_by_pkm, monitor=monitor, enrich_missing=False)

without_charge = [r for r in records_without if not r.get('_charge', {}).get('charged')]
print(f"Records WITHOUT charge: {len(without_charge)}")
for i, rec in enumerate(without_charge[:5], 1):
    charge_info = rec.get('_charge', {})
    print(f"  {i}. Case {rec.get('case_id')}: charged={charge_info.get('charged')}, employee={charge_info.get('employee')}, enriched={charge_info.get('enriched')}")

print()

# Test WITH enrichment
print("-" * 80)
print("TEST 2: WITH enrichment (enrich_missing=True)")
print("-" * 80)
records_with = add_charge_info(simplified, charges_by_pkm, monitor=monitor, enrich_missing=True)

# Count enriched records
enriched_count = 0
enriched_records = []
for r in records_with:
    charge_info = r.get('_charge', {})
    if charge_info.get('enriched') and charge_info.get('charged'):
        enriched_count += 1
        enriched_records.append(r)

print(f"✅ ENRICHED records via API: {enriched_count}")
print()

# Show enriched examples
if enriched_records:
    print("Enriched Examples:")
    for i, rec in enumerate(enriched_records[:10], 1):
        case_id = rec.get('case_id')
        doc_id = rec.get('doc_id')
        party = rec.get('party', 'N/A')[:40]
        charge_info = rec.get('_charge', {})
        employee = charge_info.get('employee', 'N/A')
        
        print(f"  {i}. Case {case_id} (doc_id: {doc_id})")
        print(f"     Party: {party}")
        print(f"     Employee: {employee}")
        print(f"     Enriched: {charge_info.get('enriched')}")
        print()

# Still without charge after enrichment
still_without = [r for r in records_with if not r.get('_charge', {}).get('charged')]
print(f"Records STILL WITHOUT charge after enrichment: {len(still_without)}")
print()

print("=" * 80)
print(f"✅ Summary:")
print(f"   - Total records: {len(simplified)}")
print(f"   - Without charge (before): {len(without_charge)}")
print(f"   - Enriched via API: {enriched_count}")
print(f"   - Still without charge: {len(still_without)}")
print(f"   - Success rate: {enriched_count}/{len(without_charge)} = {100*enriched_count/len(without_charge):.1f}%" if len(without_charge) > 0 else "   - No cases without charge")
print("=" * 80)
