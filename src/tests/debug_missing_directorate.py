#!/usr/bin/env python
"""
Ερευνά γιατί κάποιες εγγραφές βγαίνουν ως ΧΩΡΙΣ_ΓΕΝΙΚΗ_ΔΙΕΥΘΥΝΣΗ
"""
import sys
sys.path.insert(0, './src')

from config import get_project_root, INCOMING_DEFAULT_PARAMS
from utils import load_config
from monitor import PKMMonitor
from incoming import fetch_incoming_records, simplify_incoming_records
from api import enrich_record_details

# Load config
from pathlib import Path
root = Path(get_project_root())
config = load_config(str(root / 'config' / 'config.yaml'))

# Connect and fetch
print("🔐 Σύνδεση και ανάκτηση δεδομένων...\n")
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

# Fetch incoming
incoming_params = config.get('incoming_api_params', INCOMING_DEFAULT_PARAMS).copy()
data = fetch_incoming_records(monitor, incoming_params)
records = simplify_incoming_records(data.get('data', []))

# Enrich
print(f"🔄 Enriching {len(records)} records...\n")
enrich_record_details(monitor, records)

# Find records without general_directorate
missing_gd = []
for idx, rec in enumerate(records):
    gd = rec.get('general_directorate', '').strip()
    if not gd:
        missing_gd.append((idx, rec))
        if len(missing_gd) <= 3:
            print(f"❌ Record {idx} - ΧΩΡΙΣ ΓΕΝΙΚΗ ΔΙΕΥΘΥΝΣΗ:")
            print(f"   Case ID: {rec.get('case_id')}")
            print(f"   W007_P_FLD16 (raw list): {rec.get('W007_P_FLD16', 'EMPTY')}")
            print(f"   general_directorate (enriched): {rec.get('general_directorate', 'EMPTY')}")
            print(f"   W007_P_FLD18 (Τμήμα - πλήρες): {rec.get('W007_P_FLD18', 'EMPTY')[:100]}")
            print(f"   department (processed): {rec.get('department', 'EMPTY')[:80]}")
            print(f"   Subject: {rec.get('subject', '')[:60]}")
            print()

print(f"\n📊 SUMMARY:")
print(f"   Total records: {len(records)}")
print(f"   Missing general_directorate: {len(missing_gd)}")
print(f"   Percentage: {len(missing_gd)*100/len(records):.1f}%")

if missing_gd:
    print(f"\n⚠️  These records will be grouped as ΧΩΡΙΣ_ΓΕΝΙΚΗ_ΔΙΕΥΘΥΝΣΗ")
    print(f"   This usually means W007_P_FLD16 is empty in both list AND detail API")
