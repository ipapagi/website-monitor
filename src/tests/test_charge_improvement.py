#!/usr/bin/env python3
"""Compare charge enrichment: queryId=2 only vs combined"""

import sys
import os
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from incoming import fetch_incoming_records, simplify_incoming_records
from charges import (
    fetch_charges,
    add_charge_info,
    fetch_charges_combined,
    add_charge_info_from_combined,
    print_charge_statistics
)

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
    print("TEST: Charge Enrichment Comparison")
    print("="*80)
    
    # Fetch incoming records
    print("\n📥 Fetching incoming records (queryId=6)...")
    incoming_data = monitor.fetch_data(INCOMING_DEFAULT_PARAMS)
    incoming_records = incoming_data.get('data', []) if incoming_data else []
    simplified = simplify_incoming_records(incoming_records)
    print(f"✅ Fetched {len(simplified)} incoming records")
    
    # ===== Scenario 1: queryId=2 only =====
    print("\n" + "="*80)
    print("SCENARIO 1: Using queryId=2 (OTS) only")
    print("="*80)
    
    charges_ots, charges_by_pkm_ots = fetch_charges(monitor)
    records_ots = add_charge_info(simplified.copy(), charges_by_pkm_ots)
    charged_ots = [r for r in records_ots if r.get('_charge', {}).get('charged')]
    
    print(f"\n📊 Results with queryId=2 only:")
    print_charge_statistics(records_ots)
    
    # ===== Scenario 2: Combined (queryId=2 + queryId=3) =====
    print("\n" + "="*80)
    print("SCENARIO 2: Using Combined (queryId=2 + queryId=3)")
    print("="*80)
    
    charges_combined, charges_by_pkm_combined = fetch_charges_combined(monitor)
    records_combined = add_charge_info_from_combined(simplified.copy(), charges_by_pkm_combined)
    charged_combined = [r for r in records_combined if r.get('_charge', {}).get('charged')]
    
    print(f"\n📊 Results with Combined sources:")
    print_charge_statistics(records_combined)
    
    # ===== Comparison =====
    print("\n" + "="*80)
    print("COMPARISON: queryId=2 vs Combined")
    print("="*80)
    
    charged_ots_pkms = set(r.get('case_id', '') for r in charged_ots)
    charged_combined_pkms = set(r.get('case_id', '') for r in charged_combined)
    
    new_pkms_from_q3 = charged_combined_pkms - charged_ots_pkms
    
    print(f"\nCharged with queryId=2 only:    {len(charged_ots)}")
    print(f"Charged with Combined:          {len(charged_combined)}")
    print(f"Additional from queryId=3:      {len(new_pkms_from_q3)} (+{(len(new_pkms_from_q3)/len(charged_ots)*100):.1f}%)")
    
    if new_pkms_from_q3:
        print(f"\n✅ Sample NEW cases now charged (from queryId=3):")
        for pkm in sorted(new_pkms_from_q3)[:5]:
            for rec in charged_combined:
                if rec.get('case_id') == pkm:
                    employee = rec.get('_charge', {}).get('employee', 'N/A')
                    print(f"   PKM {pkm}: {employee}")
                    break
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
