#!/usr/bin/env python3
"""Get full details for DOCID=42062"""

import sys
import os

# Setup path for imports
from src_setup import *

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root

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
    
    # Get queryId=2 data
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
    
    for rec in data.get('data', []):
        if rec.get('DOCID') == 42062:
            print("\n" + "="*80)
            print("DOCID=42062 (Protocol 793923)")
            print("="*80)
            
            print(f"\n📋 Key Fields:")
            print(f"   DOCID: {rec.get('DOCID')}")
            print(f"   DESCRIPTION: {rec.get('DESCRIPTION')}")
            print(f"   W001_P_FLD10 (Employee/Charge): {rec.get('W001_P_FLD10') or 'EMPTY'}")
            print(f"   W001_P_FLD1 (Protocol): {rec.get('W001_P_FLD1')}")
            print(f"   W001_P_FLD2: {rec.get('W001_P_FLD2')}")
            print(f"   W001_P_FLD3: {rec.get('W001_P_FLD3')}")
            print(f"   W001_P_FLD9: {rec.get('W001_P_FLD9')}")
            print(f"   DATE_INSERTED_ISO: {rec.get('DATE_INSERTED_ISO')}")
            
            # Check queryId3 for the same PKM
            import re
            match = re.search(r'Αίτημα\s+\d+/(\d+)', rec.get('DESCRIPTION', ''))
            if match:
                pkm = match.group(1)
                print(f"\n   📊 PKM extracted: {pkm}")
                
                # Now check queryId=3
                params3 = {
                    'queryId': '3',
                    'queryOwner': '3',
                    'isPoll': 'true',
                    'page': '1',
                    'start': '0',
                    'limit': '100'
                }
                
                data3 = monitor.fetch_data(params3)
                if data3 and data3.get('success'):
                    for rec3 in data3.get('data', []):
                        desc = rec3.get('DESCRIPTION', '')
                        if pkm in str(desc):
                            print(f"\n   ✅ ALSO FOUND in queryId=3 (Routing):")
                            print(f"      USER_GROUP_ID_TO (Charge): {rec3.get('USER_GROUP_ID_TO')}")
                            print(f"      USER_ID_FROM: {rec3.get('USER_ID_FROM')}")

if __name__ == '__main__':
    sys.exit(main() or 0)
