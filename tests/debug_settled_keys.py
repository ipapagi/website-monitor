#!/usr/bin/env python3
"""Debug settled cases keys"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from monitor import PKMMonitor
import yaml

root = os.path.dirname(__file__)
cfg_path = os.path.join(root, 'config', 'config.yaml')
with open(cfg_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

monitor_obj = PKMMonitor(
    base_url=config.get('base_url', 'https://shde.pkm.gov.gr'),
    urls=config.get('urls', {}),
    api_params=config.get('api_params', {}),
    login_params=config.get('login_params', {}),
    check_interval=config.get('check_interval', 300),
    username=config.get('username'),
    password=config.get('password'),
    session_cookies=config.get('session_cookies')
)

if not monitor_obj.logged_in and not monitor_obj.login():
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

data = monitor_obj.fetch_data(settled_params)
if not data or not data.get('success'):
    print("Failed to fetch settled cases")
    sys.exit(1)

records_settled = data.get('data', [])
print(f"Total settled: {len(records_settled)}\n")

print("="*80)
print("SETTLED CASES - First 5 with W001_P_FLD2 (lookup key)")
print("="*80)

for idx, rec in enumerate(records_settled[:5], 1):
    w001_fld2 = str(rec.get('W001_P_FLD2', '')).strip()
    settled_date = str(rec.get('W001_P_FLD3', '')).strip()
    print(f"\n{idx}. W001_P_FLD2: '{w001_fld2}'")
    print(f"   W001_P_FLD3 (date): {settled_date}")

print("\n" + "="*80)
print("All unique W001_P_FLD2 values (lookup keys - first 20):")
print("="*80)

keys = set()
for rec in records_settled:
    key = str(rec.get('W001_P_FLD2', '')).strip()
    if key:
        keys.add(key)

for idx, key in enumerate(sorted(keys)[:20], 1):
    print(f"{idx:2}. {key}")

print(f"\nTotal unique keys: {len(keys)}")

# Check if any match pattern YYYY/NNNNNNN
import re
matching_pattern = 0
for key in keys:
    if re.match(r'^\d{4}/\d+$', key):
        matching_pattern += 1

print(f"Keys matching YYYY/NNNNN pattern: {matching_pattern}")
