#!/usr/bin/env python3
"""Debug: print all records from queryId=2 with 793923 in DESCRIPTION"""

import sys
import os

# Setup path for imports
from src_setup import *

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root
import json

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
        return 1
    
    print("\n📥 Fetching queryId=2...")
    params = {
        'queryId': '2',
        'queryOwner': '2',
        'isPoll': 'true',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '100'
    }
    
    data = monitor.fetch_data(params)
    if not data or not data.get('success'):
        print("❌ Error fetching data")
        return 1
    
    found = False
    for rec in data.get('data', []):
        desc = str(rec.get('DESCRIPTION', ''))
        if '793923' in desc:
            found = True
            print(f"\n{'='*80}")
            print(f"FOUND: DOCID={rec.get('DOCID')}")
            print(f"{'='*80}")
            print(f"\nAll fields:")
            for key in sorted(rec.keys()):
                val = rec[key]
                if val is not None and val != '':
                    print(f"  {key}: {val}")
            print()
    
    if not found:
        print("❌ Not found in queryId=2 records")

if __name__ == '__main__':
    sys.exit(main() or 0)
