#!/usr/bin/env python3
"""Generate test Excel with combined charges"""

import sys
import os

# Setup path for imports
from src_setup import *

from datetime import datetime
from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from incoming import fetch_incoming_records, simplify_incoming_records
from charges import fetch_charges_combined, add_charge_info_from_combined
from xls_export import build_requests_xls
from test_users import classify_records

def main():
    # Load config
    root = get_project_root()
    cfg_path = os.path.join(root, 'config', 'config.yaml')
    config = load_config(cfg_path)
    
    # Create monitor
    monitor = PKMMonitor(
        base_url=config.get('base_url', 'https://shde.pkm.gov.gr'),
        urls=config.get('urls', {}),
        api_params=config.get('api_params', {}),
        login_params=config.get('login_params', {}),
        check_interval=config.get('check_interval', 300),
        username=config.get('username'),
        password=config.get('password'),
        session_cookies=config.get('session_cookies')
    )
    
    if not monitor.logged_in and not monitor.login():
        print("❌ Login failed")
        return
    
    print("\n" + "="*80)
    print("TEST: Generate Excel with Combined Charges")
    print("="*80)
    
    # Fetch incoming records
    print("\n📥 Fetching incoming records...")
    incoming_data = monitor.fetch_data(INCOMING_DEFAULT_PARAMS)
    incoming_records = incoming_data.get('data', []) if incoming_data else []
    records = simplify_incoming_records(incoming_records)
    print(f"✅ Fetched {len(records)} incoming records")
    
    # Enrich with charges
    print("\n📋 Enriching with combined charges (queryId=2 + queryId=3)...")
    charges_records, charges_by_pkm = fetch_charges_combined(monitor)
    records = add_charge_info_from_combined(records, charges_by_pkm)
    print(f"✅ Enrichment complete")
    
    # Statistics
    charged = [r for r in records if r.get('_charge', {}).get('charged')]
    print(f"\n📊 Statistics:")
    print(f"   Total records: {len(records)}")
    print(f"   Charged: {len(charged)} ({len(charged)/len(records)*100:.1f}%)")
    print(f"   Uncharged: {len(records) - len(charged)}")
    
    # Classify records
    real_records, test_records = classify_records(records)
    print(f"\n   Real records: {len(real_records)}")
    print(f"   Test records: {len(test_records)}")
    
    # Build digest for Excel export
    digest = {
        "incoming": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "records": records,
            "real_new": real_records,
            "test_new": test_records
        }
    }
    
    # Generate Excel
    print("\n📊 Generating Excel file...")
    out_path = os.path.join(root, 'data', 'outputs', 'Διαδικασίες - εισερχόμενες αιτήσεις_COMBINED_TEST.xlsx')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    build_requests_xls(digest, scope='all', file_path=out_path)
    print(f"✅ Created: {out_path}")
    
    # Show sample
    print(f"\n✅ Sample charged records:")
    for i, rec in enumerate(charged[:3], 1):
        print(f"   {i}. PKM {rec.get('case_id')}: {rec.get('_charge', {}).get('employee', 'N/A')}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
