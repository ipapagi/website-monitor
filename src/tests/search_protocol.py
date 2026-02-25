#!/usr/bin/env python3
"""Search for protocol number across all sources"""

import sys
import os

# Setup path to find src modules
if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.dirname(script_dir)
    src_dir = os.path.dirname(tests_dir)
    sys.path.insert(0, src_dir)

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root

def search_by_protocol(monitor, protocol_num: str):
    """Search for protocol number in all sources"""
    
    print("\n" + "="*80)
    print(f"SEARCHING FOR PROTOCOL: {protocol_num}")
    print("="*80)
    
    results = {
        'queryId2': [],
        'queryId3': [],
        'queryId6': [],
        'queryId19': []
    }
    
    # Common parameters
    base_params = {
        'isPoll': 'true',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '100'
    }
    
    # ===== QueryId=2: OTS =====
    print("\n📥 Searching in queryId=2 (OTS)...")
    params = {**base_params, 'queryId': '2', 'queryOwner': '2'}
    data = monitor.fetch_data(params)
    if data and data.get('success'):
        for rec in data.get('data', []):
            # Search in multiple fields
            for field in ['DOCID', 'DESCRIPTION', 'W001_P_FLD1', 'W001_P_FLD2']:
                if str(rec.get(field, '')).find(protocol_num) != -1:
                    results['queryId2'].append(rec)
                    print(f"   ✅ Found in {field}: {rec.get('DOCID')}")
                    break
    if not results['queryId2']:
        print(f"   ❌ Not found")
    
    # ===== QueryId=3: Routing =====
    print("\n📥 Searching in queryId=3 (Routing)...")
    params = {**base_params, 'queryId': '3', 'queryOwner': '3'}
    data = monitor.fetch_data(params)
    if data and data.get('success'):
        for rec in data.get('data', []):
            for field in ['DOCID', 'DESCRIPTION', 'P_PROC_STEPS_COMMENTS']:
                if str(rec.get(field, '')).find(protocol_num) != -1:
                    results['queryId3'].append(rec)
                    print(f"   ✅ Found in {field}: {rec.get('DOCID')}")
                    break
    if not results['queryId3']:
        print(f"   ❌ Not found")
    
    # ===== QueryId=6: Portal =====
    print("\n📥 Searching in queryId=6 (Portal)...")
    params = {**base_params, 'queryId': '6', 'queryOwner': '6'}
    data = monitor.fetch_data(params)
    if data and data.get('success'):
        for rec in data.get('data', []):
            for field in ['DOCID', 'W007_P_FLD20', 'W007_P_FLD1']:
                if str(rec.get(field, '')).find(protocol_num) != -1:
                    results['queryId6'].append(rec)
                    print(f"   ✅ Found in {field}: {rec.get('DOCID')}")
                    break
    if not results['queryId6']:
        print(f"   ❌ Not found")
    
    # ===== QueryId=19: Completed =====
    print("\n📥 Searching in queryId=19 (Completed)...")
    params = {**base_params, 'queryId': '19', 'queryOwner': '19'}
    data = monitor.fetch_data(params)
    if data and data.get('success'):
        for rec in data.get('data', []):
            for field in ['DOCID', 'DESCRIPTION', 'W001_P_FLD1']:
                if str(rec.get(field, '')).find(protocol_num) != -1:
                    results['queryId19'].append(rec)
                    print(f"   ✅ Found in {field}: {rec.get('DOCID')}")
                    break
    if not results['queryId19']:
        print(f"   ❌ Not found")
    
    # ===== Summary =====
    print("\n" + "="*80)
    total = sum(len(v) for v in results.values())
    if total == 0:
        print(f"❌ Protocol {protocol_num} NOT FOUND in any source")
        return results
    
    print(f"✅ Found in {total} location(s)")
    
    # ===== Show Details =====
    print("\n" + "="*80)
    print("DETAILS:")
    print("="*80)
    
    if results['queryId2']:
        rec = results['queryId2'][0]
        print(f"\n📋 QueryId=2 (OTS):")
        print(f"   DOCID: {rec.get('DOCID')}")
        print(f"   DESCRIPTION: {str(rec.get('DESCRIPTION', ''))[:100]}")
        print(f"   W001_P_FLD10 (Employee): {rec.get('W001_P_FLD10')}")
    
    if results['queryId3']:
        rec = results['queryId3'][0]
        print(f"\n📋 QueryId=3 (Routing):")
        print(f"   DOCID: {rec.get('DOCID')}")
        print(f"   DESCRIPTION: {str(rec.get('DESCRIPTION', ''))[:100]}")
        print(f"   USER_GROUP_ID_TO: {rec.get('USER_GROUP_ID_TO')}")
    
    if results['queryId6']:
        rec = results['queryId6'][0]
        print(f"\n📋 QueryId=6 (Portal):")
        print(f"   DOCID: {rec.get('DOCID')}")
        print(f"   W007_P_FLD21 (Case ID): {rec.get('W007_P_FLD21')}")
        print(f"   W007_P_FLD20 (Protocol): {rec.get('W007_P_FLD20')}")
        print(f"   Party: {rec.get('W007_P_FLD26', 'N/A')}")
    
    if results['queryId19']:
        rec = results['queryId19'][0]
        print(f"\n📋 QueryId=19 (Completed):")
        print(f"   DOCID: {rec.get('DOCID')}")
        print(f"   DESCRIPTION: {str(rec.get('DESCRIPTION', ''))[:100]}")
        print(f"   W001_P_FLD10 (Completed by): {rec.get('W001_P_FLD10')}")
    
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Search for protocol number")
    parser.add_argument('protocol', help='Protocol number to search for')
    args = parser.parse_args()
    
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
    
    search_by_protocol(monitor, args.protocol)

if __name__ == '__main__':
    sys.exit(main() or 0)
