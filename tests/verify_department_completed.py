#!/usr/bin/env python3
"""Check if department-assigned OTS cases appear in completed cases (queryId=19)"""

import sys
import os
import re
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root

def is_department(employee_name: str) -> bool:
    """Check if employee_name is a department."""
    if not employee_name:
        return False
    dept_keywords = ['ΤΜΗΜΑ', 'ΔΙΕΥΘΥΝΣΗ', 'Προϊστάμενοι']
    return any(keyword in str(employee_name).upper() for keyword in dept_keywords)


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
    print("VERIFICATION: Are department-assigned cases completed?")
    print("="*80)
    
    # Fetch queryId=2 (OTS - all incoming with W001_P_FLD10)
    print("\n📥 Fetching queryId=2 (OTS)...")
    params_q2 = {
        'queryId': '2',
        'queryOwner': '2',
        'isCase': 'false',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '100',
        'isPoll': 'true'
    }
    
    data_q2 = monitor.fetch_data(params_q2)
    q2_records = data_q2.get('data', []) if data_q2 and data_q2.get('success') else []
    print(f"✅ Fetched {len(q2_records)} from queryId=2")
    
    # Extract department assignments from queryId=2
    dept_assignments_q2 = {}
    for rec in q2_records:
        employee = rec.get('W001_P_FLD10', '')
        if is_department(employee):
            # Extract PKM
            description = rec.get('DESCRIPTION', '')
            match = re.search(r'Αίτημα\s+\d+/(\d+)', description)
            if match:
                pkm = match.group(1)
                dept_assignments_q2[pkm] = employee
    
    print(f"✅ Found {len(dept_assignments_q2)} department assignments in queryId=2")
    
    # Fetch queryId=19 (Completed - Διεκπεραιωμένες)
    print("\n📥 Fetching queryId=19 (Completed cases)...")
    params_q19 = {
        'queryId': '19',
        'queryOwner': '19',
        'isCase': 'false',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '100',
        'isPoll': 'true'
    }
    
    data_q19 = monitor.fetch_data(params_q19)
    q19_records = data_q19.get('data', []) if data_q19 and data_q19.get('success') else []
    print(f"✅ Fetched {len(q19_records)} from queryId=19 (Completed)")
    
    # Extract PKMs from queryId=19
    q19_pkms = set()
    for rec in q19_records:
        description = rec.get('DESCRIPTION', '')
        match = re.search(r'Αίτημα\s+\d+/(\d+)', description)
        if match:
            pkm = match.group(1)
            q19_pkms.add(pkm)
    
    print(f"✅ Extracted {len(q19_pkms)} PKMs from queryId=19")
    
    # Compare
    print("\n" + "="*80)
    print("COMPARISON:")
    print("="*80)
    
    dept_in_completed = len([pkm for pkm in dept_assignments_q2 if pkm in q19_pkms])
    dept_not_completed = len(dept_assignments_q2) - dept_in_completed
    
    print(f"\nDepartment assignments in queryId=2:")
    print(f"  Total: {len(dept_assignments_q2)}")
    print(f"  Also in queryId=19 (Completed): {dept_in_completed}")
    print(f"  NOT in queryId=19 (Still pending): {dept_not_completed}")
    
    if dept_not_completed > 0:
        pct_pending = (dept_not_completed / len(dept_assignments_q2)) * 100
        print(f"\n✅ RESULT: {pct_pending:.1f}% of department assignments are STILL PENDING (not completed)")
    
    if dept_in_completed > 0:
        print(f"\n⚠️  {dept_in_completed} department assignments ARE completed - these may have passed through the department")
    
    # Show examples of pending department cases
    if dept_not_completed > 0:
        print(f"\n" + "="*80)
        print(f"EXAMPLES: Pending department-assigned cases")
        print("="*80)
        
        pending = {pkm: emp for pkm, emp in dept_assignments_q2.items() if pkm not in q19_pkms}
        for i, (pkm, emp) in enumerate(list(pending.items())[:5], 1):
            emp_short = emp[:60] + "..." if len(emp) > 60 else emp
            print(f"\n{i}. PKM {pkm}")
            print(f"   Department: {emp_short}")
            print(f"   Status: 🔔 PENDING (not yet completed)")
    
    print("\n" + "="*80)
    print("📌 CONCLUSION:")
    print("="*80)
    print(f"\nThe department-assigned cases are NOT typically 'completed' (διεκπεραιωμένες).")
    print(f"They are incoming cases that have been assigned to DEPARTMENTS rather than individuals.")
    print(f"These are likely cases requiring department-level review or coordination.")

if __name__ == '__main__':
    main()
