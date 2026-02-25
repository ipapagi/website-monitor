"""
Test script: Ευρεία αναζήτηση για 105139 σε ΌΛΕΣ τις Διεκπεραιωμένες Υποθέσεις
"""
import os
import sys
import re
import html

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

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
    
    print("🔐 Login...")
    if not monitor.logged_in and not monitor.login():
        print("❌ Login failed")
        return
    
    print("✅ Logged in\n")
    
    # ============================================================================
    # Fetch all charges
    # ============================================================================
    print("📋 Fetching all Διεκπεραιωμένες Υποθέσεις from queryId=19...")
    charges_records, _ = fetch_charges(monitor)
    print(f"✅ Found {len(charges_records)} records\n")
    
    # ============================================================================
    # Search for 105139 in ANY DESCRIPTION
    # ============================================================================
    print("🔍 Searching for '105139' in ALL DESCRIPTION fields...\n")
    
    found_records = []
    for rec in charges_records:
        description = rec.get('DESCRIPTION', '')
        if '105139' in description or '105139' in html.unescape(description):
            found_records.append(rec)
    
    print(f"✅ Found {len(found_records)} records containing '105139'\n")
    
    if not found_records:
        print("❌ NO records found containing 105139 in DESCRIPTION")
        print("\nThis means:")
        print("  1. Case 105139 may not have been processed yet")
        print("  2. Case 105139 may be in a different status")
        print("  3. Or the PKM extraction pattern may be different")
        return
    
    # ============================================================================
    # Print details of found records
    # ============================================================================
    for i, rec in enumerate(found_records, 1):
        print(f"Record {i}:")
        print(f"  DOCID: {rec.get('DOCID', 'N/A')}")
        employee = html.unescape(rec.get('W001_P_FLD10', '')).strip()
        print(f"  Employee (W001_P_FLD10): {employee}")
        description = html.unescape(rec.get('DESCRIPTION', ''))
        print(f"  DESCRIPTION: {description[:150]}...")
        print(f"  Full DESCRIPTION: {description}\n")

if __name__ == '__main__':
    main()
