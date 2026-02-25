#!/usr/bin/env python3
"""Find where the department assignments really come from"""

import sys
import os
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from incoming import fetch_incoming_records, simplify_incoming_records
from charges import fetch_charges_combined, add_charge_info_from_combined

def is_department(name: str) -> bool:
    if not name:
        return False
    return any(kw in str(name).upper() for kw in ['ΤΜΗΜΑ', 'ΔΙΕΥΘΥΝΣΗ', 'Προϊστάμενοι'])


def main():
    root = get_project_root()
    cfg_path = os.path.join(root, 'config', 'config.yaml')
    config = load_config(cfg_path)
    
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
    print("SEARCH: Where do 'department assignments' come from?")
    print("="*80)
    
    # Fetch and enrich incoming records
    print("\n📥 Fetching incoming records...")
    incoming_data = monitor.fetch_data(INCOMING_DEFAULT_PARAMS)
    incoming_records = incoming_data.get('data', []) if incoming_data else []
    records = simplify_incoming_records(incoming_records)
    
    charges_records, charges_by_pkm = fetch_charges_combined(monitor)
    records = add_charge_info_from_combined(records, charges_by_pkm)
    print(f"✅ Fetched {len(records)} incoming records")
    
    # Find department assignments
    charged = [r for r in records if r.get('_charge', {}).get('charged')]
    depts = [r for r in charged if is_department(r.get('_charge', {}).get('employee', ''))]
    
    print(f"✅ Found {len(depts)} department assignments")
    
    if not depts:
        print("❌ No department assignments found!")
        return
    
    # Show details
    print(f"\n" + "="*80)
    print(f"EXAMPLES: {len(depts)} Department-assigned cases")
    print("="*80)
    
    for i, rec in enumerate(depts[:5], 1):
        case_id = rec.get('case_id', '')
        employee = rec.get('_charge', {}).get('employee', '')
        doc_id = rec.get('_charge', {}).get('doc_id', '')
        
        emp_short = employee[:60] + "..." if len(employee) > 60 else employee
        
        print(f"\n{i}. PKM {case_id}, DOCID {doc_id}")
        print(f"   Assignment: {emp_short}")
    
    # Key insight
    print(f"\n" + "="*80)
    print(f"KEY INSIGHT:")
    print("="*80)
    print(f"\nThese {len(depts)} department assignments come from the combined charges (queryId=2 + queryId=3).")
    print(f"\nBUT we discovered:")
    print(f"  • queryId=2 (OTS) W001_P_FLD10: ALL EMPTY")
    print(f"  • queryId=3 (Routing) USER_GROUP_ID_TO: NO departments found")
    print(f"\nWhere are they coming from? Possible explanations:")
    print(f"  1. They come from OTHER field in queryId=3 (not USER_GROUP_ID_TO)")
    print(f"  2. They come from queryId=6 original incoming data")
    print(f"  3. They're added during enrichment from other source")
    print(f"\nLet me check queryId=6 directly...")

if __name__ == '__main__':
    main()
