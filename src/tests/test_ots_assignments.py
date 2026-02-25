"""
Test: OTS Assignments Integration
Δοκιμή ενσωμάτωσης αναθέσεων τμημάτων στα incoming records
"""
import os
from dotenv import load_dotenv

from session import PKMSession
from config import INCOMING_DEFAULT_PARAMS
from ots_assignments import (
    fetch_ots_assignments,
    add_assignment_info,
    get_assignment_info,
    filter_assigned,
    filter_unassigned,
    get_assignment_statistics,
    format_assignment_for_display,
    simplify_ots_record
)
from utils import sanitize_party_name

load_dotenv()
USERNAME = os.getenv('PKM_USERNAME', '')
PASSWORD = os.getenv('PKM_PASSWORD', '')


def test_ots_assignments_integration():
    """Δοκιμάζει την ολοκληρωμένη λειτουργία OTS assignments"""
    
    print("\n" + "=" * 80)
    print("🔧 TEST: OTS ASSIGNMENTS INTEGRATION")
    print("=" * 80)
    
    # Σύνδεση
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
    
    # 1. Ανάκτηση OTS
    print("\n1️⃣ Ανάκτηση OTS assignments...")
    ots_records, ots_by_pkm = fetch_ots_assignments(session)
    print(f"✅ OTS: {len(ots_records)} εγγραφές")
    print(f"✅ Mapping: {len(ots_by_pkm)} με ΠΚΜ")
    
    # 2. Ανάκτηση Portal incoming
    print("\n2️⃣ Ανάκτηση Portal incoming...")
    portal_params = INCOMING_DEFAULT_PARAMS.copy()
    portal_params['limit'] = 100
    portal_data = session.fetch_data(portal_params)
    portal_records = portal_data.get('data', []) if portal_data and portal_data.get('success') else []
    print(f"✅ Portal: {len(portal_records)} εγγραφές")
    
    # 3. Προσθήκη assignment info
    print("\n3️⃣ Εμπλουτισμός με assignment info...")
    enriched_records = add_assignment_info(portal_records[:50], ots_by_pkm)
    print(f"✅ Enriched: {len(enriched_records)} εγγραφές")
    
    # 4. Στατιστικά
    print("\n4️⃣ Στατιστικά αναθέσεων...")
    print("-" * 80)
    stats = get_assignment_statistics(enriched_records)
    print(f"Σύνολο:               {stats['total']}")
    print(f"Ανατεθειμένες:        {stats['assigned']} ({stats['assigned_percentage']:.1f}%)")
    print(f"Μη ανατεθειμένες:     {stats['unassigned']} ({stats['unassigned_percentage']:.1f}%)")
    print(f"Διαφορετικά τμήματα:  {stats['unique_departments']}")
    
    # 5. Κατανομή ανά τμήμα
    if stats['by_department']:
        print("\n5️⃣ Κατανομή ανά τμήμα:")
        print("-" * 80)
        sorted_depts = sorted(stats['by_department'].items(), key=lambda x: x[1], reverse=True)
        for dept, count in sorted_depts[:10]:
            print(f"   {count:2} | {dept}")
        if len(sorted_depts) > 10:
            print(f"   ... και {len(sorted_depts) - 10} ακόμα τμήματα")
    
    # 6. Ανατεθειμένες εισερχόμενες
    assigned = filter_assigned(enriched_records)
    if assigned:
        print("\n" + "=" * 80)
        print(f"✅ ΑΝΑΤΕΘΕΙΜΕΝΕΣ ΕΙΣΕΡΧΟΜΕΝΕΣ ({len(assigned)})")
        print("=" * 80)
        
        for i, rec in enumerate(assigned[:15], 1):
            pkm = rec.get('W007_P_FLD21', '')
            party = sanitize_party_name(rec.get('W007_P_FLD13', ''))[:40]
            date = rec.get('W007_P_FLD3', '')[:10]
            assignment_info = format_assignment_for_display(rec)
            
            print(f"\n{i:2}. ΠΚΜ: {pkm} | {date}")
            print(f"    Συναλλασσόμενος: {party}")
            print(f"    {assignment_info}")
        
        if len(assigned) > 15:
            print(f"\n    ... και {len(assigned) - 15} ακόμα")
    
    # 7. Μη ανατεθειμένες
    unassigned = filter_unassigned(enriched_records)
    if unassigned:
        print("\n" + "=" * 80)
        print(f"⏳ ΜΗ ΑΝΑΤΕΘΕΙΜΕΝΕΣ ΕΙΣΕΡΧΟΜΕΝΕΣ ({len(unassigned)})")
        print("=" * 80)
        print("   (Εισερχόμενες που δεν έχουν χρεωθεί σε τμήμα ακόμα)")
        
        for i, rec in enumerate(unassigned[:10], 1):
            pkm = rec.get('W007_P_FLD21', '')
            party = sanitize_party_name(rec.get('W007_P_FLD13', ''))[:40]
            date = rec.get('W007_P_FLD3', '')[:10]
            procedure = rec.get('W007_P_FLD8', '')[:35]
            
            print(f"   {i:2}. ΠΚΜ: {pkm:6} | {date} | {party:40} | {procedure}")
        
        if len(unassigned) > 10:
            print(f"       ... και {len(unassigned) - 10} ακόμα")
    
    # 8. Παράδειγμα χρήσης get_assignment_info
    print("\n" + "=" * 80)
    print("📝 ΠΑΡΑΔΕΙΓΜΑ: get_assignment_info()")
    print("=" * 80)
    
    if assigned:
        example_rec = assigned[0]
        pkm = example_rec.get('W007_P_FLD21')
        assignment = get_assignment_info(example_rec, ots_by_pkm)
        
        if assignment:
            print(f"\nΓια ΠΚΜ {pkm}:")
            print(f"  Τμήμα:            {assignment['department_short']}")
            print(f"  Ημ/νία ανάθεσης:  {assignment['date_assigned_formatted']}")
            print(f"  Κατάσταση:        {assignment['status']}")
            print(f"  Ανατέθηκε από:    {assignment['assigned_by']}")
            print(f"  OTS DOCID:        {assignment['ots_docid']}")
    
    # 9. OTS records παράδειγμα
    print("\n" + "=" * 80)
    print("📋 ΠΑΡΑΔΕΙΓΜΑ: Simplified OTS Record")
    print("=" * 80)
    
    if ots_records:
        simplified = simplify_ots_record(ots_records[0])
        print(f"\nΠΚΜ:              {simplified['pkm']}")
        print(f"Περιγραφή:        {simplified['description'][:60]}...")
        print(f"Τμήμα:            {simplified['department_short']}")
        print(f"Ημ/νία:           {simplified['date_formatted']}")
        print(f"Κατάσταση:        {simplified['status']}")
        print(f"Ανατέθηκε από:    {simplified['assigned_by']}")
    
    # 10. Σύνοψη
    print("\n" + "=" * 80)
    print("📊 ΣΥΝΟΨΗ")
    print("=" * 80)
    print(f"OTS εγγραφές:                {len(ots_records)}")
    print(f"Portal εισερχόμενες:         {len(portal_records)}")
    print(f"Δείγμα που ελέγχθηκε:        {len(enriched_records)}")
    print(f"Συσχετίσεις βρέθηκαν:        {len(assigned)} ({len(assigned)/len(enriched_records)*100:.1f}%)")
    print(f"Χωρίς ανάθεση:               {len(unassigned)} ({len(unassigned)/len(enriched_records)*100:.1f}%)")
    print(f"Διαφορετικά τμήματα:         {stats['unique_departments']}")
    
    print("\n" + "=" * 80)
    print("✅ TEST ΟΛΟΚΛΗΡΩΘΗΚΕ")
    print("=" * 80)
    
    return {
        'enriched_records': enriched_records,
        'ots_by_pkm': ots_by_pkm,
        'stats': stats
    }


if __name__ == '__main__':
    test_ots_assignments_integration()
