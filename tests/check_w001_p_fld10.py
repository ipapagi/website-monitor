#!/usr/bin/env python3
"""Check W001_P_FLD10 data in settled cases."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from monitor import PKMMonitor
from utils import load_config

config = load_config(os.path.join(os.path.dirname(__file__), 'config', 'config.yaml'))
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

if not monitor.login():
    print("❌ Failed to login")
    sys.exit(1)

print("Fetching settled cases (queryId=19)...\n")

settled_params = {
    'isPoll': 'false',
    'queryId': '19',
    'queryOwner': '2',
    'isCase': 'false',
    'stateId': 'welcomeGrid-45_dashboard0',
    'page': '1',
    'start': '0',
    'limit': '500'
}

data = monitor.fetch_data(settled_params)

if data and data.get('success'):
    records = data.get('data', [])
    print(f"Total settled cases: {len(records)}\n")
    
    print("=" * 80)
    print("CHECKING W001_P_FLD10 (Employee who settled the case)")
    print("=" * 80)
    
    # Check first 5 records
    for i, rec in enumerate(records[:5]):
        protocol = rec.get('W001_P_FLD2', 'N/A')
        settled_date = rec.get('W001_P_FLD3', 'N/A')
        employee = rec.get('W001_P_FLD10', 'N/A')
        
        print(f"\nRecord {i+1}:")
        print(f"  Protocol (W001_P_FLD2): {protocol}")
        print(f"  Date (W001_P_FLD3): {settled_date}")
        print(f"  Employee (W001_P_FLD10): {employee}")
    
    # Statistics
    with_employee = sum(1 for r in records if r.get('W001_P_FLD10'))
    without_employee = len(records) - with_employee
    
    print("\n" + "=" * 80)
    print(f"Statistics:")
    print(f"  Total: {len(records)}")
    print(f"  With W001_P_FLD10: {with_employee}")
    print(f"  Without W001_P_FLD10: {without_employee}")
    print("=" * 80)
    
    if with_employee > 0:
        print("\n✅ W001_P_FLD10 contains employee data - should be included!")
    else:
        print("\n❌ W001_P_FLD10 is empty - nothing to add")
else:
    print("❌ Failed to fetch settled cases")
