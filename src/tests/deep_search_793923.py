#!/usr/bin/env python3
"""Search for 793923 in all fields of all queryIds"""

import sys
import os
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root
import json

def deep_search(monitor, search_val: str):
    """Deep search in all fields"""
    
    print(f"\n🔍 Deep searching for: {search_val}")
    print("="*80)
    
    queryIds = ['2', '3', '6', '19']
    
    for qid in queryIds:
        print(f"\n📥 QueryId={qid}...")
        params = {
            'queryId': qid,
            'queryOwner': qid,
            'isPoll': 'true',
            'stateId': 'welcomeGrid-45_dashboard0',
            'page': '1',
            'start': '0',
            'limit': '100'
        }
        
        data = monitor.fetch_data(params)
        if not data or not data.get('success'):
            print(f"   Error fetching data")
            continue
        
        records = data.get('data', [])
        print(f"   Fetched {len(records)} records")
        
        for rec in records:
            found_fields = []
            for key, val in rec.items():
                if val and str(val).find(search_val) != -1:
                    found_fields.append((key, val))
            
            if found_fields:
                print(f"\n   ✅ FOUND in record DOCID={rec.get('DOCID')}:")
                for field, val in found_fields:
                    print(f"      {field}: {val}")

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
    
    deep_search(monitor, '793923')

if __name__ == '__main__':
    sys.exit(main() or 0)
