#!/usr/bin/env python3
"""Inspect queryId=19 to see what data it contains"""

import sys
import os
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root

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
    print("INSPECTION: queryId=19 (Disputed to be Διεκπεραιωμένες)")
    print("="*80)
    
    # Fetch from queryId=19
    params = {
        'queryId': '19',
        'queryOwner': '19',
        'isCase': 'false',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '20',
        'isPoll': 'true'
    }
    
    print("\n📥 Fetching from queryId=19...")
    data = monitor.fetch_data(params)
    
    if not data or not data.get('success'):
        print(f"❌ Error fetching queryId=19")
        print(f"Response: {data}")
        return
    
    records = data.get('data', [])
    print(f"✅ Fetched {len(records)} records from queryId=19")
    
    if not records:
        print("❌ No records in queryId=19")
        return
    
    # Show structure
    print("\n" + "="*80)
    print("RECORD STRUCTURE (first record):")
    print("="*80)
    
    first = records[0]
    for key in sorted(first.keys()):
        val = str(first[key])[:100]
        print(f"  {key}: {val}")
    
    # Show samples
    print("\n" + "="*80)
    print(f"SAMPLE RECORDS (showing first 5):")
    print("="*80)
    
    for i, rec in enumerate(records[:5], 1):
        print(f"\n{i}. Record {i}:")
        print(f"   DOCID: {rec.get('DOCID', 'N/A')}")
        print(f"   DESCRIPTION: {str(rec.get('DESCRIPTION', ''))[:80]}")
        print(f"   W001_P_FLD10: {rec.get('W001_P_FLD10', 'N/A')}")
        print(f"   W007_P_FLD21: {rec.get('W007_P_FLD21', 'N/A')}")
        print(f"   TYPESTR: {rec.get('TYPESTR', 'N/A')}")
        print(f"   STATUS: {rec.get('W001_P_FLD1', 'N/A')}")
    
    # Check for departments
    print("\n" + "="*80)
    print(f"ANALYSIS: Checking if queryId=19 contains DEPARTMENT assignments:")
    print("="*80)
    
    dept_count = 0
    personal_count = 0
    
    for rec in records:
        employee = rec.get('W001_P_FLD10', '')
        if 'ΤΜΗΜΑ' in str(employee).upper() or 'Προϊστάμενοι' in str(employee):
            dept_count += 1
        else:
            personal_count += 1
    
    print(f"\n   Department assignments: {dept_count}")
    print(f"   Personal assignments: {personal_count}")
    print(f"   Total: {len(records)}")
    
    if dept_count > 0:
        print(f"\n✅ YES - queryId=19 contains DEPARTMENT assignments!")
        print(f"   This suggests queryId=19 is NOT for 'διεκπεραιωμένες' but for routing/delegation")

if __name__ == '__main__':
    main()
