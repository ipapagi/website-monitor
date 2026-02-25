#!/usr/bin/env python3
"""Compare queryId=2 vs queryId=3 charge coverage"""

import sys
import os
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root
from charges import fetch_charges

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
    print("COMPARISON: queryId=2 vs queryId=3 Charge Coverage")
    print("="*80)
    
    # Fetch queryId=2 (OTS)
    print("\n📥 Fetching queryId=2 (OTS - Εισερχόμενα από Πρωτόκολλο)...")
    ots_records, ots_by_pkm = fetch_charges(monitor)
    print(f"✅ queryId=2: {len(ots_records)} total records")
    print(f"✅ queryId=2: {len(ots_by_pkm)} unique PKMs")
    
    # Fetch queryId=3
    print("\n📥 Fetching queryId=3 (Routing/Forwarding)...")
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
    print(f"✅ queryId=3: {len(q3_records)} total records")
    
    # Extract PKMs from queryId=3 DESCRIPTION
    import re
    q3_by_pkm = {}
    for rec in q3_records:
        description = rec.get('DESCRIPTION', '')
        match = re.search(r'Αίτημα\s+\d+/(\d+)', description)
        if match:
            pkm = match.group(1)
            q3_by_pkm[pkm] = rec
    
    print(f"✅ queryId=3: {len(q3_by_pkm)} unique PKMs")
    
    # Compare coverage
    print("\n" + "="*80)
    print("📊 Coverage Analysis:")
    print("="*80)
    
    ots_pkms = set(ots_by_pkm.keys())
    q3_pkms = set(q3_by_pkm.keys())
    
    only_in_ots = ots_pkms - q3_pkms
    only_in_q3 = q3_pkms - ots_pkms
    in_both = ots_pkms & q3_pkms
    
    print(f"\nPKMs in queryId=2 (OTS):        {len(ots_pkms)}")
    print(f"PKMs in queryId=3 (Routing):   {len(q3_pkms)}")
    print(f"PKMs in BOTH:                  {len(in_both)}")
    print(f"PKMs ONLY in queryId=2:        {len(only_in_ots)}")
    print(f"PKMs ONLY in queryId=3:        {len(only_in_q3)}")
    
    # Total coverage if we use both
    total_coverage = len(ots_pkms | q3_pkms)
    print(f"\nTotal coverage (OTS ∪ Routing): {total_coverage}")
    print(f"  → Improvement: +{total_coverage - len(ots_pkms)} PKMs")
    
    # Show samples of PKMs only in queryId=3
    if only_in_q3:
        print(f"\n✅ Sample of PKMs found ONLY in queryId=3:")
        for pkm in sorted(only_in_q3)[:5]:
            user_to = q3_by_pkm[pkm].get('USER_GROUP_ID_TO', '')
            print(f"   - PKM {pkm}: {user_to}")
    
    if only_in_ots:
        print(f"\n⚠️  Sample of PKMs found ONLY in queryId=2:")
        for pkm in sorted(only_in_ots)[:5]:
            employee = ots_by_pkm[pkm].get('W001_P_FLD10', '')
            print(f"   - PKM {pkm}: {employee}")

if __name__ == '__main__':
    main()
