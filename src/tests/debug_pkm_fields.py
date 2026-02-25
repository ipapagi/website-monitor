"""Debug script - ελέγχει τα πεδία PKM"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from incoming import fetch_incoming_records, simplify_incoming_records

root = get_project_root()
config_path = os.path.join(root, "config", "config.yaml")
config = load_config(config_path)

monitor = PKMMonitor(
    base_url=config.get("base_url"),
    urls=config.get("urls", {}),
    api_params=config.get("api_params", {}),
    login_params=config.get("login_params", {}),
    check_interval=300,
    username=config.get("username"),
    password=config.get("password"),
    session_cookies=config.get("session_cookies"),
)

monitor.login()
monitor.load_main_page()

# Fetch incoming
incoming_params = INCOMING_DEFAULT_PARAMS.copy()
incoming_data = fetch_incoming_records(monitor, incoming_params)
records = simplify_incoming_records(incoming_data.get("data", []))

print("=== INCOMING RECORD SAMPLE ===")
if records:
    rec = records[0]
    print(f"Keys: {list(rec.keys())}")
    print(f"\nprotocol_number: '{rec.get('protocol_number')}'")
    print(f"case_id: '{rec.get('case_id')}'")
    print(f"doc_id: '{rec.get('doc_id')}'")
    print(f"W007_P_FLD21 (if exists): '{rec.get('W007_P_FLD21')}'")
    
    # Check raw data
    raw = incoming_data.get("data", [])[0] if incoming_data.get("data") else {}
    print(f"\n=== RAW API FIELDS ===")
    for key, val in raw.items():
        if 'FLD21' in key or 'protocol' in key.lower() or 'pkm' in key.lower():
            print(f"{key}: {val}")
