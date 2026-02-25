#!/usr/bin/env python3
"""Debug settlement matching"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.report_service import load_digest
from incoming import simplify_incoming_records

# Load and simplify
digest = load_digest()
records = digest.get('incoming', {}).get('records', [])
simplified = simplify_incoming_records(records)

print("Sample incoming records (simplified):")
for idx, rec in enumerate(simplified[:3], 1):
    case_id = rec.get('case_id')
    submission_year = rec.get('submission_year')
    lookup_key = f"{submission_year}/{case_id}" if submission_year and case_id else "NONE"
    print(f"\n{idx}. Case ID: {case_id}, Year: {submission_year}")
    print(f"   Lookup key: {lookup_key}")
    print(f"   Document type: {rec.get('document_category')}")

# Now load settled cases
print("\n" + "="*80)
print("Loading settled cases...")

from session import PKMSession
from config import get_project_root
import yaml

root = os.path.dirname(__file__)
cfg_path = os.path.join(root, 'config', 'config.yaml')
with open(cfg_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

monitor = PKMMonitor = __import__('monitor')
from monitor import PKMMonitor

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
    print("Login failed, using environment session");
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
print(f"\nTotal settled: {len(records_settled)}")
print("\nFirst 5 settled cases (lookup keys):")
for idx, rec in enumerate(records_settled[:5], 1):
    w001_fld2 = str(rec.get('W001_P_FLD2', '')).strip()
    settled_date = str(rec.get('W001_P_FLD3', '')).strip()
    print(f"\n{idx}. W001_P_FLD2: '{w001_fld2}'")
    print(f"   Settled date: {settled_date}")
