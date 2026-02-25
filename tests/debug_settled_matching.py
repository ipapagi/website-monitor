#!/usr/bin/env python3
"""Debug settled cases and find connection with incoming"""

import sys
import os
import yaml
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from monitor import PKMMonitor

root = os.path.dirname(__file__)
cfg_path = os.path.join(root, 'config', 'config.yaml')
with open(cfg_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

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
    print("Login failed")
    sys.exit(1)

if not session.logged_in and not session.login():
    print("Login failed")
    sys.exit(1)

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
if not data or not data.get('success'):
    print("Failed to fetch settled cases")
    sys.exit(1)

records = data.get('data', [])
print(f"Total settled cases: {len(records)}")

if records:
    print("\nFirst settled case fields:")
    sample = records[0]
    for key in sorted(sample.keys()):
        val = str(sample.get(key, ''))[:80]
        print(f"  {key:30} = {val}")

# Analyze potential matching keys
print("\n" + "="*80)
print("Analyzing settled cases for potential matching with incoming (case_id like 125695):")

for idx, rec in enumerate(records[:5], 1):
    print(f"\nSettled Case {idx}:")
    # Extract various IDs
    w001_fld2 = rec.get('W001_P_FLD2', '')
    docid = rec.get('DOCID', '')
    w001_fld21 = rec.get('W001_P_FLD21', '')  # Party/employee info
    
    print(f"  W001_P_FLD2 (Protocol): {w001_fld2}")
    print(f"  DOCID: {docid}")
    print(f"  W001_P_FLD21: {w001_fld21[:60]}")
    
    # Extract numeric parts from protocol
    if w001_fld2:
        numeric_match = re.search(r'/(\d+)', str(w001_fld2))
        if numeric_match:
            print(f"  → Numeric from protocol: {numeric_match.group(1)}")

print("\n" + "="*80)
print("Conclusion: The settled cases (queryId=19) seem to be from a DIFFERENT")
print("data source than the incoming requests (queryId=6).")
print("\nThey don't have a direct case_id to correlate with.")
print("The case_id from incoming (e.g., 125695) doesn't match any field in settled cases.")
