"""
Test script: Δοκιμή σύνδεσης χρέωσης για υπόθεση 105139
"""
import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from incoming import fetch_incoming_records, simplify_incoming_records, get_docid_for_case_id
from charges import fetch_charges, add_charge_info, get_employee_from_charge

def main():
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
    
    print("🔐 Login...")
    if not monitor.logged_in and not monitor.login():
        print("❌ Login failed")
        return
    
    print("✅ Logged in\n")
    
    # ============================================================================
    # STEP 1: Fetch charges
    # ============================================================================
    print("📋 Step 1: Fetching charges from queryId=2 (OTS)...")
    charges_records, charges_by_pkm = fetch_charges(monitor)
    print(f"✅ Found {len(charges_records)} charges")
    print(f"✅ Created charges_by_pkm with {len(charges_by_pkm)} PKM keys\n")
    
    # ============================================================================
    # STEP 2: Search for case 105139 in charges
    # ============================================================================
    print("🔍 Step 2: Searching for case 105139 in charges...")
    target_pkm = "105139"
    
    if target_pkm in charges_by_pkm:
        charge = charges_by_pkm[target_pkm]
        print(f"✅ Found charge for PKM {target_pkm}!")
        print(f"   - DOCID: {charge.get('DOCID', 'N/A')}")
        print(f"   - DESCRIPTION: {charge.get('DESCRIPTION', 'N/A')[:80]}...")
        print(f"   - W001_P_FLD1 (case_id): {charge.get('W001_P_FLD1', 'N/A')}")
        
        employee = get_employee_from_charge(charge)
        print(f"   - W001_P_FLD10 (Employee): {employee}\n")
    else:
        print(f"❌ PKM {target_pkm} NOT found in charges (case is unassigned)\n")
        print("Available PKMs in charges:")
        for pkm in sorted(charges_by_pkm.keys())[:10]:
            print(f"   - {pkm}")
        if len(charges_by_pkm) > 10:
            print(f"   ... and {len(charges_by_pkm) - 10} more\n")
    
    # ============================================================================
    # STEP 3: Fetch incoming records
    # ============================================================================
    print("📨 Step 3: Fetching incoming records from queryId=6...")
    params = config.get('incoming_api_params', INCOMING_DEFAULT_PARAMS).copy()
    data = fetch_incoming_records(monitor, params)
    
    if not data or not data.get('success'):
        print("❌ Failed to fetch incoming records")
        return
    
    incoming_raw = simplify_incoming_records(data.get('data', []))
    print(f"✅ Found {len(incoming_raw)} incoming records\n")
    
    # ============================================================================
    # STEP 4: Search for case 105139 in incoming
    # ============================================================================
    print(f"🔍 Step 4: Searching for case {target_pkm} in incoming records...")
    
    matching_incoming = None
    for rec in incoming_raw:
        if str(rec.get('case_id', '')) == target_pkm:
            matching_incoming = rec
            break
    
    if matching_incoming:
        print(f"✅ Found incoming record for case {target_pkm}!")
        print(f"   - case_id: {matching_incoming.get('case_id', 'N/A')}")
        print(f"   - doc_id: {matching_incoming.get('doc_id', 'N/A')}")
        print(f"   - protocol_number: {matching_incoming.get('protocol_number', 'N/A')}")
        print(f"   - directory: {matching_incoming.get('directory', 'N/A')}")
        print(f"   - procedure: {matching_incoming.get('procedure', 'N/A')}")
        print(f"   - party: {matching_incoming.get('party', 'N/A')}")
        print(f"   - submitted_at: {matching_incoming.get('submitted_at', 'N/A')}\n")
    else:
        print(f"❌ Case {target_pkm} NOT found in incoming records")
        print("Available cases in incoming:")
        for i, rec in enumerate(incoming_raw[:10]):
            print(f"   - {rec.get('case_id', 'N/A')}")
        if len(incoming_raw) > 10:
            print(f"   ... and {len(incoming_raw) - 10} more")
        return
    
    # ============================================================================
    # STEP 5: Add charge info to incoming record
    # ============================================================================
    print("⚙️  Step 5: Enriching incoming record with charge info...")
    enriched = add_charge_info([matching_incoming], charges_by_pkm)
    enriched_rec = enriched[0]
    
    charge_info = enriched_rec.get('_charge', {})
    print(f"✅ Enrichment complete!")
    print(f"   - charged: {charge_info.get('charged', False)}")
    print(f"   - employee: {charge_info.get('employee', 'N/A')}")
    print(f"   - doc_id: {charge_info.get('doc_id', 'N/A')}")
    print(f"   - case_id (from charge): {charge_info.get('case_id', 'N/A')}")
    description = charge_info.get('description', 'N/A')
    if description and description != 'N/A':
        print(f"   - description: {description[:80]}...\n")
    else:
        print(f"   - description: {description}\n")
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("=" * 80)
    print("📊 SUMMARY - Case 105139 Connection")
    print("=" * 80)
    print(f"Incoming case_id: {matching_incoming.get('case_id')}")
    print(f"Incoming doc_id:  {get_docid_for_case_id(incoming_raw, target_pkm)}")
    print(f"Incoming party:   {matching_incoming.get('party')}")
    print(f"Incoming dir:     {matching_incoming.get('directory')}")
    print(f"")
    print(f"Charge found:     {charge_info.get('charged')}")
    print(f"Assigned to:      {charge_info.get('employee', '(none)')}")
    print("=" * 80)

if __name__ == '__main__':
    main()
