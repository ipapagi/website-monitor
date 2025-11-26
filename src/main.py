import sys
import os

# Προσθήκη του src directory στο path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor import PKMMonitor
from utils import load_config
import argparse
import json
from datetime import datetime

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
        for proc in changes['new']:
            print(f"  ✅ [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
    
    if changes['activated']:
        has_changes = True
        print(f"\n🔓 ΕΝΕΡΓΟΠΟΙΗΘΗΚΑΝ ({len(changes['activated'])})")
        print("─" * 80)
        for item in changes['activated']:
            proc = item['new']
            print(f"  ✅ [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
            print(f"     └─ Ενεργή: ΟΧΙ → ΝΑΙ")
    
    if changes['deactivated']:
        has_changes = True
        print(f"\n🔒 ΑΠΕΝΕΡΓΟΠΟΙΗΘΗΚΑΝ ({len(changes['deactivated'])})")
        print("─" * 80)
        for item in changes['deactivated']:
            proc = item['new']
            print(f"  ❌ [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
            print(f"     └─ Ενεργή: ΝΑΙ → ΟΧΙ")
    
    if changes['removed']:
        has_changes = True
        print(f"\n🗑️  ΑΦΑΙΡΕΘΗΚΑΝ ({len(changes['removed'])})")
        print("─" * 80)
        for proc in changes['removed']:
            print(f"  ⚠️  [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
    
    if changes['modified']:
        has_changes = True
        print(f"\n🔄 ΤΡΟΠΟΠΟΙΗΘΗΚΑΝ ({len(changes['modified'])})")
        print("─" * 80)
        for mod in changes['modified']:
            print(f"  📝 [{mod['new'].get('κωδικός')}] {mod['new'].get('τίτλος', '')}")
            # Εμφάνιση τι άλλαξε
            field_changes = mod.get('field_changes', {})
            for field, vals in field_changes.items():
                if field not in ['docid', '_raw']:  # Αγνόησε τα τεχνικά πεδία
                    old_val = vals['old'] if vals['old'] else '(κενό)'
                    new_val = vals['new'] if vals['new'] else '(κενό)'
                    # Περιόρισε μεγάλες τιμές
                    if len(str(old_val)) > 50:
                        old_val = str(old_val)[:50] + '...'
                    if len(str(new_val)) > 50:
                        new_val = str(new_val)[:50] + '...'
                    print(f"     └─ {field}: {old_val} → {new_val}")
    
    if not has_changes:
        print("\n✅ Καμία αλλαγή από το baseline!")
    
    print("\n" + "="*80)

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
    
    args = parser.parse_args()
    
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
    if args.save_baseline or args.compare or args.list_active:
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
        
        # Αν --no-monitor, τερμάτισε
        if args.no_monitor or args.save_baseline or args.compare or args.list_active:
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