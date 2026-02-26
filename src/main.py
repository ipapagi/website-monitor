"""Entry point για PKM Website Monitor"""
import sys
import os
import argparse
from datetime import datetime

# Ορίσει UTF-8 κωδικοποίηση για Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor import PKMMonitor
from utils import load_config
from config import INCOMING_DEFAULT_PARAMS, get_project_root
from baseline import (save_baseline, load_baseline, compare_with_baseline,
                      save_all_procedures_baseline, load_all_procedures_baseline,
                      compare_all_procedures_with_baseline)
from procedures import update_procedures_cache_from_procedures
from incoming import (simplify_incoming_records, compare_incoming_records,
                      load_previous_incoming_snapshot, save_incoming_snapshot,
                      fetch_incoming_records, load_incoming_snapshot)
from api import enrich_record_details
from display import (print_comparison_results, print_all_procedures_comparison,
                     print_incoming_changes)

# FastAPI imports (προσθήκη)
try:
    from fastapi import FastAPI
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

def parse_arguments():
    parser = argparse.ArgumentParser(description='PKM Website Monitor')
    parser.add_argument('--save-baseline', action='store_true')
    parser.add_argument('--compare', action='store_true')
    parser.add_argument('--list-active', action='store_true')
    parser.add_argument('--save-all-baseline', action='store_true')
    parser.add_argument('--compare-all', action='store_true')
    parser.add_argument('--list-all', action='store_true')
    parser.add_argument('--no-monitor', action='store_true')
    parser.add_argument('--check-incoming-portal', action='store_true')
    parser.add_argument('--enrich-all', action='store_true')
    parser.add_argument('--compare-date', type=str, metavar='YYYY-MM-DD')
    parser.add_argument('--analyze-test', type=str, metavar='YYYY-MM-DD', 
                       help='Αναλύει τις αιτήσεις ενός snapshot για δοκιμαστικές/πραγματικές')
    parser.add_argument('--analyze-current', action='store_true',
                       help='Αναλύει τις τρέχουσες αιτήσεις για δοκιμαστικές/πραγματικές')
    parser.add_argument('--send-daily-email', action='store_true',
                       help='Στέλνει ημερήσιο email report (διαδικασίες + εισερχόμενα)')
    parser.add_argument('--full-text', action='store_true',
                        help='Απενεργοποιεί το truncation για την εκτύπωση στο terminal (μόνο για text view)')
    parser.add_argument('--export-incoming-xls', action='store_true',
                        help='Εξάγει Excel (.xlsx) με νέες δοκιμαστικές και πραγματικές αιτήσεις')
    parser.add_argument('--export-incoming-xls-all', action='store_true',
                        help='Εξάγει Excel (.xlsx) με ΟΛΕΣ τις αιτήσεις (δοκιμαστικές & πραγματικές) του snapshot')
    parser.add_argument('--report-open-apps', action='store_true',
                        help='Εμφανίζει στο terminal αναφορά ανοικτών δοκιμαστικών αιτήσεων (auto-close vs manual)')
    parser.add_argument('--export-open-apps-xls', action='store_true',
                        help='Εξάγει Excel (.xlsx) με ΑΝΟΙΚΤΕΣ δοκιμαστικές αιτήσεις (υποψήφιες για κλείσιμο)')
    parser.add_argument('--send-directory-emails', action='store_true',
                       help='Δημιουργεί και στέλνει emails ανά Διεύθυνση με attachments για νέες αιτήσεις')
    parser.add_argument('--send-directory-emails-to-chat', action='store_true',
                       help='Δημιουργεί, στέλνει emails ανά Διεύθυνση ΚΑΙ αποστέλνει σύνοψη στο chat group υποστήριξης')
    return parser.parse_args()

def needs_data_fetch(args):
    return (args.save_baseline or args.compare or args.list_active or
            args.check_incoming_portal or args.save_all_baseline or
            args.compare_all or args.list_all)

def handle_procedures(args, all_procedures, active_procedures):
    """Χειρίζεται τις εντολές για διαδικασίες"""
    print(f"\n📊 Σύνολο διαδικασιών: {len(all_procedures)}")
    print(f"✅ Ενεργές: {len(active_procedures)} | ❌ Ανενεργές: {len(all_procedures) - len(active_procedures)}")
    
    if args.list_active:
        print("\n" + "="*80 + "\n" + "📋 ΕΝΕΡΓΕΣ ΔΙΑΔΙΚΑΣΙΕΣ".center(80) + "\n" + "="*80)
        for i, p in enumerate(active_procedures, 1):
            print(f"{i:3}. [{p.get('κωδικός')}] {p.get('τίτλος', '')}")
        print("="*80)
    
    if args.list_all:
        print("\n" + "="*80 + "\n" + "📋 ΟΛΕΣ ΟΙ ΔΙΑΔΙΚΑΣΙΕΣ".center(80) + "\n" + "="*80)
        for i, p in enumerate(all_procedures, 1):
            s = "✅" if p.get('ενεργή') == 'ΝΑΙ' else "❌"
            print(f"{i:3}. {s} [{p.get('κωδικός')}] {p.get('τίτλος', '')}")
        print("="*80)
    
    if args.save_baseline:
        save_baseline(active_procedures)
    if args.save_all_baseline:
        save_all_procedures_baseline(all_procedures)
    if args.compare:
        bl = load_baseline()
        if bl:
            print_comparison_results(compare_with_baseline(all_procedures, bl), bl)
        else:
            print("\n⚠️  Δεν βρέθηκε baseline! Τρέξε --save-baseline πρώτα.")
    if args.compare_all:
        bl = load_all_procedures_baseline()
        if bl:
            print_all_procedures_comparison(compare_all_procedures_with_baseline(all_procedures, bl), bl)
        else:
            print("\n⚠️  Δεν βρέθηκε baseline! Τρέξε --save-all-baseline πρώτα.")

