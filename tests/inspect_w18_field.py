#!/usr/bin/env python
"""
Εξετάζει το format του W007_P_FLD18 (department) field για να δούμε πώς εμφανίζεται η Γενική Διεύθυνση
"""
import sys
sys.path.insert(0, './src')

from pathlib import Path
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from utils import load_config
from monitor import PKMMonitor
from incoming import fetch_incoming_records, simplify_incoming_records
from api import enrich_record_details

# Load config
root = Path(get_project_root())
config = load_config(str(root / 'config' / 'config.yaml'))

# Connect
print("🔐 Σύνδεση...\n")
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
    print("❌ Login failed")
    sys.exit(1)

# Fetch
incoming_params = config.get('incoming_api_params', INCOMING_DEFAULT_PARAMS).copy()
data = fetch_incoming_records(monitor, incoming_params)
records = simplify_incoming_records(data.get('data', []))

# Enrich
print(f"🔄 Enriching {len(records)} records...\n")
enrich_record_details(monitor, records)

print("📋 SAMPLE W007_P_FLD18 VALUES:\n")
print("=" * 100)

# Show first 5 records
for idx, rec in enumerate(records[:5]):
    w18 = rec.get('W007_P_FLD18', '')
    gd = rec.get('general_directorate', '')
    
    print(f"\nRecord {idx} (Case ID: {rec.get('case_id')}):")
    print(f"  W007_P_FLD18 (raw):")
    print(f"    {w18}")
    print(f"  General Directorate:")
    print(f"    {gd}")
    
    # Check if parentheses exist
    if '(' in w18:
        # Extract content in parentheses
        parts = w18.split('(', 1)
        before_paren = parts[0].strip()
        in_paren = parts[1].rsplit(')', 1)[0] if ')' in parts[1] else parts[1]
        print(f"  Department (before parenthesis):")
        print(f"    {before_paren}")
        print(f"  Content in parentheses:")
        print(f"    {in_paren}")
        
        # Check if general directorate is in parentheses
        if '\\' in in_paren:
            path_parts = [p.strip() for p in in_paren.split('\\')]
            print(f"  Path parts (split by \\):")
            for j, part in enumerate(path_parts):
                print(f"    [{j}] {part}")

print("\n" + "=" * 100)
print("\n🔍 RECORD WITHOUT GENERAL DIRECTORATE:\n")

# Find the record without general_directorate
for idx, rec in enumerate(records):
    if not rec.get('general_directorate', '').strip():
        w18 = rec.get('W007_P_FLD18', '')
        print(f"Record {idx} (Case ID: {rec.get('case_id')}):")
        print(f"  W007_P_FLD18: {w18}")
        print(f"  department: {rec.get('department', '')}")
        print(f"  general_directorate: {rec.get('general_directorate', 'EMPTY')}")
        
        if '(' in w18:
            parts = w18.split('(', 1)
            in_paren = parts[1].rsplit(')', 1)[0] if ')' in parts[1] else parts[1]
            if '\\' in in_paren:
                path_parts = [p.strip() for p in in_paren.split('\\')]
                print(f"  Possible General Directorate from parentheses: {path_parts[0] if path_parts else 'N/A'}")
        break
