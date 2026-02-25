#!/usr/bin/env python3
"""Debug settlement case matching logic."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.report_service import load_digest
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

# Load digest
digest = load_digest()
incoming = digest.get('incoming', {}).get('records', [])

print(f"Total incoming records: {len(incoming)}")

# Get first 3 records and show their data
print("\n=== First 3 Incoming Records ===")
for i, rec in enumerate(incoming[:3]):
    print(f"\nRecord {i}:")
    print(f"  W007_P_FLD2 (year field): {rec.get('W007_P_FLD2', 'N/A')}")
    print(f"  case_id: {rec.get('case_id', 'N/A')}")
    print(f"  submission_year: {rec.get('submission_year', 'N/A')}")
    
    # Build matching key
    submission_year = str(rec.get('submission_year', '')).strip()
    case_id = str(rec.get('case_id', '')).strip()
    
    if submission_year and case_id:
        lookup_key = f"{submission_year}/{case_id}"
        print(f"  Matching key: {lookup_key}")

# Now load settled cases and show what they look like
print("\n=== Fetching Settled Cases ===")
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
    settled_records = data.get('data', [])
    print(f"Total settled records: {len(settled_records)}")
    
    # Show first 5 settled records
    print("\nFirst 5 Settled Records:")
    for i, rec in enumerate(settled_records[:5]):
        protocol_num = str(rec.get('W001_P_FLD2', '')).strip()
        settled_date = str(rec.get('W001_P_FLD3', '')).strip()
        print(f"  {i}: W001_P_FLD2='{protocol_num}', W001_P_FLD3='{settled_date}'")
        # Also show all fields for understanding structure
        print(f"     Full record keys: {list(rec.keys())[:10]}...")
    
    # Build lookup dict
    settled_by_case_id = {}
    for rec in settled_records:
        protocol_num = str(rec.get('W001_P_FLD2', '')).strip()
        settled_date = str(rec.get('W001_P_FLD3', '')).strip()
        if protocol_num:
            settled_by_case_id[protocol_num] = {'settled_date': settled_date}
    
    print(f"\nSettled lookup dict keys (first 5): {list(settled_by_case_id.keys())[:5]}")
    
    # Now test matching
    print("\n=== Testing Matches ===")
    matches = 0
    for rec in incoming[:10]:
        submission_year = str(rec.get('submission_year', '')).strip()
        case_id = str(rec.get('case_id', '')).strip()
        
        if submission_year and case_id:
            lookup_key = f"{submission_year}/{case_id}"
            if lookup_key in settled_by_case_id:
                print(f"✅ MATCH: {lookup_key} -> {settled_by_case_id[lookup_key]['settled_date']}")
                matches += 1
            else:
                print(f"✗ No match: {lookup_key}")
    
    print(f"\nTotal matches from first 10 records: {matches}/10")
else:
    print("❌ Failed to fetch settled cases")
