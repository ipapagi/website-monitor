#!/usr/bin/env python
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

print("📋 CHECKING FOR ΚΑΤΑΓΓΕΛΙΑ RECORDS:\n")
print("=" * 100)

# Find records with "Καταγγελία" in document_category
kataggelies = []
for idx, rec in enumerate(records):
    doc_cat = rec.get('document_category', '').strip()
    w30 = rec.get('W007_P_FLD30', '').strip()
    w25 = rec.get('W007_P_FLD25', '').strip()
    
    if 'Καταγγελία' in doc_cat or 'Καταγγελία' in w30 or 'Καταγγελία' in w25:
        kataggelies.append((idx, rec))
        if len(kataggelies) <= 5:
            print(f"\n❌ Record {idx} - ΚΑΤΑΓΓΕΛΙΑ:")
            print(f"   Case ID: {rec.get('case_id')}")
            print(f"   document_category: {doc_cat}")
            print(f"   W007_P_FLD30: {w30}")
            print(f"   W007_P_FLD25: {w25}")
            print(f"   Subject: {rec.get('subject', '')[:60]}")

print(f"\n{'=' * 100}")
print(f"\n📊 SUMMARY:")
print(f"   Total records: {len(records)}")
print(f"   Καταγγελία records: {len(kataggelies)}")
print(f"   Percentage: {len(kataggelies)*100/len(records):.1f}%")

if kataggelies:
    print(f"\n⚠️  These records should be EXCLUDED from reports")
    print(f"   Filter: document_category != 'Καταγγελία'")
