"""
Αναζήτηση συσχέτισης μεταξύ Κωδ. Υπόθεσης (διεκπεραιωμένες) και εισερχόμενων
"""
import json
import os
from datetime import datetime

from session import PKMSession
from config import INCOMING_DEFAULT_PARAMS, SETTLED_CASES_DEFAULT_PARAMS

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

load_dotenv()
USERNAME = os.getenv('PKM_USERNAME', '')
PASSWORD = os.getenv('PKM_PASSWORD', '')


def analyze_correlation():
    """Αναλύει τη συσχέτιση μεταξύ των δύο endpoints"""
    print("\n" + "=" * 80)
    print("🔍 ΑΝΑΖΗΤΗΣΗ ΣΥΣΧΕΤΙΣΗΣ: Κωδ. Υπόθεσης")
    print("=" * 80)

    session = PKMSession(
        base_url="https://shde.pkm.gov.gr",
        urls={
            'login_page': '/login.jsp',
            'login_api': '/services/LoginServices/loginWeb',
            'main_page': '/ext_main.jsp?locale=el',
            'data_api': '/services/SearchServices/getSearchDataByQueryId'
        },
        login_params={
            'application': '2',
            'otp': ''
        },
        username=USERNAME,
        password=PASSWORD
    )

    # Ανάκτηση δειγμάτων
    print("\n1️⃣ Ανάκτηση δειγμάτων...")
    
    params_incoming = INCOMING_DEFAULT_PARAMS.copy()
    params_incoming['limit'] = 50
    data_incoming = session.fetch_data(params_incoming)
    
    params_settled = SETTLED_CASES_DEFAULT_PARAMS.copy()
    params_settled['limit'] = 50
    data_settled = session.fetch_data(params_settled)
    
    if not data_incoming.get('success') or not data_settled.get('success'):
        print("❌ Αποτυχία ανάκτησης")
        return
    
    incoming_records = data_incoming.get('data', [])
    settled_records = data_settled.get('data', [])
    
    print(f"✅ Εισερχόμενες: {len(incoming_records)} εγγραφές")
    print(f"✅ Διεκπεραιωμένες: {len(settled_records)} εγγραφές")
    
    # Ανάλυση δομής Κωδ. Υπόθεσης
    print("\n2️⃣ Ανάλυση Κωδ. Υπόθεσης (Διεκπεραιωμένες):")
    print("-" * 80)
    case_codes = []
    for i, rec in enumerate(settled_records[:10], 1):
        case_code = rec.get('W001_P_FLD2', '')
        case_codes.append(case_code)
        subject = rec.get('W001_P_FLD11', '')[:50]
        party = rec.get('W001_P_FLD21', '')[:30]
        print(f"{i:2}. {case_code:15} | {party:30} | {subject}")
    
    # Ανάλυση πιθανών πεδίων συσχέτισης στις εισερχόμενες
    print("\n3️⃣ Πιθανά πεδία συσχέτισης (Εισερχόμενες):")
    print("-" * 80)
    
    # Εξετάζουμε τα πεδία που μπορεί να περιέχουν τον κωδικό υπόθεσης
    potential_fields = [
        ('W007_P_FLD21', 'Αρ. ΠΚΜ'),
        ('W007_P_FLD7', 'Αφορά Υπόθεση'),
        ('W007_P_FLD1', 'Αρ. εγγράφου'),
    ]
    
    for field, label in potential_fields:
        print(f"\n📋 {label} ({field}):")
        for i, rec in enumerate(incoming_records[:10], 1):
            value = rec.get(field, '')
            subject = rec.get('W007_P_FLD6', '')[:40]
            party = rec.get('W007_P_FLD13', '')[:25]
            print(f"{i:2}. {str(value):20} | {party:25} | {subject}")
    
    # Προσπάθεια εύρεσης αντιστοιχιών
    print("\n4️⃣ Αναζήτηση αντιστοιχιών:")
    print("-" * 80)
    
    # Δημιουργία sets για γρήγορη αναζήτηση
    incoming_pkm_numbers = {str(rec.get('W007_P_FLD21', '')).strip().upper() 
                           for rec in incoming_records if rec.get('W007_P_FLD21')}
    
    incoming_case_refs = {str(rec.get('W007_P_FLD7', '')).strip().upper() 
                         for rec in incoming_records if rec.get('W007_P_FLD7')}
    
    matches_found = 0
    for rec in settled_records[:20]:
        case_code = str(rec.get('W001_P_FLD2', '')).strip().upper()
        if not case_code:
            continue
        
        # Έλεγχος αν ο κωδικός υπόθεσης εμφανίζεται στα πεδία των εισερχόμενων
        if case_code in incoming_pkm_numbers:
            matches_found += 1
            print(f"✅ MATCH in Αρ. ΠΚΜ: {case_code}")
        elif case_code in incoming_case_refs:
            matches_found += 1
            print(f"✅ MATCH in Αφορά Υπόθεση: {case_code}")
        elif any(case_code in str(rec.get('W007_P_FLD7', '')).upper() 
                for rec in incoming_records):
            matches_found += 1
            print(f"✅ MATCH (substring) in Αφορά Υπόθεση: {case_code}")
    
    if matches_found == 0:
        print("\n⚠️  Δεν βρέθηκαν άμεσες αντιστοιχίες στα δείγματα")
        print("\n💡 Πιθανές εξηγήσεις:")
        print("   • Οι εισερχόμενες δεν έχουν ακόμα γίνει υποθέσεις")
        print("   • Η συσχέτιση γίνεται μέσω άλλου πεδίου (π.χ. Συναλλασσόμενος)")
        print("   • Το 'Αφορά Υπόθεση' αναφέρεται σε άλλη υπόθεση, όχι στον ίδιο κωδικό")
    else:
        print(f"\n✅ Βρέθηκαν {matches_found} αντιστοιχίες")
    
    # Έλεγχος συσχέτισης μέσω Συναλλασσόμενου
    print("\n5️⃣ Συσχέτιση μέσω Συναλλασσόμενου:")
    print("-" * 80)
    
    # Δημιουργία mapping party -> records
    incoming_by_party = {}
    for rec in incoming_records:
        party = str(rec.get('W007_P_FLD13', '')).strip().upper()
        if party:
            if party not in incoming_by_party:
                incoming_by_party[party] = []
            incoming_by_party[party].append(rec)
    
    matched_parties = 0
    for rec in settled_records[:10]:
        party = str(rec.get('W001_P_FLD21', '')).strip().upper()
        case_code = rec.get('W001_P_FLD2', '')
        if party in incoming_by_party:
            matched_parties += 1
            incoming_count = len(incoming_by_party[party])
            print(f"✅ {party[:40]:40} | Υπόθεση: {case_code:15} | Εισερχ: {incoming_count}")
    
    print(f"\n📊 {matched_parties}/10 διεκπεραιωμένες έχουν εισερχόμενες με τον ίδιο συναλλασσόμενο")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    analyze_correlation()
