"""Σύγκριση πεδίων (columns) μεταξύ των δύο endpoints"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Προσθήκη src στο path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from session import PKMSession
from config import INCOMING_DEFAULT_PARAMS, SETTLED_CASES_DEFAULT_PARAMS

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

# Φόρτωση credentials από .env
load_dotenv()
USERNAME = os.getenv('PKM_USERNAME', '')
PASSWORD = os.getenv('PKM_PASSWORD', '')

def get_columns_comparison():
    """Ανακτά και συγκρίνει τα columns από τα δύο endpoints"""
    
    print("\n" + "="*80)
    print("🔍 ΣΥΓΚΡΙΣΗ ΠΕΔΙΩΝ: Εισερχόμενες vs Διεκπεραιωμένες")
    print("="*80)
    
    # Αρχικοποίηση session
    session = PKMSession(
        base_url="https://shde.pkm.gov.gr",
        urls={
            'home': 'https://shde.pkm.gov.gr',
            'login': 'https://shde.pkm.gov.gr/services/LoginServices/loginWeb',
            'api': 'https://shde.pkm.gov.gr/services/SearchServices/getSearchDataByQueryId'
        },
        login_params={
            'application': '2',
            'otp': ''
        },
        username=USERNAME,
        password=PASSWORD
    )
    
    # ============ ΕΙΣΕΡΧΟΜΕΝΕΣ ΑΙΤΗΣΕΙΣ ============
    print("\n📥 ΕΙΣΕΡΧΟΜΕΝΕΣ ΑΙΤΗΣΕΙΣ (queryId=6)")
    print("-" * 80)
    
    params_incoming = INCOMING_DEFAULT_PARAMS.copy()
    params_incoming['limit'] = 5  # Μόνο 5 records για γρήγορη δοκιμή
    
    try:
        data_incoming = session.fetch_data(params_incoming)
        
        if data_incoming and data_incoming.get('success'):
            columns_incoming = data_incoming.get('columns', [])
            total_incoming = data_incoming.get('total', 0)
            
            print(f"✅ Success: Σύνολο εγγραφών: {total_incoming}")
            print(f"📊 Αριθμός στηλών: {len(columns_incoming)}")
            print("\n📋 Ονομασίες πεδίων (columns):")
            print("-" * 40)
            
            for i, col in enumerate(columns_incoming, 1):
                field_name = col.get('name', 'N/A')
                field_label = col.get('label', 'N/A')
                field_type = col.get('type', 'N/A')
                print(f"{i:2}. {field_name:30} | Label: {field_label:20} | Type: {field_type}")
            
            # Αποθήκευση για σύγκριση
            with open('incoming_columns.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'endpoint': 'Εισερχόμενες (queryId=6)',
                    'columns': columns_incoming,
                    'fetched_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            print("\n✅ Αποθηκεύθηκαν σε incoming_columns.json")
            
        else:
            print(f"❌ Αποτυχία: {data_incoming}")
            return
            
    except Exception as e:
        print(f"❌ Σφάλμα: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ============ ΔΙΕΚΠΕΡΑΙΩΜΕΝΕΣ ΥΠΟΘΕΣΕΙΣ ============
    print("\n\n📋 ΔΙΕΚΠΕΡΑΙΩΜΕΝΕΣ ΥΠΟΘΕΣΕΙΣ (queryId=19)")
    print("-" * 80)
    
    params_settled = SETTLED_CASES_DEFAULT_PARAMS.copy()
    params_settled['limit'] = 5  # Μόνο 5 records για γρήγορη δοκιμή
    
    try:
        data_settled = session.fetch_data(params_settled)
        
        if data_settled and data_settled.get('success'):
            columns_settled = data_settled.get('columns', [])
            total_settled = data_settled.get('total', 0)
            
            print(f"✅ Success: Σύνολο εγγραφών: {total_settled}")
            print(f"📊 Αριθμός στηλών: {len(columns_settled)}")
            print("\n📋 Ονομασίες πεδίων (columns):")
            print("-" * 40)
            
            for i, col in enumerate(columns_settled, 1):
                field_name = col.get('name', 'N/A')
                field_label = col.get('label', 'N/A')
                field_type = col.get('type', 'N/A')
                print(f"{i:2}. {field_name:30} | Label: {field_label:20} | Type: {field_type}")
            
            # Αποθήκευση για σύγκριση
            with open('settled_columns.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'endpoint': 'Διεκπεραιωμένες (queryId=19)',
                    'columns': columns_settled,
                    'fetched_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            print("\n✅ Αποθηκεύθηκαν σε settled_columns.json")
            
        else:
            print(f"❌ Αποτυχία: {data_settled}")
            return
            
    except Exception as e:
        print(f"❌ Σφάλμα: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ============ ΣΥΓΚΡΙΣΗ ============
    print("\n\n" + "="*80)
    print("🔄 ΣΥΓΚΡΙΣΗ ΠΕΔΙΩΝ")
    print("="*80)
    
    incoming_names = {col.get('name') for col in columns_incoming}
    settled_names = {col.get('name') for col in columns_settled}
    
    common = incoming_names & settled_names
    only_incoming = incoming_names - settled_names
    only_settled = settled_names - incoming_names
    
    print(f"\n✅ Κοινά πεδία ({len(common)}):")
    for name in sorted(common):
        print(f"   • {name}")
    
    print(f"\n📥 Μόνο σε Εισερχόμενες ({len(only_incoming)}):")
    for name in sorted(only_incoming):
        print(f"   • {name}")
    
    print(f"\n📋 Μόνο σε Διεκπεραιωμένες ({len(only_settled)}):")
    for name in sorted(only_settled):
        print(f"   • {name}")
    
    # ============ ΣΥΣΤΑΣΕΙΣ ============
    print("\n\n" + "="*80)
    print("💡 ΣΥΣΤΑΣΕΙΣ ΓΙΑ ΕΝΗΜΕΡΩΣΗ")
    print("="*80)
    
    print("\n1️⃣ Αν θέλετε να ενημερώσετε το src/settled_cases.py:")
    print("   Αντικαταστήστε τα field mappings με αυτά που βρήκατε")
    
    print("\n2️⃣ Πεδία που βρήκατε:")
    print("\n   Διεκπεραιωμένες:")
    for col in columns_settled[:5]:
        print(f"      '{col.get('name')}': '{col.get('label')}'")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    get_columns_comparison()
