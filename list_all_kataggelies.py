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

print("📋 ΛΙΣΤΑ ΚΑΤΑΓΓΕΛΙΩΝ ΠΟΥ ΕΞΑΙΡΟΥΝΤΑΙ ΑΠΟ ΤΙΣ ΑΝΑΦΟΡΕΣ:\n")
print("=" * 120)

# Find all records with "Καταγγελία"
kataggelies = []
for idx, rec in enumerate(records):
    doc_cat = rec.get('document_category', '').strip()
    
    if 'Καταγγελία' in doc_cat or doc_cat.lower() == 'καταγγελία':
        kataggelies.append((idx, rec))

# Display all
for i, (idx, rec) in enumerate(kataggelies, 1):
    print(f"\n{i}. ΚΑΤΑΓΓΕΛΙΑ #{idx}")
    print(f"   {'─' * 110}")
    print(f"   Αρ. Υπόθεσης:        {rec.get('case_id', 'N/A')}")
    print(f"   Doc ID:              {rec.get('doc_id', 'N/A')}")
    print(f"   Κατηγορία:           {rec.get('document_category', 'N/A')}")
    print(f"   Ημ/νία Υποβολής:     {rec.get('submitted_at', 'N/A')}")
    print(f"   Συναλλασσόμενος:     {rec.get('party', 'N/A')}")
    print(f"   Θέμα:                {rec.get('subject', 'N/A')[:100]}")
    print(f"   Γενική Δ/νση:        {rec.get('general_directorate', 'N/A')}")
    print(f"   Διεύθυνση:           {rec.get('directory', 'N/A')[:80]}")
    print(f"   Τμήμα:               {rec.get('department', 'N/A')[:80]}")

print(f"\n{'=' * 120}")
print(f"\n📊 ΣΥΝΟΛΟ: {len(kataggelies)} καταγγελίες")
print(f"   Ποσοστό επί του συνόλου: {len(kataggelies)*100/len(records):.1f}%")
print(f"\n✅ Αυτές οι καταγγελίες ΔΕΝ συμπεριλαμβάνονται στις εβδομαδιαίες αναφορές")
