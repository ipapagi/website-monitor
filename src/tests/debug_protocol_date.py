#!/usr/bin/env python3
"""Debug script για να δούμε τι fields έχει το detail API response"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import get_project_root, INCOMING_DEFAULT_PARAMS
from utils import load_config
from monitor import PKMMonitor
from incoming import fetch_incoming_records, simplify_incoming_records
from api import fetch_record_details

project_root = get_project_root()
config = load_config(os.path.join(project_root, 'config', 'config.yaml'))

monitor = PKMMonitor(
    base_url=config.get('base_url', 'https://shde.pkm.gov.gr'),
    urls=config.get('urls', {}),
    api_params=config.get('api_params', {}),
    login_params=config.get('login_params', {}),
    username=config.get('username'),
    password=config.get('password'),
    session_cookies=config.get('session_cookies'))

if not monitor.logged_in and not monitor.login():
    print("Login failed")
    exit(1)

# Fetch incoming
incoming_params = config.get('incoming_api_params', INCOMING_DEFAULT_PARAMS).copy()
data = fetch_incoming_records(monitor, incoming_params)

if not data:
    print("No incoming data")
    exit(1)

raw_records = data.get('data', [])

# Πάρε το πρώτο record που έχει doc_id
for rec in raw_records[:10]:
    doc_id = rec.get('DOCID') or rec.get('docid')
    if doc_id:
        print(f"Ανάκτηση detail API για DOCID={doc_id}\n")
        
        # Κάλεσε το detail API
        session = getattr(monitor, 'session', None)
        base_url = getattr(monitor, 'base_url', '')
        jwt_token = getattr(monitor, 'jwt_token', None)
        main_page_url = getattr(monitor, 'main_page_url', '')
        
        url = base_url.rstrip('/') + f"/services/DataServices/fetchDataTableRecord/7/{doc_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': '*/*',
            'Accept-Language': 'el',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': main_page_url or base_url,
        }
        if jwt_token:
            headers['Authorization'] = f'Bearer {jwt_token}'
        
        try:
            response = session.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            payload = response.json()
            
            if payload.get('success'):
                print("=" * 80)
                print(f"ΟΛΑ ΤΑ FIELDS ΤΟΥ DETAIL API (πρώτα 30 fields)")
                print("=" * 80)
                
                # Πάρε τα fields από το payload
                record_data = payload.get('record') or payload.get('data') or {}
                if isinstance(record_data, list):
                    record_data = record_data[0] if record_data else {}
                
                for i, (key, value) in enumerate(sorted(record_data.items())):
                    if i >= 30:
                        break
                    
                    if isinstance(value, str) and len(str(value)) > 60:
                        display_value = str(value)[:60] + "..."
                    else:
                        display_value = value
                    
                    print(f"{key}: {display_value}")
                
                print("\n" + "=" * 80)
                print("Ειδικά fields που ίσως έχουν ημερομηνία:")
                print("=" * 80)
                
                for key in sorted(record_data.keys()):
                    if 'date' in key.lower() or 'fld6' in key.lower() or 'fld3' in key.lower():
                        value = record_data[key]
                        print(f"{key}: {value}")
                
                break
        except Exception as exc:
            print(f"Error: {exc}")
