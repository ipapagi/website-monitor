"""
Δοκιμή ενσωμάτωσης διεκπεραιωμένων υποθέσεων με τα διορθωμένα field mappings
"""
import os
import sys
from datetime import datetime, timedelta

# Προσθήκη src στο path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from monitor import PKMMonitor
from settled_cases import fetch_settled_cases, simplify_settled_records
from config import get_project_root
from utils import load_config

load_dotenv()

def test_settled_cases():
    """Δοκιμάζει την ανάκτηση και απλοποίηση διεκπεραιωμένων υποθέσεων"""
    print("=" * 80)
    print("🧪 ΔΟΚΙΜΗ ΔΙΕΚΠΕΡΑΙΩΜΕΝΩΝ ΥΠΟΘΕΣΕΩΝ")
    print("=" * 80)
    
    # Φόρτωση config και δημιουργία monitor instance
    config = load_config(os.path.join(get_project_root(), 'config', 'config.yaml'))
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
    
    # Login
    print("\n0️⃣ Σύνδεση...")
    if not monitor.login():
        print("❌ Αποτυχία login")
        return
    print("✅ Επιτυχής σύνδεση")
    
    print("\n1️⃣ Ανάκτηση διεκπεραιωμένων υποθέσεων...")
    result = fetch_settled_cases(monitor)
    
    if not result['success']:
        print("❌ Αποτυχία ανάκτησης")
        return
    
    print(f"✅ Ανακτήθηκαν {result['total']} εγγραφές")
    
    # Απλοποίηση
    print("\n2️⃣ Απλοποίηση εγγραφών...")
    simplified = simplify_settled_records(result['data'])
    print(f"✅ Απλοποιήθηκαν {len(simplified)} εγγραφές")
    
    # Προβολή δείγματος
    if simplified:
        print("\n3️⃣ Δείγμα πρώτης εγγραφής:")
        print("-" * 80)
        first = simplified[0]
        for key, value in first.items():
            print(f"  {key:20}: {value}")
        
        # Στατιστικά
        print("\n4️⃣ Στατιστικά:")
        print("-" * 80)
        completed_count = sum(1 for rec in simplified if rec.get('completion_date'))
        print(f"  Υποθέσεις με ημ/νία διεκπεραίωσης: {completed_count}")
        
        portals = set(rec.get('portal', '') for rec in simplified if rec.get('portal'))
        print(f"  Portals: {', '.join(portals) if portals else 'N/A'}")
        
        statuses = set(rec.get('status', '') for rec in simplified if rec.get('status'))
        print(f"  Καταστάσεις: {', '.join(statuses) if statuses else 'N/A'}")
        
    print("\n" + "=" * 80)
    print("✅ ΔΟΚΙΜΗ ΟΛΟΚΛΗΡΩΘΗΚΕ")
    print("=" * 80)

if __name__ == '__main__':
    test_settled_cases()
