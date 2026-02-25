"""Δοκιμή module χρεώσεων - Ανάκτηση και στατιστικά"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from charges import (
    fetch_charges, 
    add_charge_info, 
    filter_charged, 
    filter_uncharged,
    print_charge_statistics
)
from incoming import fetch_incoming_records, simplify_incoming_records


def main():
    """Test charges functionality"""
    print("\n" + "="*80)
    print("🧪 ΔΟΚΙΜΗ ΧΡΕΩΣΕΩΝ ΕΚΚΡΕΜΩΝ ΥΠΟΘΕΣΕΩΝ".center(80))
    print("="*80 + "\n")
    
    # Load config
    root = get_project_root()
    config_path = os.path.join(root, "config", "config.yaml")
    config = load_config(config_path)
    
    # Create monitor
    monitor = PKMMonitor(
        base_url=config.get("base_url", "https://shde.pkm.gov.gr"),
        urls=config.get("urls", {}),
        api_params=config.get("api_params", {}),
        login_params=config.get("login_params", {}),
        check_interval=config.get("check_interval", 300),
        username=config.get("username"),
        password=config.get("password"),
        session_cookies=config.get("session_cookies"),
    )
    
    # Login
    print("🔐 Σύνδεση στο σύστημα...")
    if not monitor.login():
        print("❌ Αποτυχία σύνδεσης")
        sys.exit(1)
    print("✅ Σύνδεση επιτυχής\n")
    
    if not monitor.main_page_loaded:
        monitor.load_main_page()
    
    # STEP 1: Fetch charges
    print("📋 ΒΗΜΑ 1: Ανάκτηση χρεώσεων από queryId=19")
    print("-" * 60)
    charges_records, charges_by_pkm = fetch_charges(monitor)
    print(f"✅ Συνολικές χρεώσεις: {len(charges_records)}")
    print(f"✅ Χρεώσεις με PKM: {len(charges_by_pkm)}")
    
    if charges_records:
        print(f"\n📄 Δείγμα χρέωσης:")
        sample = charges_records[0]
        print(f"   DOCID: {sample.get('DOCID')}")
        print(f"   PKM (W007_P_FLD21): {sample.get('W007_P_FLD21')}")
        print(f"   Υπάλληλος (W001_P_FLD10): {sample.get('W001_P_FLD10')}")
        print(f"   Case ID (W001_P_FLD1): {sample.get('W001_P_FLD1')}")
        print(f"   Description: {sample.get('DESCRIPTION', '')[:100]}...")
    
    # STEP 2: Fetch incoming requests
    print("\n\n📋 ΒΗΜΑ 2: Ανάκτηση εισερχόμενων αιτήσεων")
    print("-" * 60)
    incoming_params = INCOMING_DEFAULT_PARAMS.copy()
    incoming_data = fetch_incoming_records(monitor, incoming_params)
    
    if not incoming_data or not incoming_data.get("success"):
        print("❌ Αποτυχία ανάκτησης εισερχόμενων")
        sys.exit(1)
    
    records = simplify_incoming_records(incoming_data.get("data", []))
    print(f"✅ Ανακτήθηκαν {len(records)} αιτήσεις")
    
    # STEP 3: Add charge info to records
    print("\n\n📋 ΒΗΜΑ 3: Εμπλουτισμός αιτήσεων με χρεώσεις")
    print("-" * 60)
    enriched_records = add_charge_info(records, charges_by_pkm)
    print(f"✅ Εμπλουτίστηκαν {len(enriched_records)} αιτήσεις")
    
    # STEP 4: Statistics
    print("\n\n📋 ΒΗΜΑ 4: Στατιστικά")
    print_charge_statistics(enriched_records)
    
    # STEP 5: Show examples
    charged = filter_charged(enriched_records)
    uncharged = filter_uncharged(enriched_records)
    
    print("\n\n📋 ΒΗΜΑ 5: Παραδείγματα")
    print("-" * 60)
    
    if charged:
        print(f"\n✅ Χρεωμένες αιτήσεις ({len(charged)}):")
        for i, rec in enumerate(charged[:5], 1):
            charge = rec.get('_charge', {})
            print(f"\n   {i}. PKM: {rec.get('protocol_number')}")
            print(f"      Διαδικασία: {rec.get('procedure', 'N/A')}")
            print(f"      Υπάλληλος: {charge.get('employee', 'N/A')}")
    
    if uncharged:
        print(f"\n\n⏳ Μη χρεωμένες αιτήσεις ({len(uncharged)}):")
        for i, rec in enumerate(uncharged[:5], 1):
            print(f"\n   {i}. PKM: {rec.get('protocol_number')}")
            print(f"      Διαδικασία: {rec.get('procedure', 'N/A')}")
    
    print("\n" + "="*80)
    print("✅ Η δοκιμή ολοκληρώθηκε επιτυχώς!".center(80))
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
