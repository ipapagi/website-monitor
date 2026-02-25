#!/usr/bin/env python3
"""Check queryId=3 for department vs person assignments"""

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
    print("CHECK: Department assignments in queryId=3 (USER_GROUP_ID_TO)")
    print("="*80)
    
    # Fetch queryId=3
    params_q3 = {
        'queryId': '3',
        'queryOwner': '3',
        'isCase': 'false',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '100',
        'isPoll': 'true'
    }
    
    data_q3 = monitor.fetch_data(params_q3)
    q3_records = data_q3.get('data', []) if data_q3 else []
    print(f"\n✅ Fetched {len(q3_records)} from queryId=3")
    
    # Count by type
    dept_count = 0
    person_count = 0
    empty_count = 0
    
    dept_examples = []
    
    for rec in q3_records:
        to = rec.get('USER_GROUP_ID_TO', '')
        docid = rec.get('DOCID', '')
        
        if not to:
            empty_count += 1
        elif is_department(to):
            dept_count += 1
            if len(dept_examples) < 5:
                dept_examples.append((docid, to))
        else:
            person_count += 1
    
    print(f"\n📊 Assignment types (USER_GROUP_ID_TO) in queryId=3:")
    print(f"   Department assignments: {dept_count}")
    print(f"   Personal assignments: {person_count}")
    print(f"   Empty: {empty_count}")
    print(f"   Total: {len(q3_records)}")
    
    if dept_count > 0:
        print(f"\n✅ YES - {dept_count} Department assignments in queryId=3!")
        print(f"\nExamples:")
        for docid, emp in dept_examples:
            emp_short = emp[:70] + "..." if len(emp) > 70 else emp
            print(f"   DOCID {docid}: {emp_short}")
        
        # Now check if they're in queryId=19
        print(f"\n" + "="*80)
        print("CHECKING IF THEY'RE COMPLETED:")
        print("="*80)
        
        # Fetch queryId=19
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
        q19_records = data_q19.get('data', []) if data_q19 else []
        q19_docids = set(rec.get('DOCID', '') for rec in q19_records)
        
        print(f"✅ Fetched {len(q19_records)} from queryId=19 (Completed)")
        
        dept_completed = 0
        for rec in q3_records:
            to = rec.get('USER_GROUP_ID_TO', '')
            docid = rec.get('DOCID', '')
            
            if is_department(to):
                if docid in q19_docids:
                    dept_completed += 1
        
        print(f"\nDepartment assignments from queryId=3:")
        print(f"  Total: {dept_count}")
        print(f"  Found in queryId=19 (Completed): {dept_completed}")
        print(f"  NOT completed (still pending): {dept_count - dept_completed}")
        
        if dept_count - dept_completed > 0:
            pct = ((dept_count - dept_completed) / dept_count) * 100
            print(f"\n✅ ANSWER: {pct:.1f}% of department assignments are STILL PENDING")
            print(f"   They are NOT completed/διεκπεραιωμένες")

if __name__ == '__main__':
    main()
