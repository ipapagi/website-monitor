#!/usr/bin/env python3
"""Direct check of W001_P_FLD10 in queryId=2 for departments"""

import sys
import os
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root

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
    print("CHECK: Department assignments in queryId=2 (direct W001_P_FLD10)")
    print("="*80)
    
    # Fetch queryId=2
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
    q2_records = data_q2.get('data', []) if data_q2 else []
    print(f"\n✅ Fetched {len(q2_records)} from queryId=2")
    
    # Count by type
    dept_count = 0
    person_count = 0
    empty_count = 0
    
    dept_examples = []
    person_examples = []
    
    for rec in q2_records:
        employee = rec.get('W001_P_FLD10', '')
        docid = rec.get('DOCID', '')
        
        if not employee:
            empty_count += 1
        elif is_department(employee):
            dept_count += 1
            if len(dept_examples) < 5:
                dept_examples.append((docid, employee))
        else:
            person_count += 1
            if len(person_examples) < 5:
                person_examples.append((docid, employee))
    
    print(f"\n📊 Assignment types in queryId=2:")
    print(f"   Department assignments: {dept_count}")
    print(f"   Personal assignments: {person_count}")
    print(f"   Empty (no assignment): {empty_count}")
    print(f"   Total: {len(q2_records)}")
    
    if dept_count > 0:
        print(f"\n✅ YES - Department assignments EXIST in queryId=2")
        print(f"\nSample department assignments:")
        for docid, emp in dept_examples:
            emp_short = emp[:70] + "..." if len(emp) > 70 else emp
            print(f"   DOCID {docid}: {emp_short}")
    else:
        print(f"\n❌ No department assignments found (strange!)")
    
    if person_count > 0:
        print(f"\nSample personal assignments:")
        for docid, emp in person_examples:
            print(f"   DOCID {docid}: {emp}")

if __name__ == '__main__':
    main()
