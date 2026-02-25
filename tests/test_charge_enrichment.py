#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test enrichment of charges using two-step API calls"""

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
from charges import enrich_charge_with_employee, fetch_case_detail_payload, get_doc_id_from_w007_p_fld7
from incoming import simplify_incoming_records

print("=" * 80)
print("TEST: Enrichment with Two-Step API Call")
print("=" * 80)

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

# Fetch incoming records
params = {'queryId': 6, 'limit': 20}  # Increased to find more records
incoming_data = monitor.fetch_data(params)
incoming_records = incoming_data.get('data', []) if incoming_data else []

print(f"📥 Fetched {len(incoming_records)} incoming records\n")

# Simplify and test enrichment
simplified = simplify_incoming_records(incoming_records)

# Test with first 5 records (was 3)
for i, rec in enumerate(simplified[:5], 1):
    case_id = rec.get('case_id')
    doc_id = rec.get('doc_id')  # DOCID from incoming record
    party = rec.get('party', 'N/A')[:30]
    doc_type = rec.get('document_category', 'N/A')
    
    print(f"{i}. Case ID: {case_id}")
    print(f"   Doc ID: {doc_id}")
    print(f"   Party: {party}")
    print(f"   Type: {doc_type}")
    
    if not doc_id:
        print(f"   ⚠️  No DOCID in record, skipping")
        print()
        continue
    
    # Step 1: Fetch case detail (endpoint /7) using DOCID
    payload = fetch_case_detail_payload(monitor, doc_id)
    if payload:
        print(f"   ✅ Got payload: success={payload.get('success')}")
        data = payload.get('data')
        if isinstance(data, dict):
            print(f"   Data keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"   Data: list with {len(data)} items" if data else "Data: empty list")
        else:
            print(f"   Data: {type(data).__name__}")
        
        # Step 2: Extract charge DOCID from W007_P_FLD7.docIds[0]
        charge_doc_id = get_doc_id_from_w007_p_fld7(payload)
        print(f"   Charge DOCID from W007_P_FLD7: {charge_doc_id}")
        
        # Step 3: Get employee via enrichment
        employee = enrich_charge_with_employee(monitor, doc_id)
        if employee:
            print(f"   ✅ Employee (enriched): {employee}")
        else:
            print(f"   ⚠️  No employee found")
    else:
        print(f"   ❌ Failed to fetch case detail (payload=None)")
    
    print()

print("=" * 80)
print("✅ Test Complete")
print("=" * 80)
