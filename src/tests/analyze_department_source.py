#!/usr/bin/env python3
"""Analyze where department assignments come from"""

import sys
import os
import re
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from incoming import fetch_incoming_records, simplify_incoming_records
from charges import (
    fetch_charges,
    fetch_charges_from_queryid3,
    fetch_charges_combined,
    add_charge_info_from_combined
)

def is_department(employee_name: str) -> bool:
    """Check if employee_name is a department."""
    if not employee_name:
        return False
    
    dept_keywords = ['ΤΜΗΜΑ', 'ΔΙΕΥΘΥΝΣΗ', 'Προϊστάμενοι']
    name_upper = str(employee_name).upper()
    return any(keyword in name_upper for keyword in dept_keywords)


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
    print("ANALYSIS: Where do department assignments come from?")
    print("="*80)
    
    # Get all 3 sources
    print("\n📥 Fetching charge sources...")
    ots_records, ots_by_pkm = fetch_charges(monitor)
    q3_records, q3_by_pkm = fetch_charges_from_queryid3(monitor)
    
    print(f"✅ queryId=2 (OTS): {len(ots_by_pkm)} PKMs")
    print(f"✅ queryId=3 (Routing): {len(q3_by_pkm)} PKMs")
    
    # Fetch incoming records with combined charges
    print("\n📥 Fetching incoming records with combined charges...")
    incoming_data = monitor.fetch_data(INCOMING_DEFAULT_PARAMS)
    incoming_records = incoming_data.get('data', []) if incoming_data else []
    records = simplify_incoming_records(incoming_records)
    
    charges_records, charges_by_pkm = fetch_charges_combined(monitor)
    records = add_charge_info_from_combined(records, charges_by_pkm)
    print(f"✅ Fetched {len(records)} incoming records")
    
    # Analyze department assignments
    charged_records = [r for r in records if r.get('_charge', {}).get('charged')]
    department_assignments = [r for r in charged_records if is_department(r.get('_charge', {}).get('employee', ''))]
    
    print(f"\n" + "="*80)
    print(f"DEPARTMENT ASSIGNMENTS ANALYSIS:")
    print("="*80)
    
    print(f"\nTotal charged records: {len(charged_records)}")
    print(f"Department assignments: {len(department_assignments)}")
    print(f"Personal assignments: {len(charged_records) - len(department_assignments)}")
    
    # Check source of department assignments
    print(f"\n" + "="*80)
    print(f"SOURCE ANALYSIS: Where do department assignments come from?")
    print("="*80)
    
    dept_from_ots = 0
    dept_from_q3 = 0
    dept_mixed = 0
    
    for rec in department_assignments:
        case_id = rec.get('case_id', '')
        
        in_ots = case_id in ots_by_pkm
        in_q3 = case_id in q3_by_pkm
        
        if in_ots and in_q3:
            dept_mixed += 1
        elif in_q3:
            dept_from_q3 += 1
        else:
            dept_from_ots += 1
    
    print(f"\nDepartment assignments by source:")
    print(f"  From queryId=2 (OTS) only: {dept_from_ots}")
    print(f"  From queryId=3 (Routing) only: {dept_from_q3} ✅")
    print(f"  In BOTH sources: {dept_mixed}")
    print(f"  Total department assignments: {len(department_assignments)}")
    
    if dept_from_q3 > 0:
        pct = (dept_from_q3 / len(department_assignments)) * 100
        print(f"\n✅ CONCLUSION: {pct:.1f}% of department assignments come from queryId=3 (Routing)")
        print(f"   These are cases that have been ROUTED/FORWARDED to departments!")
    
    # Show examples
    if department_assignments:
        print(f"\n" + "="*80)
        print(f"EXAMPLES: Department assignments and their source")
        print("="*80)
        
        for i, rec in enumerate(department_assignments[:5], 1):
            case_id = rec.get('case_id', '')
            employee = rec.get('_charge', {}).get('employee', '')
            
            in_ots = "✅" if case_id in ots_by_pkm else "❌"
            in_q3 = "✅" if case_id in q3_by_pkm else "❌"
            
            emp_short = employee[:50] + "..." if len(employee) > 50 else employee
            print(f"\n{i}. PKM {case_id}")
            print(f"   Assignment: {emp_short}")
            print(f"   In queryId=2 (OTS): {in_ots}")
            print(f"   In queryId=3 (Routing): {in_q3}")

if __name__ == '__main__':
    main()
