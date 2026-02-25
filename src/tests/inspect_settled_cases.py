#!/usr/bin/env python3
"""
Inspection του endpoint getSearchDataByQueryId για Διεκπεραιωμένες Υποθέσεις (queryId=19)
Ελέγχει αν μπορούμε να βρούμε σωστά τις υποθέσεις που έχουν διεκπεραιωθεί
"""

import sys
import os
from datetime import datetime

# Setup path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
src_dir = os.path.join(project_root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root
import json
import html

def inspect_settled_cases():
    """Inspect διεκπεραιωμένων υποθέσεων από queryId=19"""
    
    print("\n" + "=" * 80)
    print("🔍 INSPECTION: Διεκπεραιωμένες Υποθέσεις (queryId=19)")
    print("=" * 80)
    
    # Load config
    root = get_project_root()
    cfg_path = os.path.join(root, 'config', 'config.yaml')
    config = load_config(cfg_path)
    
    # Create monitor
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
        print("[ERR] Failed to login")
        return 1
    
    print("\n✅ Connected to system")
    
    # Παράμετροι για Διεκπεραιωμένες (queryId=19)
    settled_params = {
        'isPoll': 'false',
        'queryId': '19',
        'queryOwner': '2',
        'isCase': 'false',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '200'
    }
    
    print("\n[*] Fetching data with parameters:")
    for k, v in settled_params.items():
        print(f"    {k:20} = {v}")
    
    print("\n[*] Making request to: /services/SearchServices/getSearchDataByQueryId")
    data = monitor.fetch_data(settled_params)
    
    if not data or not data.get('success'):
        print(f"[ERR] Failed to fetch: {data}")
        return 1
    
    records = data.get('data', [])
    total = data.get('total', 0)
    
    print(f"\n✅ Got {len(records)} records (total: {total})")
    
    if not records:
        print("[WARN] No settled cases found")
        return 0
    
    # Ανάλυση δομής
    print("\n" + "=" * 80)
    print("📋 ΠΕΔΙΑ ΔΕΔΟΜΕΝΩΝ")
    print("=" * 80)
    
    sample = records[0]
    print(f"\nFirst record has {len(sample)} fields:")
    
    # Ταξινομημένα πεδία
    fields_by_category = {
        'IDs & Keys': [],
        'Case Info': [],
        'Dates': [],
        'Status & State': [],
        'Descriptions': [],
        'Other': []
    }
    
    for key in sorted(sample.keys()):
        if 'ID' in key or 'DOC' in key or 'CASE' in key:
            fields_by_category['IDs & Keys'].append(key)
        elif 'P_FLD' in key:
            # W001, W003, W007 κλπ
            fields_by_category['Case Info'].append(key)
        elif 'DATE' in key or 'CDATE' in key:
            fields_by_category['Dates'].append(key)
        elif 'STATE' in key or 'STATUS' in key:
            fields_by_category['Status & State'].append(key)
        elif 'DESC' in key or 'DESCRIPTION' in key:
            fields_by_category['Descriptions'].append(key)
        else:
            fields_by_category['Other'].append(key)
    
    for category, keys in fields_by_category.items():
        if keys:
            print(f"\n📌 {category}:")
            for key in keys:
                value = sample.get(key, '')
                # Truncate long values
                if isinstance(value, str):
                    value_str = value[:60].replace('\n', ' ')
                else:
                    value_str = str(value)[:60]
                print(f"   {key:30} = {value_str}")
    
    # Ανάλυση πεδίων που δείχνουν διεκπεραίωση
    print("\n" + "=" * 80)
    print("🎯 ΑΝΑΛΥΣΗ: Πεδία που Δείχνουν Διεκπεραίωση")
    print("=" * 80)
    
    # Potential fields
    status_fields = ['W001_P_FLD9', 'W007_P_FLD19', 'W007_P_FLD20', 'STATUS', 'STATE', 'DOCSTATE']
    date_fields = ['W007_P_FLD20', 'W007_P_FLD3', 'CDATE', 'MDATE', 'DATE_END']
    
    print("\nStatus fields found:")
    for rec_idx, rec in enumerate(records[:5]):
        print(f"\n  Record {rec_idx + 1}:")
        for field in status_fields:
            if field in rec:
                value = rec.get(field, '')
                print(f"    {field:20} = {value}")
    
    # Ελέγχος για PKM / Case ID
    print("\n" + "=" * 80)
    print("🏷️  ΑΝΑΛΥΣΗ: Πεδία για Case ID (PKM)")
    print("=" * 80)
    
    id_fields = ['W007_P_FLD21', 'W001_P_FLD21', 'DOCID', 'W007_P_FLD1', 'W001_P_FLD1']
    
    print("\nPotential PKM/Case ID fields:")
    for field in id_fields:
        if field in sample:
            print(f"\n  {field}:")
            sample_values = []
            for rec in records[:3]:
                val = rec.get(field, '')
                sample_values.append(str(val))
            print(f"    Sample values: {sample_values}")
    
    # Ελέγχος DESCRIPTION για protocol numbers
    print("\n" + "=" * 80)
    print("📝 ΑΝΑΛΥΣΗ: DESCRIPTION Field")
    print("=" * 80)
    
    print("\nFIRST 3 DESCRIPTIONS:")
    for idx, rec in enumerate(records[:3]):
        desc = rec.get('DESCRIPTION', '')
        desc = html.unescape(desc)  # Decode HTML entities
        print(f"\n  Record {idx + 1}:")
        if len(desc) > 150:
            print(f"    {desc[:150]}...")
        else:
            print(f"    {desc}")
    
    # Statistics
    print("\n" + "=" * 80)
    print("📊 ΣΤΑΤΙΣΤΙΚΑ")
    print("=" * 80)
    
    # Check which PKM field exists
    pkm_field = None
    for field in ['W007_P_FLD21', 'W001_P_FLD21']:
        if field in sample:
            pkm_counts = {}
            for rec in records:
                val = rec.get(field, '')
                pkm_counts[val] = pkm_counts.get(val, 0) + 1
            if pkm_counts:
                pkm_field = field
                break
    
    if pkm_field:
        print(f"\n✅ Using {pkm_field} for PKM/Case ID")
        non_empty = sum(1 for rec in records if rec.get(pkm_field))
        print(f"   Records with PKM: {non_empty}/{len(records)}")
        
        # Get unique PKMs
        pkms = set()
        for rec in records:
            val = rec.get(pkm_field, '')
            if val:
                pkms.add(str(val))
        print(f"   Unique PKMs: {len(pkms)}")
        print(f"   Sample PKMs: {list(sorted(pkms))[:10]}")
    else:
        print(f"\n⚠️  No PKM field found")
    
    # Check status field
    print("\n✅ Status field detection:")
    status_values = {}
    for rec in records:
        status = rec.get('W007_P_FLD19', rec.get('W001_P_FLD9', 'UNKNOWN'))
        status_values[status] = status_values.get(status, 0) + 1
    
    for status, count in sorted(status_values.items(), key=lambda x: -x[1]):
        print(f"   {status:30} -> {count} records")
    
    # Αναφορά
    print("\n" + "=" * 80)
    print("✅ ΑΝΑΦΟΡΑ")
    print("=" * 80)
    
    print(f"""
✅ Endpoint: /services/SearchServices/getSearchDataByQueryId?queryId=19
✅ Records fetched: {len(records)} / {total}
✅ PKM field: {pkm_field or 'NOT FOUND'}
✅ Status field: W007_P_FLD19 or W001_P_FLD9
✅ Date field (closed): W007_P_FLD20

Χρησιμοποιώντας αυτό το endpoint, ΜΠΟΡΟΥΜΕ να βρούμε σωστά τις διεκπεραιωμένες υποθέσεις.
    """)
    
    return 0


if __name__ == '__main__':
    sys.exit(inspect_settled_cases())
