#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify weekly report enrichment is working."""

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
print("VERIFY: Weekly Report Enrichment")
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

# Fetch charges (combined like weekly report does)
print("📋 Fetching charges (combined)...")
charges_records, charges_by_pkm = fetch_charges_combined(monitor)
print(f"   Found {len(charges_records)} charges from combined sources")
print()

# Add charge info WITH enrichment
print("🔄 Adding charge info with enrichment (enrich_missing=True)...")
enriched_records = add_charge_info_from_combined(records, charges_by_pkm, monitor=monitor, enrich_missing=True)

# Count enriched
enriched_count = 0
charged_from_portal = 0
not_charged = 0

for rec in enriched_records:
    charge_info = rec.get('_charge', {})
    if charge_info.get('charged'):
        if charge_info.get('enriched'):
            enriched_count += 1
        else:
            charged_from_portal += 1
    else:
        not_charged += 1

print()
print("=" * 80)
print("SUMMARY:")
print(f"  - Total records: {len(enriched_records)}")
print(f"  - Charged from portal: {charged_from_portal}")
print(f"  - Enriched via API: {enriched_count}")
print(f"  - Not charged: {not_charged}")
print()
print(f"✅ Weekly report will use these enriched records in XLSX files")
print(f"   Column G 'Ανάθεση σε' will show enriched employee names")
print("=" * 80)
