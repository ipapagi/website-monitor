#!/usr/bin/env python3
"""Check queryId=3 DESCRIPTION field format"""

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
    
    print("\n📥 Fetching queryId=3 records...")
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
    q3_records = data_q3.get('data', []) if data_q3 and data_q3.get('success') else []
    
    print(f"\n✅ Fetched {len(q3_records)} records\n")
    print("="*80)
    print("Sample DESCRIPTION fields from queryId=3:")
    print("="*80)
    
    for i, rec in enumerate(q3_records[:10], 1):
        description = rec.get('DESCRIPTION', '')
        user_to = rec.get('USER_GROUP_ID_TO', '')
        user_from = rec.get('USER_ID_FROM', '')
        
        print(f"\n{i}. DESCRIPTION: {description[:100]}")
        print(f"   USER_GROUP_ID_TO:  {user_to}")
        print(f"   USER_ID_FROM:      {user_from}")
    
    # Check all available fields in first record
    if q3_records:
        print("\n" + "="*80)
        print("All fields in first record:")
        print("="*80)
        first = q3_records[0]
        for key in sorted(first.keys()):
            val = str(first[key])[:80]
            print(f"  {key}: {val}")

if __name__ == '__main__':
    main()
