#!/usr/bin/env python3
"""Test combined charge sources (queryId=2 + queryId=3)"""

import sys
import os
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root
from charges import (
    fetch_charges,
    fetch_charges_from_queryid3,
    fetch_charges_combined
)

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
    print("TEST: Combined Charge Sources (queryId=2 + queryId=3)")
    print("="*80)
    
    # Test 1: queryId=2 (OTS)
    print("\n📥 Test 1: Fetching from queryId=2 (OTS)...")
    ots_records, ots_by_pkm = fetch_charges(monitor)
    print(f"✅ queryId=2: {len(ots_records)} total records")
    print(f"✅ queryId=2: {len(ots_by_pkm)} unique PKMs")
    
    # Test 2: queryId=3 (Routing)
    print("\n📥 Test 2: Fetching from queryId=3 (Routing)...")
    q3_records, q3_by_pkm = fetch_charges_from_queryid3(monitor)
    print(f"✅ queryId=3: {len(q3_records)} total records")
    print(f"✅ queryId=3: {len(q3_by_pkm)} unique PKMs")
    
    # Test 3: Combined
    print("\n📥 Test 3: Fetching COMBINED (queryId=2 + queryId=3)...")
    combined_records, combined_by_pkm = fetch_charges_combined(monitor)
    print(f"✅ Combined: {len(combined_records)} total records")
    print(f"✅ Combined: {len(combined_by_pkm)} unique PKMs")
    
    # Analysis
    print("\n" + "="*80)
    print("📊 Coverage Analysis:")
    print("="*80)
    
    ots_pkms = set(ots_by_pkm.keys())
    q3_pkms = set(q3_by_pkm.keys())
    both = ots_pkms & q3_pkms
    only_ots = ots_pkms - q3_pkms
    only_q3 = q3_pkms - ots_pkms
    
    print(f"\nqueryId=2 PKMs:      {len(ots_pkms)}")
    print(f"queryId=3 PKMs:      {len(q3_pkms)}")
    print(f"Overlap (both):      {len(both)}")
    print(f"Only in queryId=2:   {len(only_ots)}")
    print(f"Only in queryId=3:   {len(only_q3)}")
    print(f"\nTotal unique PKMs:   {len(combined_by_pkm)}")
    if len(ots_pkms) > 0:
        improvement = ((len(combined_by_pkm) - len(ots_pkms)) / len(ots_pkms)) * 100
        print(f"Improvement over OTS: +{improvement:.1f}%")
    
    # Show samples
    print(f"\n✅ Sample queryId=3 PKMs that enhance coverage:")
    for pkm in sorted(only_q3)[:5]:
        user_to = q3_by_pkm[pkm].get('USER_GROUP_ID_TO', '')
        print(f"   - PKM {pkm}: {user_to}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
