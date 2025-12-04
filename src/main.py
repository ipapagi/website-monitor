import sys
import os
import re

# Προσθήκη του src directory στο path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor import PKMMonitor
from utils import load_config
import argparse
import json
from datetime import datetime

INCOMING_DEFAULT_PARAMS = {
    'isPoll': False,
    'queryId': 6,
    'queryOwner': 2,
    'isCase': False,
    'stateId': 'welcomeGrid-23_dashboard0',
    'page': 1,
    'start': 0,
    'limit': 100
}

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_baseline_path():
    """Επιστρέφει το path του baseline αρχείου"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'data', 'active_procedures_baseline.json')

def save_baseline(active_procedures):
    """Αποθηκεύει τις ενεργές διαδικασίες ως baseline"""
    baseline_path = get_baseline_path()
    
    # Δημιουργία data φακέλου αν δεν υπάρχει
    os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
    
    baseline_data = {
        'timestamp': datetime.now().isoformat(),
        'count': len(active_procedures),
        'procedures': active_procedures
    }
    
    with open(baseline_path, 'w', encoding='utf-8') as f:
        json.dump(baseline_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Baseline αποθηκεύτηκε: {baseline_path}")
    print(f"📋 Ενεργές διαδικασίες: {len(active_procedures)}")
    return baseline_path

def load_baseline():
    """Φορτώνει το baseline αν υπάρχει"""
    baseline_path = get_baseline_path()
    
    if not os.path.exists(baseline_path):
        return None
    
    with open(baseline_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_with_baseline(current_procedures, baseline_data):
    """Συγκρίνει τις τρέχουσες διαδικασίες με το baseline"""
    baseline_procedures = baseline_data.get('procedures', [])
    
    # Δημιουργία dictionaries με βάση το docid
    baseline_dict = {p['docid']: p for p in baseline_procedures}
    current_dict = {p['docid']: p for p in current_procedures}
    
    changes = {
        'new': [],           # Νέες ενεργές
        'removed': [],       # Αφαιρέθηκαν (έγιναν ανενεργές)
        'activated': [],     # Έγιναν ενεργές (από ΟΧΙ σε ΝΑΙ)
        'deactivated': [],   # Έγιναν ανενεργές (από ΝΑΙ σε ΟΧΙ)
        'modified': []       # Άλλες αλλαγές
    }
    
    # Εύρεση νέων ενεργών
    for docid, proc in current_dict.items():
        if docid not in baseline_dict:
            if proc.get('ενεργή') == 'ΝΑΙ':
                changes['new'].append(proc)
        else:
            old_proc = baseline_dict[docid]
            # Έλεγχος αν άλλαξε η κατάσταση ενεργής
            if old_proc.get('ενεργή') != proc.get('ενεργή'):
                if proc.get('ενεργή') == 'ΝΑΙ':
                    changes['activated'].append({'old': old_proc, 'new': proc})
                else:
                    changes['deactivated'].append({'old': old_proc, 'new': proc})
            # Έλεγχος για άλλες αλλαγές σε ενεργές διαδικασίες
            elif proc.get('ενεργή') == 'ΝΑΙ' and old_proc != proc:
                # Βρες τι άλλαξε
                field_changes = {}
                for key in proc.keys():
                    if old_proc.get(key) != proc.get(key):
                        field_changes[key] = {
                            'old': old_proc.get(key, ''),
                            'new': proc.get(key, '')
                        }
                changes['modified'].append({
                    'old': old_proc, 
                    'new': proc,
                    'field_changes': field_changes
                })
    
    # Εύρεση διαδικασιών που αφαιρέθηκαν
    for docid, proc in baseline_dict.items():
        if docid not in current_dict:
            changes['removed'].append(proc)
    
    return changes

def print_comparison_results(changes, baseline_data):
    """Εμφανίζει τα αποτελέσματα της σύγκρισης"""
    baseline_time = baseline_data.get('timestamp', 'Άγνωστο')
    baseline_count = baseline_data.get('count', 0)
    
    print("\n" + "="*80)
    print("📊 ΣΥΓΚΡΙΣΗ ΜΕ BASELINE".center(80))
    print("="*80)
    print(f"📅 Baseline από: {baseline_time}")
    print(f"📋 Ενεργές στο baseline: {baseline_count}")
    print("="*80)
    
    has_changes = False
    
    if changes['new']:
        has_changes = True
        print(f"\n🆕 ΝΕΕΣ ΕΝΕΡΓΕΣ ΔΙΑΔΙΚΑΣΙΕΣ ({len(changes['new'])})")
        print("─" * 80)
        for idx, proc in enumerate(changes['new'], 1):
            print(f"{idx:3}. ✅ [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
    
    if changes['activated']:
        has_changes = True
        print(f"\n🔓 ΕΝΕΡΓΟΠΟΙΗΘΗΚΑΝ ({len(changes['activated'])})")
        print("─" * 80)
        for idx, item in enumerate(changes['activated'], 1):
            proc = item['new']
            print(f"{idx:3}. ✅ [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
            print(f"     └─ Ενεργή: ΟΧΙ → ΝΑΙ")
    
    if changes['deactivated']:
        has_changes = True
        print(f"\n🔒 ΑΠΕΝΕΡΓΟΠΟΙΗΘΗΚΑΝ ({len(changes['deactivated'])})")
        print("─" * 80)
        for idx, item in enumerate(changes['deactivated'], 1):
            proc = item['new']
            print(f"{idx:3}. ❌ [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
            print(f"     └─ Ενεργή: ΝΑΙ → ΟΧΙ")
    
    if changes['removed']:
        has_changes = True
        print(f"\n🗑️  ΑΦΑΙΡΕΘΗΚΑΝ ({len(changes['removed'])})")
        print("─" * 80)
        for idx, proc in enumerate(changes['removed'], 1):
            print(f"{idx:3}. ⚠️  [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
    
    if changes['modified']:
        has_changes = True
        print(f"\n🔄 ΤΡΟΠΟΠΟΙΗΘΗΚΑΝ ({len(changes['modified'])})")
        print("─" * 80)
        for idx, mod in enumerate(changes['modified'], 1):
            print(f"{idx:3}. 📝 [{mod['new'].get('κωδικός')}] {mod['new'].get('τίτλος', '')}")
            field_changes = mod.get('field_changes', {})
            for field, vals in field_changes.items():
                if field not in ['docid', '_raw']:
                    old_val = vals['old'] if vals['old'] else '(κενό)'
                    new_val = vals['new'] if vals['new'] else '(κενό)'
                    if len(str(old_val)) > 50:
                        old_val = str(old_val)[:50] + '...'
                    if len(str(new_val)) > 50:
                        new_val = str(new_val)[:50] + '...'
                    print(f"     └─ {field}: {old_val} → {new_val}")
    
    if not has_changes:
        print("\n✅ Καμία αλλαγή από το baseline!")
    
    print("\n" + "="*80)

def get_incoming_snapshot_path(date_str):
    project_root = get_project_root()
    incoming_dir = os.path.join(project_root, 'data', 'incoming_requests')
    os.makedirs(incoming_dir, exist_ok=True)
    return os.path.join(incoming_dir, f'incoming_{date_str}.json')

def load_incoming_snapshot(date_str):
    path = get_incoming_snapshot_path(date_str)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_incoming_snapshot(date_str, records):
    payload = {
        'date': date_str,
        'count': len(records),
        'records': records
    }
    with open(get_incoming_snapshot_path(date_str), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def list_incoming_snapshot_dates():
    incoming_dir = os.path.join(get_project_root(), 'data', 'incoming_requests')
    if not os.path.exists(incoming_dir):
        return []
    dates = []
    for filename in os.listdir(incoming_dir):
        if filename.startswith('incoming_') and filename.endswith('.json'):
            date_part = filename[len('incoming_'):-5]
            try:
                dates.append(datetime.strptime(date_part, "%Y-%m-%d").date())
            except ValueError:
                continue
    return sorted(dates)

def load_previous_incoming_snapshot(current_date_str):
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    for snapshot_date in reversed(list_incoming_snapshot_dates()):
        if snapshot_date < current_date:
            snapshot_str = snapshot_date.strftime("%Y-%m-%d")
            return snapshot_str, load_incoming_snapshot(snapshot_str)
    return None, None

def sanitize_party_name(raw_party):
    if not raw_party:
        return ''
    text = str(raw_party)
    text = re.sub(r'\s*[-–]?\s*\(?\b\d{9}\b\)?', '', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def simplify_incoming_records(records):
    simplified = []
    for rec in records:
        case_id_raw = (
            rec.get('W007_P_FLD21')
            or rec.get('Αρ. εγγράφου')
            or rec.get('αρ. εγγράφου')
            or rec.get('αρ_εγγράφου')
            or rec.get('DOCID')
            or rec.get('docid')
            or rec.get('CASE_ID')
        )
        case_id = str(case_id_raw or '').strip()
        if not case_id:
            continue
        submitted_at = rec.get('DATE_INSERTED_ISO') or rec.get('W003_DATA_INSERT') or rec.get('DATE_INSERT') or rec.get('SUBMIT_DATE') or ''
        party_raw = rec.get('W007_P_FLD13') or rec.get('party') or rec.get('customer') or rec.get('applicant') or ''
        party_name = sanitize_party_name(party_raw)
        doc_id = str(rec.get('DOCID') or rec.get('docid') or '').strip()
        simplified.append({
            'case_id': case_id,
            'submitted_at': submitted_at,
            'party': party_name,
            'doc_id': doc_id
        })
    return simplified

def compare_incoming_records(current, previous):
    previous_records = previous.get('records', []) if previous else []
    prev_dict = {r['case_id']: r for r in previous_records if r.get('case_id')}
    curr_dict = {r['case_id']: r for r in current if r.get('case_id')}
    new_docs = [r for cid, r in curr_dict.items() if cid not in prev_dict]
    removed_docs = [r for cid, r in prev_dict.items() if cid not in curr_dict]
    modified = []
    for cid, record in curr_dict.items():
        if cid in prev_dict and record.get('submitted_at') != prev_dict[cid].get('submitted_at'):
            modified.append({'old': prev_dict[cid], 'new': record})
    return {'new': new_docs, 'removed': removed_docs, 'modified': modified}

def print_incoming_changes(changes, has_reference_snapshot, date_str, reference_date_str=None):
    print("\n" + "="*80)
    print(f"📥 ΕΙΣΕΡΧΟΜΕΝΕΣ ΑΙΤΗΣΕΙΣ ({date_str})".center(80))
    print("="*80)
    if not has_reference_snapshot:
        print("ℹ️  Δεν βρέθηκε προηγούμενο snapshot. Δημιουργήθηκε baseline για μελλοντικές συγκρίσεις.")
    else:
        print(f"🔁 Σύγκριση με snapshot {reference_date_str}")
        if not any(changes.values()):
            print("✅ Καμία αλλαγή σε σχέση με το αποθηκευμένο snapshot.")
        if changes['new']:
            print(f"\n🆕 Νέες αιτήσεις ({len(changes['new'])})")
            print("─"*80)
            for idx, rec in enumerate(changes['new'], 1):
                party = (rec.get('party') or '').strip()
                case_id = rec.get('case_id', 'N/A')
                submitted = rec.get('submitted_at', 'N/A')
                submitted_display = submitted.ljust(26)
                party_display = party if party else '—'
                print(f"{idx:>3}. [+] Υπόθεση {case_id:<8} │ Ημερ.: {submitted_display} │ Συναλλασσόμενος: {party_display}")
        if changes['removed']:
            print(f"\n🗑️  Αφαιρέθηκαν ({len(changes['removed'])})")
            print("─"*80)
            for idx, rec in enumerate(changes['removed'], 1):
                party = f" – {rec.get('party')}" if rec.get('party') else ''
                print(f"{idx:3}. [-] Υπόθεση {rec.get('case_id', 'N/A')} – Ημερ.: {rec.get('submitted_at', 'N/A')}{party}")
        if changes['modified']:
            print(f"\n🔄 Τροποποιήθηκαν ({len(changes['modified'])})")
            print("─"*80)
            for idx, pair in enumerate(changes['modified'], 1):
                party = pair['new'].get('party') or pair['old'].get('party') or ''
                party_info = f" – {party}" if party else ''
                print(f"{idx:3}. [~] Υπόθεση {pair['new'].get('case_id', 'N/A')}{party_info}")
                print(f"     └─ Παλαιό: {pair['old'].get('submitted_at', '(κενό)')}")
                print(f"     └─ Νέο : {pair['new'].get('submitted_at', '(κενό)')}")
    print("\n" + "="*80)

def fetch_incoming_records(monitor, incoming_params):
    params = incoming_params.copy()
    original_params = monitor.api_params.copy()
    try:
        monitor.api_params = params
        return monitor.fetch_page()
    finally:
        monitor.api_params = original_params

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='PKM Website Monitor - Παρακολούθηση ενεργών διαδικασιών'
    )
    parser.add_argument(
        '--save-baseline', 
        action='store_true',
        help='Αποθηκεύει τις τρέχουσες ενεργές διαδικασίες ως baseline'
    )
    parser.add_argument(
        '--compare', 
        action='store_true',
        help='Συγκρίνει με το αποθηκευμένο baseline (χωρίς continuous monitoring)'
    )
    parser.add_argument(
        '--list-active', 
        action='store_true',
        help='Εμφανίζει τις ενεργές διαδικασίες'
    )
    parser.add_argument(
        '--no-monitor', 
        action='store_true',
        help='Δεν ξεκινά continuous monitoring'
    )
    parser.add_argument(
        '--check-incoming-portal',
        action='store_true',
        help='Ελέγχει τις εισερχόμενες αιτήσεις (portal) και αποθηκεύει ημερήσιο snapshot'
    )
    
    args = parser.parse_args()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "="*80)
    print(f"🚀 Εκκίνηση PKM Website Monitor - {current_time}".center(80))
    print("="*80)
    
    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    
    # Load configuration
    config = load_config(config_path)
    
    # Create monitor instance
    monitor = PKMMonitor(
        base_url=config.get('base_url', 'https://shde.pkm.gov.gr/dev'),
        urls=config.get('urls', {}),
        api_params=config.get('api_params', {}),
        login_params=config.get('login_params', {}),
        check_interval=config.get('check_interval', 300),
        username=config.get('username'),
        password=config.get('password'),
        session_cookies=config.get('session_cookies')
    )
    
    # Αν χρειάζεται σύγκριση ή αποθήκευση, πρέπει να πάρουμε τα δεδομένα
    if args.save_baseline or args.compare or args.list_active or args.check_incoming_portal:
        print("\n🔄 Ανάκτηση δεδομένων...")
        
        # Login και fetch
        if not monitor.logged_in:
            if not monitor.login():
                print("❌ Αποτυχία login")
                sys.exit(1)
        
        if not monitor.main_page_loaded:
            monitor.load_main_page()
        
        json_data = monitor.fetch_page()
        if not json_data:
            print("❌ Αποτυχία ανάκτησης δεδομένων")
            sys.exit(1)
        
        all_procedures = monitor.parse_table_data(json_data)
        active_procedures = [p for p in all_procedures if p.get('ενεργή') == 'ΝΑΙ']
        
        print(f"\n📊 Σύνολο διαδικασιών: {len(all_procedures)}")
        print(f"✅ Ενεργές διαδικασίες: {len(active_procedures)}")
        
        # Εμφάνιση ενεργών
        if args.list_active:
            print("\n" + "="*80)
            print("📋 ΕΝΕΡΓΕΣ ΔΙΑΔΙΚΑΣΙΕΣ".center(80))
            print("="*80)
            for i, proc in enumerate(active_procedures, 1):
                print(f"{i:3}. [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
            print("="*80)
        
        # Αποθήκευση baseline
        if args.save_baseline:
            save_baseline(active_procedures)
        
        # Σύγκριση με baseline
        if args.compare:
            baseline_data = load_baseline()
            if baseline_data:
                changes = compare_with_baseline(all_procedures, baseline_data)
                print_comparison_results(changes, baseline_data)
            else:
                print("\n⚠️  Δεν βρέθηκε baseline!")
                print("💡 Τρέξε πρώτα με --save-baseline για να δημιουργήσεις ένα.")
        
        # Έλεγχος εισερχόμενων αιτήσεων
        if args.check_incoming_portal:
            incoming_params = config.get('incoming_api_params', INCOMING_DEFAULT_PARAMS).copy()
            json_data_incoming = fetch_incoming_records(monitor, incoming_params)
            if not json_data_incoming or not json_data_incoming.get('success', False):
                print("\n⚠️  Αποτυχία λήψης εισερχόμενων αιτήσεων.")
            else:
                incoming_records = simplify_incoming_records(json_data_incoming.get('data', []))
                today_str = datetime.now().strftime("%Y-%m-%d")
                prev_snapshot_date, previous_snapshot = load_previous_incoming_snapshot(today_str)
                has_reference_snapshot = previous_snapshot is not None
                if has_reference_snapshot:
                    changes = compare_incoming_records(incoming_records, previous_snapshot)
                else:
                    changes = {'new': [], 'removed': [], 'modified': []}
                print_incoming_changes(changes, has_reference_snapshot, today_str, prev_snapshot_date)
                save_incoming_snapshot(today_str, incoming_records)
        
        # Αν --no-monitor, τερμάτισε
        if args.no_monitor or args.save_baseline or args.compare or args.list_active or args.check_incoming_portal:
            sys.exit(0)
    
    # Start monitoring
    try:
        # Φόρτωση baseline για σύγκριση κατά το monitoring
        baseline_data = load_baseline()
        if baseline_data:
            print(f"\n📊 Φορτώθηκε baseline με {baseline_data.get('count', 0)} ενεργές διαδικασίες")
        
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        sys.exit(0)

if __name__ == '__main__':
    main()