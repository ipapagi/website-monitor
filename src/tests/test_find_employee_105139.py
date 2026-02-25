"""
Test script: Δοκιμή αναζήτησης Διεκπεραιωμένης Υπόθεσης για 105139
Ο χρήστης ισχυρίζεται ότι υπάρχει εισηγητής ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ (W001_P_FLD10)
που έχει τη υπόθεση 105139 στο DESCRIPTION
"""
import os
import sys
import re
import html

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from charges import fetch_charges

def extract_all_pkms_from_description(description: str):
    """Εξάγει ΌΛΟΥΣ τους PKMs από το DESCRIPTION"""
    description = html.unescape(description)
    # Αναζήτηση όλων "Αίτημα XXXX/YYYY" patterns
    matches = re.findall(r'Αίτημα\s+\d+/(\d+)', description)
    return matches

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
    # STEP 1: Fetch all charges (Διεκπεραιωμένες Υποθέσεις)
    # ============================================================================
    print("📋 Step 1: Fetching all Διεκπεραιωμένες Υποθέσεις from queryId=19...")
    charges_records, _ = fetch_charges(monitor)
    print(f"✅ Found {len(charges_records)} records\n")
    
    # ============================================================================
    # STEP 2: Search for ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ in W001_P_FLD10
    # ============================================================================
    print("🔍 Step 2: Searching for 'ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ' in W001_P_FLD10...")
    target_employee = "ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ"
    
    matching_records = []
    for rec in charges_records:
        employee = rec.get('W001_P_FLD10', '')
        if employee and isinstance(employee, str):
            employee_clean = html.unescape(employee).strip()
            if target_employee.upper() in employee_clean.upper():
                matching_records.append(rec)
    
    print(f"✅ Found {len(matching_records)} records assigned to '{target_employee}'\n")
    
    if not matching_records:
        print("❌ No records found for this employee")
        return
    
    # ============================================================================
    # STEP 3: For each matching record, extract all PKMs from DESCRIPTION
    # ============================================================================
    print(f"🔍 Step 3: Extracting PKMs from DESCRIPTION fields...\n")
    
    found_105139 = False
    for i, rec in enumerate(matching_records, 1):
        description = rec.get('DESCRIPTION', '')
        pkms = extract_all_pkms_from_description(description)
        
        print(f"Record {i}:")
        print(f"  DOCID: {rec.get('DOCID', 'N/A')}")
        print(f"  Employee: {html.unescape(rec.get('W001_P_FLD10', '')).strip()}")
        print(f"  DESCRIPTION: {description[:100]}...")
        print(f"  PKMs found: {pkms}")
        
        if '105139' in pkms or '105139' in description:
            print(f"  ✅ FOUND 105139 IN THIS RECORD!")
            found_105139 = True
            
            # Print full details
            print(f"  \n  📄 FULL DETAILS:")
            print(f"     DOCID: {rec.get('DOCID')}")
            print(f"     W001_P_FLD1: {rec.get('W001_P_FLD1')}")
            print(f"     W001_P_FLD10: {html.unescape(rec.get('W001_P_FLD10', '')).strip()}")
            print(f"     DESCRIPTION: {html.unescape(description)}")
        print()
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Employee searched: {target_employee}")
    print(f"Records found: {len(matching_records)}")
    print(f"Case 105139 found: {'✅ YES' if found_105139 else '❌ NO'}")
    print("=" * 80)

if __name__ == '__main__':
    main()