def handle_incoming(args, monitor, config):
    """Χειρίζεται τις εντολές για εισερχόμενες αιτήσεις"""
    from incoming import merge_with_previous_snapshot  # Προσθήκη import
    
    data = fetch_incoming_records(monitor, config.get('incoming_api_params', INCOMING_DEFAULT_PARAMS).copy())
    if not data or not data.get('success'):
        print("\n⚠️  Αποτυχία λήψης εισερχόμενων αιτήσεων.")
        return
    
    records = simplify_incoming_records(data.get('data', []))
    today = datetime.now().strftime("%Y-%m-%d")
    prev_date, prev_snap = load_previous_incoming_snapshot(today)
    has_prev = prev_snap is not None
    
    # Συγχώνευση με προηγούμενο snapshot για να μην χαθούν παλιές εγγραφές
    if has_prev:
        records = merge_with_previous_snapshot(records, prev_snap)
    
    if has_prev:
        prev_dict = {r['case_id']: r for r in prev_snap.get('records', []) if r.get('case_id')}
        for rec in records:
            if rec.get('case_id') in prev_dict:
                prev = prev_dict[rec['case_id']]
                for k in ['protocol_number', 'procedure', 'directory', 'document_category']:
                    if prev.get(k) and not rec.get(k):
                        rec[k] = prev[k]
        changes = compare_incoming_records(records, prev_snap)
    else:
        changes = {'new': [], 'removed': [], 'modified': []}
    
    to_enrich = ([r for r in records if not r.get('procedure') or not r.get('directory')] 
                 if args.enrich_all else (changes['new'] if has_prev else records))
    if to_enrich:
        if args.enrich_all:
            print(f"\n🔄 Εμπλουτισμός {len(to_enrich)} εγγραφών...")
        enrich_record_details(monitor, to_enrich)
    
    print_incoming_changes(changes, has_prev, today, prev_date)
    save_incoming_snapshot(today, records)

def handle_analyze_test(date_str):
    """Αναλύει τις αιτήσεις ενός snapshot για δοκιμαστικές/πραγματικές"""
    from test_users import classify_records, get_record_stats
    from display import print_test_analysis
    
    snap = load_incoming_snapshot(date_str)
    if not snap:
        print(f"❌ Δεν βρέθηκε snapshot για {date_str}")
        return False
    
    records = snap.get('records', [])
    print_test_analysis(records, date_str)
    return True


def create_fastapi_app():
    """Δημιουργεί και επιστρέφει το FastAPI application (για χρήση με uvicorn)."""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI δεν είναι εγκατεστημένο")

    # Καθυστερημένη import για να αποφευχθεί σύγκρουση με το υπάρχον api.py module
    from webapi import create_app

    return create_app()


# Δημιουργία app instance για χρήση με uvicorn
# Εκτέλεση: uvicorn src.main:app --host 0.0.0.0 --port 8000
if FASTAPI_AVAILABLE:
    app = create_fastapi_app()


