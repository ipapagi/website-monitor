"""
Συσχέτιση OTS Εισερχόμενων (Πρωτόκολλο) με Portal Εισερχόμενα
"""
import json
import os
from datetime import datetime

from session import PKMSession
from config import INCOMING_DEFAULT_PARAMS

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

load_dotenv()
USERNAME = os.getenv('PKM_USERNAME', '')
PASSWORD = os.getenv('PKM_PASSWORD', '')

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'tmp')

# OTS Configuration
OTS_INCOMING_PARAMS = {
    'queryId': '2',
    'queryOwner': '3',
    'isCase': 'false',
    'stateId': 'welcomeGrid-18_dashboard0',
    'page': '1',
    'start': '0',
    'limit': '100',
    'isPoll': 'false'
}


def correlate_ots_with_portal():
    """Συσχετίζει OTS εισερχόμενα με Portal εισερχόμενα"""
    print("\n" + "=" * 80)
    print("🔗 ΣΥΣΧΕΤΙΣΗ: OTS Εισερχόμενα <-> Portal Εισερχόμενα")
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

    # Ανάκτηση OTS
    print("\n1️⃣ Ανάκτηση OTS εισερχόμενων (Πρωτόκολλο)...")
    ots_data = session.fetch_data(OTS_INCOMING_PARAMS)
    ots_records = ots_data.get('data', []) if ots_data and ots_data.get('success') else []
    print(f"✅ OTS: {len(ots_records)} εγγραφές")

    # Ανάκτηση Portal
    print("\n2️⃣ Ανάκτηση Portal εισερχόμενων...")
    portal_params = INCOMING_DEFAULT_PARAMS.copy()
    portal_params['limit'] = 200
    portal_data = session.fetch_data(portal_params)
    portal_records = portal_data.get('data', []) if portal_data and portal_data.get('success') else []
    print(f"✅ Portal: {len(portal_records)} εγγραφές")

    # Ανάλυση πεδίων
    print("\n3️⃣ Ανάλυση πεδίων για συσχέτιση...")
    print("-" * 80)

    # OTS keys
    if ots_records:
        ots_sample = ots_records[0]
        print(f"\n📋 OTS πεδία που μπορεί να συσχετίζονται:")
        for key in ots_sample.keys():
            value = str(ots_sample.get(key, ''))
            if value and value.strip() and len(value) < 100:
                print(f"   {key:30} = {value}")

    # Portal keys  
    if portal_records:
        portal_sample = portal_records[0]
        print(f"\n📋 Portal πεδία που μπορεί να συσχετίζονται:")
        potential_fields = ['DOCID', 'W007_P_FLD1', 'W007_P_FLD21', 'W007_P_FLD53']
        for key in portal_sample.keys():
            if 'DOC' in key.upper() or 'ID' in key.upper() or key in potential_fields:
                value = str(portal_sample.get(key, ''))
                if value and len(value) < 100:
                    print(f"   {key:30} = {value}")

    # Δημιουργία mapping από OTS ΠΚΜ (από DESCRIPTION)
    print("\n4️⃣ Δημιουργία OTS mapping (ΠΚΜ από DESCRIPTION -> Record)...")
    import html
    import re
    
    ots_by_pkm = {}
    for rec in ots_records:
        description = rec.get('DESCRIPTION', '')
        # Decode HTML entities
        description = html.unescape(description)
        # Extract PKM number: "Αίτημα 2026/106653 ..." -> 106653
        match = re.search(r'Αίτημα\s+\d+/(\d+)', description)
        if match:
            pkm = match.group(1)
            ots_by_pkm[pkm] = rec
    print(f"✅ OTS με ΠΚΜ: {len(ots_by_pkm)}")

    # Αναζήτηση συσχετίσεων
    print("\n5️⃣ Αναζήτηση συσχετίσεων (Portal ΠΚΜ με OTS DESCRIPTION)...")
    print("-" * 80)

    correlations = []
    portal_pkms_found = set()

    # Έλεγχος κάθε Portal record για match με OTS ΠΚΜ
    for portal_rec in portal_records:
        pkm = str(portal_rec.get('W007_P_FLD21', '')).strip()
        
        if pkm and pkm in ots_by_pkm:
            correlations.append({
                'pkm': pkm,
                'portal': portal_rec,
                'ots': ots_by_pkm[pkm]
            })
            portal_pkms_found.add(pkm)

    print(f"✅ Βρέθηκαν {len(correlations)} συσχετίσεις")

    # Απεικόνιση αποτελεσμάτων
    if correlations:
        print("\n" + "=" * 80)
        print(f"✅ ΣΥΣΧΕΤΙΣΜΕΝΕΣ ΕΓΓΡΑΦΕΣ ({len(correlations)})")
        print("=" * 80)

        for i, corr in enumerate(correlations[:20], 1):  # Πρώτες 20
            pkm = corr['pkm']
            portal = corr['portal']
            ots = corr['ots']

            party = portal.get('W007_P_FLD13', '')[:40]
            portal_date = portal.get('W007_P_FLD3', '')[:10]
            assigned_to = ots.get('USER_GROUP_ID_TO', '')[:50]
            date_assigned = ots.get('DATE_START_ISO', '')[:10]

            print(f"\n{i:2}. ΠΚΜ: {pkm}")
            print(f"    Portal:    Ημ/νία {portal_date} | {party}")
            print(f"    OTS:       Χρεώθηκε σε: {assigned_to}")
            print(f"    Ανάθεση:   {date_assigned}")

        if len(correlations) > 20:
            print(f"\n    ... και {len(correlations) - 20} ακόμα")

    # OTS χωρίς Portal
    ots_without_portal = [
        rec for pkm, rec in ots_by_pkm.items()
        if pkm not in portal_pkms_found
    ]

    if ots_without_portal:
        print("\n" + "=" * 80)
        print(f"⚠️  OTS ΧΩΡΙΣ PORTAL ({len(ots_without_portal)})")
        print("=" * 80)
        print("   (Πιθανά εισερχόμενα που δεν είναι από Portal)")

        for i, ots in enumerate(ots_without_portal[:10], 1):
            description = html.unescape(ots.get('DESCRIPTION', ''))[:60]
            assigned_to = ots.get('USER_GROUP_ID_TO', '')[:50]
            date_assigned = ots.get('DATE_START_ISO', '')[:10]
            print(f"   {i:2}. {description:60} | {assigned_to:50} | {date_assigned}")

    # Portal χωρίς OTS  
    portal_without_ots = [
        rec for rec in portal_records[:50]  # Πρώτες 50 για έλεγχο
        if str(rec.get('W007_P_FLD21', '')).strip() not in portal_pkms_found
    ]

    if portal_without_ots:
        print("\n" + "=" * 80)
        print(f"⏳ PORTAL ΧΩΡΙΣ OTS ΧΡΕΩΣΗ (από δείγμα {len(portal_records[:50])})")
        print("=" * 80)
        print("   (Εισερχόμενες που δεν έχουν χρεωθεί σε τμήμα)")

        for i, portal in enumerate(portal_without_ots[:10], 1):
            pkm = portal.get('W007_P_FLD21', '')
            party = portal.get('W007_P_FLD13', '')[:40]
            date = portal.get('W007_P_FLD3', '')[:10]
            print(f"   {i:2}. ΠΚΜ: {pkm:10} | {party:40} | {date}")

    # Αποθήκευση αποτελεσμάτων
    print("\n6️⃣ Αποθήκευση αποτελεσμάτων...")
    
    correlation_file = os.path.join(OUT_DIR, 'ots_portal_correlation.json')
    with open(correlation_file, 'w', encoding='utf-8') as f:
        json.dump({
            'correlations': correlations,
            'stats': {
                'total_ots': len(ots_records),
                'total_portal': len(portal_records),
                'matched': len(correlations),
                'match_rate': len(correlations) / len(ots_records) if ots_records else 0
            },
            'ots_without_portal_count': len(ots_without_portal),
            'generated_at': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    print(f"✅ Αποθηκεύτηκε σε: {correlation_file}")

    # Σύνοψη
    print("\n" + "=" * 80)
    print("📊 ΣΥΝΟΨΗ ΣΥΣΧΕΤΙΣΗΣ")
    print("=" * 80)
    print(f"   OTS εισερχόμενα:              {len(ots_records)}")
    print(f"   Portal εισερχόμενα:           {len(portal_records)}")
    print(f"   Συσχετίσεις βρέθηκαν:         {len(correlations)}")
    print(f"   Ποσοστό συσχέτισης:           {len(correlations) / len(ots_records) * 100 if ots_records else 0:.1f}%")
    print(f"   OTS χωρίς Portal:             {len(ots_without_portal)}")
    print(f"   Portal χωρίς OTS (δείγμα):    {len(portal_without_ots)}")

    print("\n" + "=" * 80)
    print("✅ ΟΛΟΚΛΗΡΩΣΗ ΣΥΣΧΕΤΙΣΗΣ")
    print("=" * 80)

    return {
        'correlations': correlations,
        'ots_records': ots_records,
        'portal_records': portal_records
    }


if __name__ == '__main__':
    correlate_ots_with_portal()
