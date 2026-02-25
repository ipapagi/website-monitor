"""
Test συσχέτισης εισερχόμενων με διεκπεραιωμένες υποθέσεις
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from monitor import PKMMonitor
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from utils import load_config
from settled_cases import (
    fetch_settled_cases, 
    correlate_incoming_with_settled,
    filter_out_settled_from_incoming,
    get_settled_for_incoming
)

load_dotenv()


def test_correlation():
    """Δοκιμή συσχέτισης εισερχόμενων με διεκπεραιωμένες"""
    print("=" * 80)
    print("🔗 ΔΟΚΙΜΗ ΣΥΣΧΕΤΙΣΗΣ: Εισερχόμενες <-> Διεκπεραιωμένες")
    print("=" * 80)
    
    # Σύνδεση
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
    
    print("\n0️⃣ Σύνδεση...")
    if not monitor.login():
        print("❌ Αποτυχία login")
        return
    print("✅ Επιτυχής σύνδεση")
    
    # Ανάκτηση εισερχόμενων
    print("\n1️⃣ Ανάκτηση εισερχόμενων...")
    params = INCOMING_DEFAULT_PARAMS.copy()
    params['limit'] = 50
    monitor.api_params = params
    incoming_data = monitor.fetch_page()
    incoming_records = incoming_data.get('data', [])
    print(f"✅ Ανακτήθηκαν {len(incoming_records)} εισερχόμενες")
    
    # Ανάκτηση διεκπεραιωμένων
    print("\n2️⃣ Ανάκτηση διεκπεραιωμένων...")
    settled_result = fetch_settled_cases(monitor)
    settled_records = settled_result.get('data', [])
    print(f"✅ Ανακτήθηκαν {len(settled_records)} διεκπεραιωμένες")
    
    # Συσχέτιση
    print("\n3️⃣ Συσχέτιση...")
    correlation = correlate_incoming_with_settled(incoming_records, settled_records)
    
    # Στατιστικά
    stats = correlation['stats']
    print("\n" + "=" * 80)
    print("📊 ΣΤΑΤΙΣΤΙΚΑ ΣΥΣΧΕΤΙΣΗΣ")
    print("=" * 80)
    print(f"   Εισερχόμενες:        {stats['total_incoming']}")
    print(f"   Διεκπεραιωμένες:     {stats['total_settled']}")
    print(f"   Αντιστοιχίες:        {stats['matched']}")
    print(f"   Ποσοστό:             {stats['match_rate']:.1%}")
    print(f"   Ενεργές (χωρίς διεκπ): {len(correlation['incoming_without_settled'])}")
    
    # Προβολή αντιστοιχιών
    if correlation['correlated']:
        print("\n" + "=" * 80)
        print(f"✅ ΔΙΕΚΠΕΡΑΙΩΜΕΝΕΣ ΑΙΤΗΣΕΙΣ ({len(correlation['correlated'])})")
        print("=" * 80)
        
        for i, item in enumerate(correlation['correlated'], 1):
            case_code = item['case_code']
            inc = item['incoming']
            settled = item['settled']
            
            party = inc.get('W007_P_FLD13', '')[:35]
            completion = settled.get('W001_P_FLD8', '')
            status = settled.get('W001_P_FLD9', '')
            
            print(f"{i:2}. {case_code:15} | {party:35} | {completion:12} | {status}")
    
    # Προβολή ενεργών
    if correlation['incoming_without_settled']:
        print("\n" + "=" * 80)
        print(f"⏳ ΕΝΕΡΓΕΣ ΑΙΤΗΣΕΙΣ ({len(correlation['incoming_without_settled'])})")
        print("=" * 80)
        
        for i, inc in enumerate(correlation['incoming_without_settled'], 1):
            party = inc.get('W007_P_FLD13', '')[:40]
            pkm = inc.get('W007_P_FLD21', '')
            procedure = inc.get('W007_P_FLD23', '')[:35]
            date = inc.get('W007_P_FLD3', '')
            
            print(f"{i:2}. ΠΚΜ {pkm:10} | {party:40} | {date:12} | {procedure}")
    
    # Test filter_out_settled_from_incoming
    print("\n" + "=" * 80)
    print("🔍 ΔΟΚΙΜΗ ΦΙΛΤΡΑΡΙΣΜΑΤΟΣ")
    print("=" * 80)
    
    active_only = filter_out_settled_from_incoming(incoming_records, settled_records)
    
    print(f"   Αρχικές εισερχόμενες:     {len(incoming_records)}")
    print(f"   Μετά από φιλτράρισμα:     {len(active_only)}")
    print(f"   Αφαιρέθηκαν:               {len(incoming_records) - len(active_only)}")
    
    # Test get_settled_for_incoming
    print("\n" + "=" * 80)
    print("🔎 ΔΟΚΙΜΗ ΑΝΑΖΗΤΗΣΗΣ ΔΙΕΚΠΕΡΑΙΩΣΗΣ")
    print("=" * 80)
    
    # Βρες μια εισερχόμενη που έχει διεκπεραιωθεί
    if correlation['correlated']:
        test_incoming = correlation['correlated'][0]['incoming']
        party = test_incoming.get('W007_P_FLD13', '')[:40]
        
        print(f"\nΈλεγχος για: {party}")
        
        settled = get_settled_for_incoming(test_incoming, settled_records)
        if settled:
            print("   ✅ Βρέθηκε διεκπεραίωση")
            print(f"      Κωδ. Υπόθεσης:       {settled.get('W001_P_FLD2', '')}")
            print(f"      Ημ/νία Διεκπ.:       {settled.get('W001_P_FLD8', '')}")
            print(f"      Κατάσταση:           {settled.get('W001_P_FLD9', '')}")
        else:
            print("   ❌ Δεν βρέθηκε διεκπεραίωση")
    
    # Έλεγχος για μια που δεν έχει διεκπεραιωθεί
    if correlation['incoming_without_settled']:
        test_incoming = correlation['incoming_without_settled'][0]
        party = test_incoming.get('W007_P_FLD13', '')[:40]
        
        print(f"\nΈλεγχος για: {party}")
        
        settled = get_settled_for_incoming(test_incoming, settled_records)
        if settled:
            print("   ✅ Βρέθηκε διεκπεραίωση")
        else:
            print("   ⏳ Δεν έχει διεκπεραιωθεί (αναμενόμενο)")
    
    print("\n" + "=" * 80)
    print("✅ ΟΛΟΚΛΗΡΩΣΗ ΔΟΚΙΜΩΝ")
    print("=" * 80)


if __name__ == '__main__':
    test_correlation()