def main():
    args = parse_arguments()
    # Runtime override for terminal formatting widths
    if args.full_text:
        os.environ['PKM_FULL_TEXT'] = '1'
    print("\n" + "="*80)
    print(f"🚀 PKM Website Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
    print("="*80)
    
    # Ανάλυση δοκιμαστικών για συγκεκριμένη ημερομηνία
    if args.analyze_test:
        handle_analyze_test(args.analyze_test)
        sys.exit(0)

    if args.send_daily_email:
        from daily_report import send_daily_email

        try:
            send_daily_email()
            print("✅ Ημερήσιο email εστάλη")
            sys.exit(0)
        except Exception as exc:
            print(f"❌ Αποτυχία αποστολής ημερήσιου email: {exc}")
            sys.exit(1)

    if args.send_directory_emails or args.send_directory_emails_to_chat:
        from directory_emails import send_directory_emails

        try:
            send_to_chat = args.send_directory_emails_to_chat
            send_directory_emails(send_to_chat=send_to_chat)
            print("✅ Emails ανά Διεύθυνση εστάλησαν")
            sys.exit(0)
        except Exception as exc:
            print(f"❌ Αποτυχία αποστολής emails ανά Διεύθυνση: {exc}")
            sys.exit(1)

    # Always create monitor first (needed for settled cases lookup)
    config = load_config(os.path.join(get_project_root(), 'config', 'config.yaml'))
    monitor = PKMMonitor(
        base_url=config.get('base_url', 'https://shde.pkm.gov.gr'),
        urls=config.get('urls', {}), api_params=config.get('api_params', {}),
        login_params=config.get('login_params', {}), check_interval=config.get('check_interval', 300),
        username=config.get('username'), password=config.get('password'),
        session_cookies=config.get('session_cookies'))

    if args.report_open_apps:
        try:
            from services.report_service import load_digest
            from xls_export import print_open_apps_terminal
            digest = load_digest()
            print_open_apps_terminal(digest, monitor_instance=monitor)
            sys.exit(0)
        except Exception as exc:
            import traceback; traceback.print_exc()
            print(f"❌ Αποτυχία αναφοράς ανοικτών δοκιμαστικών: {exc}")
            sys.exit(1)

    if args.export_open_apps_xls:
        try:
            from services.report_service import load_digest
            from xls_export import build_open_apps_xls
            
            digest = load_digest()
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(get_project_root(), 'data', 'outputs', f'Ανοικτές_δοκιμαστικές_{timestamp}.xlsx')
            
            print(f"📊 Δημιουργία Excel με ανοικτές δοκιμαστικές αιτήσεις...")
            build_open_apps_xls(digest, monitor_instance=monitor, file_path=output_path)
            print(f"✅ Δημιουργήθηκε: {output_path}")
            sys.exit(0)
        except Exception as exc:
            import traceback; traceback.print_exc()
            print(f"❌ Αποτυχία εξαγωγής Excel: {exc}")
            sys.exit(1)

    if args.export_incoming_xls or args.export_incoming_xls_all:
        # Δημιουργεί το XLS από το digest των νέων αιτήσεων
        try:
            from services.report_service import load_digest
            from xls_export import build_requests_xls
            digest = load_digest()
            date_str = (digest.get('incoming', {}) or {}).get('date') or datetime.now().strftime('%Y-%m-%d')
            out_dir = os.path.join(get_project_root(), 'data')
            os.makedirs(out_dir, exist_ok=True)
            scope = 'all' if args.export_incoming_xls_all else 'new'
            if scope == 'all':
                out_path = os.path.join(out_dir, "Διαδικασίες - εισερχόμενες αιτήσεις.xlsx")
            else:
                out_path = os.path.join(out_dir, f"incoming_{scope}_{date_str}.xlsx")
            build_requests_xls(digest, scope=scope, file_path=out_path, monitor_instance=monitor)
            print(f"✅ Δημιουργήθηκε XLS ({scope}): {out_path}")
            sys.exit(0)
        except Exception as exc:
            print(f"❌ Αποτυχία δημιουργίας XLS: {exc}")
            sys.exit(1)
    
    if args.compare_date:
        snap = load_incoming_snapshot(args.compare_date)
        if not snap:
            print(f"❌ Δεν βρέθηκε snapshot για {args.compare_date}")
            sys.exit(1)
        prev_date, prev = load_previous_incoming_snapshot(args.compare_date)
        if prev:
            print_incoming_changes(compare_incoming_records(snap.get('records', []), prev), True, args.compare_date, prev_date)
        else:
            print(f"ℹ️  Δεν βρέθηκε προηγούμενο snapshot. Εγγραφές: {snap.get('count', 0)}")
        sys.exit(0)
    
    if needs_data_fetch(args) or args.analyze_current:
        print("\n🔄 Ανάκτηση δεδομένων...")
        if not monitor.logged_in and not monitor.login():
            print("❌ Αποτυχία login")
            sys.exit(1)
        if not monitor.main_page_loaded:
            monitor.load_main_page()
        data = monitor.fetch_page()
        if not data:
            print("❌ Αποτυχία ανάκτησης")
            sys.exit(1)
        
        all_procs = monitor.parse_table_data(data)
        active = [p for p in all_procs if p.get('ενεργή') == 'ΝΑΙ']
        update_procedures_cache_from_procedures(all_procs)
        handle_procedures(args, all_procs, active)
        
        if args.check_incoming_portal or args.analyze_current:
            handle_incoming(args, monitor, config)
            
            # Ανάλυση δοκιμαστικών για τρέχουσες αιτήσεις
            if args.analyze_current:
                from test_users import classify_records
                from display import print_test_analysis
                today = datetime.now().strftime("%Y-%m-%d")
                snap = load_incoming_snapshot(today)
                if snap:
                    print_test_analysis(snap.get('records', []), today)
        
        sys.exit(0)
    
    try:
        bl = load_baseline()
        if bl:
            print(f"\n📊 Baseline: {bl.get('count', 0)} ενεργές διαδικασίες")
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nStopped by user")
        sys.exit(0)

if __name__ == '__main__':
    # Το πρόγραμμα τρέχει κανονικά με email + terminal
    # Για FastAPI, χρησιμοποίησε: uvicorn src.main:app --host 0.0.0.0 --port 8000
    main()