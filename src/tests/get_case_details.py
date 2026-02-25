#!/usr/bin/env python3
"""Fetch complete case details for a given case ID (PKM number)"""

import sys
import os

# Setup path to find src modules
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
src_dir = os.path.join(project_root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import re
import argparse
import html
from monitor import PKMMonitor
from utils import load_config
from config import get_project_root

def extract_pkm(description: str) -> str:
    """Extract PKM from DESCRIPTION field"""
    if not description:
        return None
    match = re.search(r'Αίτημα\s+\d+/(\d+)', description)
    return match.group(1) if match else None


def fetch_case_details_by_protocol(monitor, protocol_num: str):
    """Fetch case details using protocol number (αριθμός πρωτοκόλλου)"""
    
    print("\n" + "="*80)
    print(f"PROTOCOL: {protocol_num}")
    print("="*80)
    
    # Search in queryId=2
    print("\n📥 Searching in queryId=2 (OTS)...")
    params = {
        'queryId': '2',
        'queryOwner': '2',
        'isCase': 'false',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '100',
        'isPoll': 'true'
    }
    
    data = monitor.fetch_data(params)
    if data and data.get('success'):
        for rec in data.get('data', []):
            desc = str(rec.get('DESCRIPTION', ''))
            if protocol_num in desc:
                print(f"   ✅ FOUND (DOCID: {rec.get('DOCID')})")
                
                # Decode HTML entities
                desc_decoded = html.unescape(desc)
                
                print("\n📋 Record Details:")
                print(f"   DOCID: {rec.get('DOCID')}")
                print(f"   DESCRIPTION: {desc_decoded[:100]}")
                print(f"   USER_GROUP_ID_TO (Assigned To): {rec.get('USER_GROUP_ID_TO') or 'EMPTY'}")
                print(f"   USER_ID_FROM (From): {rec.get('USER_ID_FROM') or 'EMPTY'}")
                print(f"   W001_P_FLD10 (Employee): {rec.get('W001_P_FLD10') or 'EMPTY'}")
                print(f"   ACTIONS: {rec.get('ACTIONS')}")
                print(f"   DATE_START_ISO: {rec.get('DATE_START_ISO')}")
                return rec
    
    print(f"   ❌ Not found in queryId=2")
    return None


def fetch_case_details(monitor, case_id: str):
    """Fetch case details from all available sources"""
    
    print("\n" + "="*80)
    print(f"CASE DETAILS FOR: {case_id}")
    print("="*80)
    
    results = {
        'queryId2': None,  # OTS - Εισερχόμενα από Πρωτόκολλο
        'queryId3': None,  # Routing - προώθηση
        'queryId6': None,  # Portal incoming - εισερχόμενα αιτήματα
        'queryId19': None  # Completed - διεκπεραιωμένες
    }
    
    # ===== QueryId=2: OTS (Εισερχόμενα από Πρωτόκολλο) =====
    print("\n📥 Searching in queryId=2 (OTS - Εισερχόμενα από Πρωτόκολλο)...")
    params = {
        'queryId': '2',
        'queryOwner': '2',
        'isCase': 'false',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '100',
        'isPoll': 'true'
    }
    
    data = monitor.fetch_data(params)
    if data and data.get('success'):
        for rec in data.get('data', []):
            pkm = extract_pkm(rec.get('DESCRIPTION', ''))
            if pkm == case_id:
                results['queryId2'] = rec
                print(f"   ✅ FOUND in queryId=2 (DOCID: {rec.get('DOCID')})")
                break
        if not results['queryId2']:
            print(f"   ❌ Not found in queryId=2")
    
    # ===== QueryId=3: Routing (Προώθηση) =====
    print("\n📥 Searching in queryId=3 (Routing - Προώθηση)...")
    params['queryId'] = '3'
    params['queryOwner'] = '3'
    
    data = monitor.fetch_data(params)
    if data and data.get('success'):
        for rec in data.get('data', []):
            pkm = extract_pkm(rec.get('DESCRIPTION', ''))
            if pkm == case_id:
                results['queryId3'] = rec
                print(f"   ✅ FOUND in queryId=3 (DOCID: {rec.get('DOCID')})")
                break
        if not results['queryId3']:
            print(f"   ❌ Not found in queryId=3")
    
    # ===== QueryId=6: Portal Incoming (Εισερχόμενα αιτήματα) =====
    print("\n📥 Searching in queryId=6 (Portal - Εισερχόμενα αιτήματα)...")
    params['queryId'] = '6'
    params['queryOwner'] = '6'
    
    data = monitor.fetch_data(params)
    if data and data.get('success'):
        for rec in data.get('data', []):
            # In queryId=6, case_id is W007_P_FLD21
            w007 = str(rec.get('W007_P_FLD21', '')).strip()
            if w007 == case_id:
                results['queryId6'] = rec
                print(f"   ✅ FOUND in queryId=6 (DOCID: {rec.get('DOCID')})")
                break
        if not results['queryId6']:
            print(f"   ❌ Not found in queryId=6")
    
    # ===== QueryId=19: Completed (Διεκπεραιωμένες) =====
    print("\n📥 Searching in queryId=19 (Completed - Διεκπεραιωμένες)...")
    params['queryId'] = '19'
    params['queryOwner'] = '19'
    
    data = monitor.fetch_data(params)
    if data and data.get('success'):
        for rec in data.get('data', []):
            pkm = extract_pkm(rec.get('DESCRIPTION', ''))
            if pkm == case_id:
                results['queryId19'] = rec
                print(f"   ✅ FOUND in queryId=19 (DOCID: {rec.get('DOCID')})")
                break
        if not results['queryId19']:
            print(f"   ❌ Not found in queryId=19")
    
    # ===== Display Results =====
    print("\n" + "="*80)
    print("CASE STATUS SUMMARY:")
    print("="*80)
    
    status_found = 0
    if results['queryId2']:
        print(f"\n✅ In queryId=2 (OTS):")
        status_found += 1
    if results['queryId3']:
        print(f"\n✅ In queryId=3 (Routing):")
        status_found += 1
    if results['queryId6']:
        print(f"\n✅ In queryId=6 (Portal Incoming):")
        status_found += 1
    if results['queryId19']:
        print(f"\n✅ In queryId=19 (Completed - ΔΙΕΚΠΕΡΑΙΩΜΕΝΗ):")
        status_found += 1
    
    if status_found == 0:
        print(f"\n❌ Case {case_id} NOT FOUND in any source")
        return results
    
    print(f"\n📊 Summary: Found in {status_found} source(s)")
    
    # ===== Detailed View by Source =====
    print("\n" + "="*80)
    print("DETAILED INFORMATION:")
    print("="*80)
    
    if results['queryId2']:
        print("\n📋 QueryId=2 (OTS - Εισερχόμενα από Πρωτόκολλο):")
        rec = results['queryId2']
        desc_decoded = html.unescape(str(rec.get('DESCRIPTION', '')))
        print(f"   DOCID: {rec.get('DOCID')}")
        print(f"   DESCRIPTION: {desc_decoded[:100]}")
        print(f"   USER_GROUP_ID_TO (Assigned To): {rec.get('USER_GROUP_ID_TO') or 'EMPTY'}")
        print(f"   USER_ID_FROM (From): {rec.get('USER_ID_FROM') or 'EMPTY'}")
        print(f"   W001_P_FLD10 (Employee): {rec.get('W001_P_FLD10') or 'EMPTY'}")
        print(f"   DATE_INSERTED: {rec.get('DATE_INSERTED_ISO')}")
    
    if results['queryId3']:
        print("\n📋 QueryId=3 (Routing - Προώθηση):")
        rec = results['queryId3']
        desc_decoded = html.unescape(str(rec.get('DESCRIPTION', '')))
        print(f"   DOCID: {rec.get('DOCID')}")
        print(f"   USER_GROUP_ID_TO (Assigned To): {rec.get('USER_GROUP_ID_TO')}")
        print(f"   USER_ID_FROM (From): {rec.get('USER_ID_FROM')}")
        print(f"   P_PROC_STEPS_STEPID: {rec.get('P_PROC_STEPS_STEPID')}")
        print(f"   DATE_START: {rec.get('DATE_START_ISO')}")
    
    if results['queryId6']:
        print("\n📋 QueryId=6 (Portal - Εισερχόμενα αιτήματα):")
        rec = results['queryId6']
        print(f"   DOCID: {rec.get('DOCID')}")
        print(f"   W007_P_FLD21 (Case ID): {rec.get('W007_P_FLD21')}")
        print(f"   Party: {rec.get('W007_P_FLD26', 'N/A')}")
        print(f"   Directory: {rec.get('W007_P_FLD24', 'N/A')}")
        print(f"   Procedure: {rec.get('W007_P_FLD25', 'N/A')}")
        print(f"   Submitted: {rec.get('W007_P_FLD22')}")
    
    if results['queryId19']:
        print("\n📋 QueryId=19 (Completed - Διεκπεραιωμένες):")
        rec = results['queryId19']
        desc_decoded = html.unescape(str(rec.get('DESCRIPTION', '')))
        print(f"   DOCID: {rec.get('DOCID')}")
        print(f"   W001_P_FLD10: {rec.get('W001_P_FLD10')}")
        print(f"   W001_P_FLD9: {rec.get('W001_P_FLD9')} ✅ COMPLETED")
        print(f"   W001_P_FLD17: {rec.get('W001_P_FLD17')}")
        print(f"   W001_P_FLD3 (Date): {rec.get('W001_P_FLD3')}")
    
    # ===== Interpretation =====
    print("\n" + "="*80)
    print("CASE STATUS INTERPRETATION:")
    print("="*80)
    
    if results['queryId19']:
        print(f"\n✅ This case is COMPLETED (Διεκπεραιωμένη)")
    elif results['queryId2']:
        if results['queryId3']:
            print(f"\n🔄 This case is ROUTED/FORWARDED")
        else:
            print(f"\n📩 This case is INCOMING (in OTS)")
    elif results['queryId6']:
        print(f"\n📨 This case is PORTAL INCOMING")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch complete case details for a given case ID (PKM) or protocol number")
    parser.add_argument('case_id', help='Case ID / PKM number (e.g., 105139) or protocol number (e.g., 793923)')
    parser.add_argument('--protocol', '-p', action='store_true', help='Search by protocol number instead of case ID')
    
    args = parser.parse_args()
    case_id = args.case_id
    
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
        print("❌ Login failed")
        return 1
    
    if args.protocol:
        fetch_case_details_by_protocol(monitor, case_id)
    else:
        results = fetch_case_details(monitor, case_id)
    
    print("\n" + "="*80)

if __name__ == '__main__':
    sys.exit(main() or 0)
