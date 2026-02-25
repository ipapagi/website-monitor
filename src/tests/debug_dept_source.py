#!/usr/bin/env python3
"""Debug: Show full record details for department assignments"""

import sys
import os
import json
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
    print("DEBUG: Department assignment source")
    print("="*80)
    
    # Fetch incoming + charges
    incoming_data = monitor.fetch_data(INCOMING_DEFAULT_PARAMS)
    incoming_records = incoming_data.get('data', []) if incoming_data else []
    records = simplify_incoming_records(incoming_records)
    
    charges_records, charges_by_pkm = fetch_charges_combined(monitor)
    records = add_charge_info_from_combined(records, charges_by_pkm)
    
    # Find ONE department assignment
    for rec in records:
        employee = rec.get('_charge', {}).get('employee', '')
        if is_department(employee):
            case_id = rec.get('case_id', '')
            print(f"\n✅ Found department assignment: PKM {case_id}")
            print(f"   Employee: {employee[:80]}")
            
            # Check where it came from
            if case_id in charges_by_pkm:
                source_rec = charges_by_pkm[case_id]
                print(f"\n📊 Source record in charges_by_pkm:")
                
                # Check which queryId it came from
                has_w001 = source_rec.get('W001_P_FLD10')
                has_user_to = source_rec.get('USER_GROUP_ID_TO')
                
                print(f"   W001_P_FLD10 (queryId=2 field): {has_w001}")
                print(f"   USER_GROUP_ID_TO (queryId=3 field): {has_user_to}")
                
                # Show ALL fields that contain "ΤΜΗΜΑ" or the department name
                print(f"\n📋 All fields containing department keywords:")
                dept_found = False
                for key, val in source_rec.items():
                    if isinstance(val, str) and ('ΤΜΗΜΑ' in val.upper() or 'ΔΙΕΥΘΥΝΣΗ' in val.upper()):
                        print(f"   {key}: {str(val)[:100]}")
                        dept_found = True
                        if val == employee:
                            print(f"   ^^^ THIS IS THE MATCH!")
                
                if not dept_found:
                    print(f"   (no fields contain ΤΜΗΜΑ/ΔΙΕΥΘΥΝΣΗ)")
                    print(f"\n   All fields in source_rec:")
                    for key, val in source_rec.items():
                        if val and isinstance(val, str) and len(str(val)) < 100:
                            print(f"   {key}: {val}")
            
            break

if __name__ == '__main__':
    main()
