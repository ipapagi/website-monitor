"""
Test script: Αναζήτηση 105139 στις χρεώσεις "Εισερχόμενα Από Πρωτόκολλο (OTS)"
Χρησιμοποιώντας queryId=19 με πιθανές διαφορές στις παραμέτρους
"""
import os
import sys
import re
import html

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root

def extract_pkm_from_description(description: str):
    """Εξάγει το PKM από το DESCRIPTION"""
    description = html.unescape(description)
    match = re.search(r'Αίτημα\s+\d+/(\d+)', description)
    return match.group(1) if match else None

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
    # Try different parameter combinations for queryId 19
    # ============================================================================
    test_params = [
        # Original
        {
            'queryId': '19',
            'queryOwner': '2',
            'isCase': 'false',
            'stateId': 'welcomeGrid-45_dashboard0',
            'page': '1',
            'start': '0',
            'limit': '100',
            'isPoll': 'true',
            'name': 'Original (Διεκπεραιωμένες)'
        },
        # Try different queryOwner
        {
            'queryId': '19',
            'queryOwner': '3',
            'isCase': 'false',
            'stateId': 'welcomeGrid-45_dashboard0',
            'page': '1',
            'start': '0',
            'limit': '100',
            'isPoll': 'true',
            'name': 'queryOwner=3'
        },
        # Try without stateId specifier
        {
            'queryId': '19',
            'queryOwner': '2',
            'isCase': 'false',
            'page': '1',
            'start': '0',
            'limit': '100',
            'isPoll': 'true',
            'name': 'Without stateId'
        },
        # Try with isCase=true
        {
            'queryId': '19',
            'queryOwner': '2',
            'isCase': 'true',
            'page': '1',
            'start': '0',
            'limit': '100',
            'isPoll': 'true',
            'name': 'isCase=true'
        },
    ]
    
    all_results = {}
    
    for test_param in test_params:
        name = test_param.pop('name')
        print(f"🔍 Testing: {name}")
        print(f"   Parameters: {test_param}\n")
        
        try:
            data = monitor.fetch_data(test_param)
            
            if not data or not data.get('success'):
                print(f"   ❌ API returned error or no success\n")
                continue
            
            records = data.get('data', [])
            print(f"   ✅ Got {len(records)} records\n")
            
            all_results[name] = records
            
            # Search for 105139
            found_105139 = False
            for rec in records:
                description = rec.get('DESCRIPTION', '')
                if '105139' in description or '105139' in html.unescape(description):
                    found_105139 = True
                    print(f"   🎯 FOUND 105139!")
                    print(f"      DOCID: {rec.get('DOCID')}")
                    employee = html.unescape(rec.get('W001_P_FLD10', '')).strip()
                    print(f"      Employee (W001_P_FLD10): {employee}")
                    description_decoded = html.unescape(description)
                    print(f"      DESCRIPTION: {description_decoded[:200]}...")
                    break
            
            if not found_105139:
                print(f"   ❌ 105139 not found in these records\n")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}\n")
    
    # ============================================================================
    # Summary
    # ============================================================================
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    for name, records in all_results.items():
        print(f"{name}: {len(records)} records")

if __name__ == '__main__':
    main()
