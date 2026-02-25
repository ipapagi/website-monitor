"""
Εξερεύνηση Εισερχόμενων Από Πρωτόκολλο (OTS)
"""
import json
import os
from datetime import datetime

from session import PKMSession

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

load_dotenv()
USERNAME = os.getenv('PKM_USERNAME', '')
PASSWORD = os.getenv('PKM_PASSWORD', '')

# Configuration για OTS Incoming
OTS_INCOMING_PARAMS = {
    'queryId': '2',
    'queryOwner': '3',
    'isCase': 'false',
    'stateId': 'welcomeGrid-18_dashboard0',
    'page': '1',
    'start': '0',
    'limit': '50',
    'isPoll': 'false'
}


def explore_ots_incoming():
    """Εξερεύνηση OTS εισερχόμενων και των λεπτομερειών τους"""
    print("\n" + "=" * 80)
    print("🔍 ΕΞΕΡΕΥΝΗΣΗ: Εισερχόμενα Από Πρωτόκολλο (OTS)")
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

    # Βήμα 1: Λίστα εισερχόμενων από πρωτόκολλο
    print("\n1️⃣ Ανάκτηση λίστας OTS εισερχόμενων...")
    data = session.fetch_data(OTS_INCOMING_PARAMS)
    
    if not data or not data.get('success'):
        print("❌ Αποτυχία ανάκτησης")
        if data:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    
    records = data.get('data', [])
    metadata = data.get('metaData', {})
    columns = metadata.get('columns', [])
    total = data.get('total', 0)
    
    print(f"✅ Success: Σύνολο εγγραφών: {total}")
    print(f"📊 Αριθμός στηλών: {len(columns)}")
    print(f"📋 Ανακτήθηκαν: {len(records)} εγγραφές")
    
    # Εμφάνιση columns
    print("\n2️⃣ Δομή πεδίων (columns):")
    print("-" * 80)
    for i, col in enumerate(columns, 1):
        if isinstance(col, dict):
            data_index = col.get('dataIndex', '')
            header = col.get('header', '')
            field_type = col.get('type', '')
            print(f"{i:2}. {data_index:30} | {header:30} | Type: {field_type}")
    
    # Αποθήκευση columns
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'tmp')
    os.makedirs(out_dir, exist_ok=True)
    
    columns_file = os.path.join(out_dir, 'ots_incoming_columns.json')
    with open(columns_file, 'w', encoding='utf-8') as f:
        json.dump({
            'endpoint': 'OTS Incoming (queryId=2)',
            'columns': columns,
            'total': total,
            'fetched_at': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Columns αποθηκεύτηκαν σε: {columns_file}")
    
    # Δείγμα εγγραφών
    print("\n3️⃣ Δείγμα εγγραφών:")
    print("-" * 80)
    
    sample_records = records[:10]
    for i, rec in enumerate(sample_records, 1):
        # Προσπάθεια να βρούμε key fields
        doc_id = rec.get('DOCID', rec.get('docid', ''))
        record_id = rec.get('id', rec.get('ID', ''))
        
        print(f"\n{i}. Record ID: {record_id} | DOCID: {doc_id}")
        
        # Εμφάνιση όλων των πεδίων
        for key, value in list(rec.items())[:15]:  # Πρώτα 15 πεδία
            if value and str(value).strip():
                print(f"   {key:25} = {str(value)[:60]}")
    
    # Αποθήκευση δείγματος
    sample_file = os.path.join(out_dir, 'ots_incoming_sample.json')
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_records, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Δείγμα εγγραφών αποθηκεύτηκε σε: {sample_file}")
    
    # Βήμα 2: Ανάλυση των πεδίων που ήδη διαθέτουμε
    print("\n" + "=" * 80)
    print("4️⃣ ΑΝΆΛΥΣΗ ΠΕΔΊΩΝ ΓΙΑ ΧΡΈΩΣΗ & ΑΝΆΘΕΣΗ")
    print("=" * 80)
    print("""
Note: Το detail endpoint (/fetchDataTableRecord) έχει ξεχωριστή authentication.
      Όμως δεν χρειάζεται! Το list endpoint ήδη παρέχει όλες τις πληροφορίες.
""")
    
    # Ανάλυση των πεδίων που αφορούν χρέωση/υπάλληλο
    print("\n🔍 Πεδία που αφορούν χρέωση/ανάθεση:")
    print("-" * 80)
    
    if sample_records:
        rec = sample_records[0]
        
        # Πεδία που αναζητούμε
        key_fields = [
            ('USER_GROUP_ID_TO', 'Department assigned to'),
            ('USER_GROUP_ID_TO_ID', 'Department ID'),
            ('USER_ID_FROM', 'Assigned by (From)'),
            ('USER_ID_FROM_ID', 'User ID from'),
            ('USER_ID_LOCKED', 'Locked by user'),
            ('USER_ID_LOCKED_ID', 'Locked by user ID'),
            ('USER_ID_FINISHD', 'Finished by user'),
            ('USER_ID_FINISHD_ID', 'Finished by user ID'),
            ('USER_GROUP_ID_LOCKED', 'Locked by group'),
            ('USER_GROUP_ID_FINISHD', 'Finished by group'),
            ('DATE_START_ISO', 'Assignment start date'),
            ('DATE_START', 'Assignment start (formatted)'),
            ('DATE_END_ISO', 'Assignment end date'),
            ('DATE_END', 'Assignment end (formatted)'),
            ('DATE_FINISHED', 'Finished date'),
            ('ACTIONS', 'Current action/status'),
            ('XR_ACTIONS', 'Action type'),
        ]
        
        found_fields = []
        for field_name, description in key_fields:
            if field_name in rec and rec[field_name]:
                value = rec[field_name]
                found_fields.append((field_name, description, value))
                print(f"   ✅ {field_name:25} | {description:30} | {str(value)[:50]}")
        
        if not found_fields:
            print("   ℹ️  Δεν βρέθηκαν πεδία χρέωσης στο δείγμα")
        
        print(f"\n   Σύνολο πεδίων χρέωσης που βρέθηκαν: {len(found_fields)}")
    
    # Ανάλυση όλων των εγγραφών
    print("\n📊 Ανάλυση όλων των OTS εγγραφών:")
    print("-" * 80)
    
    stats = {
        'total': len(records),
        'with_department': 0,
        'with_user_from': 0,
        'with_locked_user': 0,
        'with_finished_user': 0,
        'departments': set(),
        'statuses': set()
    }
    
    for rec in records:
        if rec.get('USER_GROUP_ID_TO'):
            stats['with_department'] += 1
            dept = str(rec.get('USER_GROUP_ID_TO', ''))[:50]
            stats['departments'].add(dept)
        
        if rec.get('USER_ID_FROM'):
            stats['with_user_from'] += 1
        
        if rec.get('USER_ID_LOCKED'):
            stats['with_locked_user'] += 1
        
        if rec.get('USER_ID_FINISHD'):
            stats['with_finished_user'] += 1
        
        status = rec.get('ACTIONS')
        if status:
            stats['statuses'].add(str(status))
    
    print(f"   Σύνολο OTS εγγραφών:           {stats['total']}")
    print(f"   Με USER_GROUP_ID_TO:          {stats['with_department']} ({stats['with_department']/stats['total']*100:.1f}%)")
    print(f"   Με USER_ID_FROM:              {stats['with_user_from']} ({stats['with_user_from']/stats['total']*100:.1f}%)")
    print(f"   Με USER_ID_LOCKED:            {stats['with_locked_user']} ({stats['with_locked_user']/stats['total']*100:.1f}%)")
    print(f"   Με USER_ID_FINISHD:           {stats['with_finished_user']} ({stats['with_finished_user']/stats['total']*100:.1f}%)")
    print(f"   Διαφορετικές τμήματα:         {len(stats['departments'])}")
    print(f"   Διαφορετικές καταστάσεις:     {len(stats['statuses'])}")
    
    print(f"\n   Όλες οι καταστάσεις (ACTIONS):")
    for status in sorted(stats['statuses']):
        print(f"      • {status}")
    
    # Αποθήκευση πληροφοριών
    stats_file = os.path.join(out_dir, 'ots_incoming_stats.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump({
            'endpoint': 'OTS Incoming (queryId=2)',
            'total_records': stats['total'],
            'with_department_assignments': stats['with_department'],
            'with_user_from': stats['with_user_from'],
            'with_locked_user': stats['with_locked_user'],
            'with_finished_user': stats['with_finished_user'],
            'unique_departments': len(stats['departments']),
            'unique_statuses': list(stats['statuses']),
            'generated_at': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Στατιστικά αποθηκεύτηκαν σε: {stats_file}")
    
    # Σύνοψη
    print("\n" + "=" * 80)
    print("� ΣΥΝΟΨΗ")
    print("=" * 80)
    print(f"   Σύνολο OTS εισερχόμενων:    {total}")
    print(f"   Ανακτήθηκαν:                 {len(records)}")
    print(f"   Αρχεία εξόδου:")
    print(f"      • data/tmp/ots_incoming_columns.json")
    print(f"      • data/tmp/ots_incoming_sample.json")
    print(f"      • data/tmp/ots_incoming_stats.json")
    
    print("\n💡 Κύρια ευρήματα:")
    print(f"   • {stats['with_department']} εγγραφές έχουν ανάθεση τμήματος (USER_GROUP_ID_TO)")
    print(f"   • {len(stats['departments'])} διαφορετικές τμήματα")
    print(f"   • Στατιστικές αποθηκεύτηκαν για περαιτέρω ανάλυση")
    
    print("\n" + "=" * 80)
    print("✅ ΟΛΟΚΛΗΡΩΣΗ ΕΞΕΡΕΥΝΗΣΗΣ")
    print("=" * 80)
    
    return {
        'records': records,
        'columns': columns,
        'total': total,
        'stats': stats
    }


if __name__ == '__main__':
    explore_ots_incoming()
