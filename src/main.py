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
    from fastapi.responses import JSONResponse
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
    """Δημιουργεί και επιστρέφει το FastAPI application (για χρήση με uvicorn)"""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI δεν είναι εγκατεστημένο")
    
    app = FastAPI(
        title="PKM Monitor API",
        version="1.0.0",
        description="API για πρόσβαση στα δεδομένα παρακολούθησης του PKM Portal"
    )
    
    # ==================== ΠΛΗΡΗΣ ΑΝΑΦΟΡΑ ====================
    
    @app.get("/sede/daily", tags=["Πλήρης Αναφορά"])
    async def get_sede_daily():
        """Επιστρέφει την πλήρη ημερήσια αναφορά ΣΗΔΕ σε JSON μορφή"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            return JSONResponse(content=report, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης αναφοράς ΣΗΔΕ"},
                status_code=500
            )
    
    # ==================== ΣΤΑΤΙΣΤΙΚΑ & ΣΥΝΟΨΗ ====================
    
    @app.get("/sede/summary", tags=["Στατιστικά"])
    async def get_summary():
        """Επιστρέφει σύνοψη με βασικά νούμερα"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            
            active_changes = report.get('active', {}).get('changes') or {}
            all_changes = report.get('all', {}).get('changes') or {}
            incoming = report.get('incoming', {})
            
            summary = {
                "generated_at": report.get('generated_at'),
                "totals": {
                    "active_procedures": report.get('active', {}).get('total', 0),
                    "all_procedures": report.get('all', {}).get('total', 0),
                    "incoming_total": incoming.get('stats', {}).get('total', 0),
                    "incoming_real": incoming.get('stats', {}).get('real', 0),
                    "incoming_test": incoming.get('stats', {}).get('test', 0)
                },
                "changes": {
                    "active_new": len(active_changes.get('new', [])),
                    "active_modified": len(active_changes.get('modified', [])),
                    "all_new": len(all_changes.get('new', [])),
                    "incoming_new_real": len(incoming.get('real_new', [])),
                    "incoming_new_test": len(incoming.get('test_new', [])),
                    "incoming_removed": len(incoming.get('changes', {}).get('removed', []))
                }
            }
            return JSONResponse(content=summary, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης σύνοψης"},
                status_code=500
            )
    
    @app.get("/sede/stats", tags=["Στατιστικά"])
    async def get_stats():
        """Επιστρέφει λεπτομερή στατιστικά"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            
            incoming = report.get('incoming', {})
            stats = incoming.get('stats', {})
            total = stats.get('total', 0)
            
            return JSONResponse(content={
                "generated_at": report.get('generated_at'),
                "procedures": {
                    "active": report.get('active', {}).get('total', 0),
                    "all": report.get('all', {}).get('total', 0),
                    "inactive": report.get('all', {}).get('total', 0) - report.get('active', {}).get('total', 0)
                },
                "incoming": {
                    "total": total,
                    "real": stats.get('real', 0),
                    "test": stats.get('test', 0),
                    "real_percentage": round(stats.get('real', 0) / total * 100, 1) if total > 0 else 0,
                    "test_percentage": round(stats.get('test', 0) / total * 100, 1) if total > 0 else 0,
                    "test_breakdown": stats.get('test_breakdown', {})
                },
                "baselines": {
                    "active": report.get('active', {}).get('baseline_timestamp'),
                    "all": report.get('all', {}).get('baseline_timestamp'),
                    "incoming": incoming.get('reference_date')
                }
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης στατιστικών"},
                status_code=500
            )
    
    # ==================== ΕΙΣΕΡΧΟΜΕΝΕΣ ΑΙΤΗΣΕΙΣ ====================
    
    @app.get("/sede/incoming", tags=["Εισερχόμενες Αιτήσεις"])
    async def get_incoming():
        """Επιστρέφει όλες τις εισερχόμενες αιτήσεις"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            incoming = report.get('incoming', {})
            
            return JSONResponse(content={
                "date": incoming.get('date'),
                "reference_date": incoming.get('reference_date'),
                "total": incoming.get('stats', {}).get('total', 0),
                "records": incoming.get('records', [])
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης εισερχόμενων"},
                status_code=500
            )
    
    @app.get("/sede/incoming/new", tags=["Εισερχόμενες Αιτήσεις"])
    async def get_incoming_new():
        """Επιστρέφει μόνο νέες αιτήσεις (real + test)"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            incoming = report.get('incoming', {})
            
            return JSONResponse(content={
                "date": incoming.get('date'),
                "real": incoming.get('real_new', []),
                "test": incoming.get('test_new', []),
                "total": len(incoming.get('real_new', [])) + len(incoming.get('test_new', []))
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης νέων αιτήσεων"},
                status_code=500
            )
    
    @app.get("/sede/incoming/real", tags=["Εισερχόμενες Αιτήσεις"])
    async def get_incoming_real():
        """Επιστρέφει μόνο πραγματικές αιτήσεις"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            incoming = report.get('incoming', {})
            
            # Φιλτράρισμα μόνο πραγματικών
            from test_users import classify_records
            all_records = incoming.get('records', [])
            real, _ = classify_records(all_records)
            
            return JSONResponse(content={
                "date": incoming.get('date'),
                "total": len(real),
                "records": real
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης πραγματικών αιτήσεων"},
                status_code=500
            )
    
    @app.get("/sede/incoming/test", tags=["Εισερχόμενες Αιτήσεις"])
    async def get_incoming_test():
        """Επιστρέφει μόνο δοκιμαστικές αιτήσεις"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            incoming = report.get('incoming', {})
            
            # Φιλτράρισμα μόνο δοκιμαστικών
            from test_users import classify_records
            all_records = incoming.get('records', [])
            _, test = classify_records(all_records)
            
            return JSONResponse(content={
                "date": incoming.get('date'),
                "total": len(test),
                "records": test
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης δοκιμαστικών αιτήσεων"},
                status_code=500
            )
    
    @app.get("/sede/incoming/changes", tags=["Εισερχόμενες Αιτήσεις"])
    async def get_incoming_changes():
        """Επιστρέφει μόνο αλλαγές εισερχόμενων"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            incoming = report.get('incoming', {})
            changes = incoming.get('changes', {})
            
            return JSONResponse(content={
                "date": incoming.get('date'),
                "reference_date": incoming.get('reference_date'),
                "new": changes.get('new', []),
                "removed": changes.get('removed', []),
                "modified": changes.get('modified', []),
                "totals": {
                    "new": len(changes.get('new', [])),
                    "removed": len(changes.get('removed', [])),
                    "modified": len(changes.get('modified', []))
                }
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης αλλαγών"},
                status_code=500
            )
    
    @app.get("/sede/incoming/{date}", tags=["Εισερχόμενες Αιτήσεις"])
    async def get_incoming_by_date(date: str):
        """Επιστρέφει snapshot συγκεκριμένης ημερομηνίας (YYYY-MM-DD)"""
        try:
            from incoming import load_incoming_snapshot
            from test_users import get_record_stats
            
            snapshot = load_incoming_snapshot(date)
            if not snapshot:
                return JSONResponse(
                    content={"error": f"Δεν βρέθηκε snapshot για {date}"},
                    status_code=404
                )
            
            records = snapshot.get('records', [])
            stats = get_record_stats(records)
            
            return JSONResponse(content={
                "date": date,
                "total": len(records),
                "stats": stats,
                "records": records
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": f"Αποτυχία ανάκτησης snapshot {date}"},
                status_code=500
            )
    
    # ==================== ΔΙΑΔΙΚΑΣΙΕΣ ====================
    
    @app.get("/sede/procedures/active", tags=["Διαδικασίες"])
    async def get_procedures_active():
        """Επιστρέφει μόνο ενεργές διαδικασίες"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            
            # Ανάκτηση ενεργών διαδικασιών από changes ή φιλτράρισμα
            return JSONResponse(content={
                "generated_at": report.get('generated_at'),
                "total": report.get('active', {}).get('total', 0),
                "baseline_timestamp": report.get('active', {}).get('baseline_timestamp'),
                "changes": report.get('active', {}).get('changes')
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης ενεργών διαδικασιών"},
                status_code=500
            )
    
    @app.get("/sede/procedures/all", tags=["Διαδικασίες"])
    async def get_procedures_all():
        """Επιστρέφει όλες τις διαδικασίες"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            
            return JSONResponse(content={
                "generated_at": report.get('generated_at'),
                "total": report.get('all', {}).get('total', 0),
                "baseline_timestamp": report.get('all', {}).get('baseline_timestamp'),
                "changes": report.get('all', {}).get('changes')
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης διαδικασιών"},
                status_code=500
            )
    
    @app.get("/sede/procedures/changes", tags=["Διαδικασίες"])
    async def get_procedures_changes():
        """Επιστρέφει αλλαγές διαδικασιών"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            
            active_changes = report.get('active', {}).get('changes') or {}
            all_changes = report.get('all', {}).get('changes') or {}
            
            return JSONResponse(content={
                "generated_at": report.get('generated_at'),
                "active": {
                    "new": active_changes.get('new', []),
                    "activated": active_changes.get('activated', []),
                    "deactivated": active_changes.get('deactivated', []),
                    "removed": active_changes.get('removed', []),
                    "modified": active_changes.get('modified', [])
                },
                "all": {
                    "new": all_changes.get('new', []),
                    "activated": all_changes.get('activated', []),
                    "deactivated": all_changes.get('deactivated', []),
                    "removed": all_changes.get('removed', []),
                    "modified": all_changes.get('modified', [])
                }
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης αλλαγών διαδικασιών"},
                status_code=500
            )
    
    @app.get("/sede/procedures/inactive", tags=["Διαδικασίες"])
    async def get_procedures_inactive():
        """Επιστρέφει μόνο ανενεργές διαδικασίες"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            
            active_total = report.get('active', {}).get('total', 0)
            all_total = report.get('all', {}).get('total', 0)
            inactive_count = all_total - active_total
            
            return JSONResponse(content={
                "generated_at": report.get('generated_at'),
                "total": inactive_count,
                "message": "Για λίστα ανενεργών, χρησιμοποίησε /sede/procedures/all και φίλτραρε ενεργή=ΟΧΙ"
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία υπολογισμού ανενεργών"},
                status_code=500
            )
    
    # ==================== ΑΝΑΖΗΤΗΣΗ & ΦΙΛΤΡΑ ====================
    
    @app.get("/sede/search", tags=["Αναζήτηση"])
    async def search(q: str):
        """Αναζήτηση σε διαδικασίες και αιτήσεις"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            
            query = q.lower()
            results = {
                "query": q,
                "incoming": [],
                "procedures": []
            }
            
            # Αναζήτηση σε εισερχόμενες
            incoming = report.get('incoming', {})
            for record in incoming.get('records', []):
                if (query in str(record.get('case_id', '')).lower() or
                    query in str(record.get('party', '')).lower() or
                    query in str(record.get('subject', '')).lower() or
                    query in str(record.get('procedure', '')).lower()):
                    results['incoming'].append(record)
            
            # Αναζήτηση σε διαδικασίες (από changes)
            all_changes = report.get('all', {}).get('changes') or {}
            for change_type in ['new', 'activated', 'deactivated', 'modified']:
                for item in all_changes.get(change_type, []):
                    proc = item.get('new', item) if isinstance(item, dict) and 'new' in item else item
                    if (query in str(proc.get('κωδικός', '')).lower() or
                        query in str(proc.get('τίτλος', '')).lower()):
                        if proc not in results['procedures']:
                            results['procedures'].append(proc)
            
            results['totals'] = {
                "incoming": len(results['incoming']),
                "procedures": len(results['procedures'])
            }
            
            return JSONResponse(content=results, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία αναζήτησης"},
                status_code=500
            )
    
    @app.get("/sede/incoming/filter", tags=["Αναζήτηση"])
    async def filter_incoming(
        party: str = None,
        procedure: str = None,
        date_from: str = None,
        date_to: str = None
    ):
        """Φιλτράρει εισερχόμενες αιτήσεις"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            
            records = report.get('incoming', {}).get('records', [])
            filtered = []
            
            for record in records:
                # Φίλτρο party
                if party and party.lower() not in str(record.get('party', '')).lower():
                    continue
                
                # Φίλτρο procedure
                if procedure and procedure.lower() not in str(record.get('procedure', '')).lower():
                    continue
                
                # Φίλτρο date range
                submitted = record.get('submitted_at', '')[:10]
                if date_from and submitted < date_from:
                    continue
                if date_to and submitted > date_to:
                    continue
                
                filtered.append(record)
            
            return JSONResponse(content={
                "filters": {
                    "party": party,
                    "procedure": procedure,
                    "date_from": date_from,
                    "date_to": date_to
                },
                "total": len(filtered),
                "records": filtered
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία φιλτραρίσματος"},
                status_code=500
            )
    
    # ==================== ΙΣΤΟΡΙΚΟ & TRENDS ====================
    
    @app.get("/sede/history/daily", tags=["Ιστορικό"])
    async def get_daily_history(days: int = 7):
        """Επιστρέφει ιστορικό τελευταίων n ημερών"""
        try:
            from datetime import datetime, timedelta
            from incoming import load_incoming_snapshot
            from test_users import get_record_stats
            
            history = []
            today = datetime.now()
            
            for i in range(days):
                date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                snapshot = load_incoming_snapshot(date)
                
                if snapshot:
                    records = snapshot.get('records', [])
                    stats = get_record_stats(records)
                    history.append({
                        "date": date,
                        "total": len(records),
                        "real": stats.get('real', 0),
                        "test": stats.get('test', 0)
                    })
            
            return JSONResponse(content={
                "days": days,
                "history": history
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης ιστορικού"},
                status_code=500
            )
    
    @app.get("/sede/comparison", tags=["Ιστορικό"])
    async def compare_dates(date1: str, date2: str):
        """Σύγκριση δύο ημερομηνιών"""
        try:
            from incoming import load_incoming_snapshot, compare_incoming_records
            from test_users import get_record_stats
            
            snap1 = load_incoming_snapshot(date1)
            snap2 = load_incoming_snapshot(date2)
            
            if not snap1:
                return JSONResponse(
                    content={"error": f"Δεν βρέθηκε snapshot για {date1}"},
                    status_code=404
                )
            if not snap2:
                return JSONResponse(
                    content={"error": f"Δεν βρέθηκε snapshot για {date2}"},
                    status_code=404
                )
            
            records1 = snap1.get('records', [])
            records2 = snap2.get('records', [])
            stats1 = get_record_stats(records1)
            stats2 = get_record_stats(records2)
            
            # Σύγκριση
            changes = compare_incoming_records(records2, snap1)
            
            return JSONResponse(content={
                "date1": date1,
                "date2": date2,
                "date1_stats": {
                    "total": len(records1),
                    "real": stats1.get('real', 0),
                    "test": stats1.get('test', 0)
                },
                "date2_stats": {
                    "total": len(records2),
                    "real": stats2.get('real', 0),
                    "test": stats2.get('test', 0)
                },
                "changes": changes,
                "diff": {
                    "total": len(records2) - len(records1),
                    "real": stats2.get('real', 0) - stats1.get('real', 0),
                    "test": stats2.get('test', 0) - stats1.get('test', 0)
                }
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία σύγκρισης"},
                status_code=500
            )
    
    @app.get("/sede/trends/weekly", tags=["Ιστορικό"])
    async def get_weekly_trends():
        """Επιστρέφει weekly trends"""
        try:
            from datetime import datetime, timedelta
            from incoming import load_incoming_snapshot
            from test_users import get_record_stats
            
            weeks = []
            today = datetime.now()
            
            for week in range(4):  # Τελευταίες 4 εβδομάδες
                week_data = {
                    "week": week + 1,
                    "days": []
                }
                
                for day in range(7):
                    date = (today - timedelta(days=(week * 7 + day))).strftime('%Y-%m-%d')
                    snapshot = load_incoming_snapshot(date)
                    
                    if snapshot:
                        records = snapshot.get('records', [])
                        stats = get_record_stats(records)
                        week_data["days"].append({
                            "date": date,
                            "total": len(records),
                            "real": stats.get('real', 0),
                            "test": stats.get('test', 0)
                        })
                
                if week_data["days"]:
                    week_data["totals"] = {
                        "total": sum(d['total'] for d in week_data["days"]),
                        "real": sum(d['real'] for d in week_data["days"]),
                        "test": sum(d['test'] for d in week_data["days"])
                    }
                    weeks.append(week_data)
            
            return JSONResponse(content={
                "weeks": weeks
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης trends"},
                status_code=500
            )
    
    # ==================== HEALTH & STATUS ====================
    
    @app.get("/health", tags=["Status"])
    async def health_check():
        """Health check του API"""
        try:
            from datetime import datetime
            from config import get_project_root
            import os
            
            # Έλεγχος baseline files
            root = get_project_root()
            baseline_active = os.path.join(root, 'data', 'active_procedures_baseline.json')
            baseline_all = os.path.join(root, 'data', 'all_procedures_baseline.json')
            
            return JSONResponse(content={
                "status": "healthy",
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "api_version": "1.0.0",
                "data_available": {
                    "active_baseline": os.path.exists(baseline_active),
                    "all_baseline": os.path.exists(baseline_all)
                }
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"status": "unhealthy", "error": str(e)},
                status_code=503
            )
    
    @app.get("/sede/baseline", tags=["Status"])
    async def get_baseline_info():
        """Επιστρέφει πληροφορίες baseline"""
        try:
            from sede_report import get_daily_sede_report
            report = get_daily_sede_report()
            
            return JSONResponse(content={
                "active_procedures": {
                    "timestamp": report.get('active', {}).get('baseline_timestamp'),
                    "count": report.get('active', {}).get('total', 0)
                },
                "all_procedures": {
                    "timestamp": report.get('all', {}).get('baseline_timestamp'),
                    "count": report.get('all', {}).get('total', 0)
                },
                "incoming": {
                    "current_date": report.get('incoming', {}).get('date'),
                    "reference_date": report.get('incoming', {}).get('reference_date')
                }
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης baseline info"},
                status_code=500
            )
    
    @app.get("/sede/last-update", tags=["Status"])
    async def get_last_update():
        """Επιστρέφει πότε ανανεώθηκαν τα δεδομένα"""
        try:
            from datetime import datetime
            from config import get_project_root
            import os
            
            root = get_project_root()
            incoming_today = os.path.join(root, 'data', 'incoming_requests', 
                                         f'incoming_{datetime.now().strftime("%Y-%m-%d")}.json')
            
            last_update = None
            if os.path.exists(incoming_today):
                last_update = datetime.fromtimestamp(
                    os.path.getmtime(incoming_today)
                ).strftime('%Y-%m-%d %H:%M:%S')
            
            return JSONResponse(content={
                "last_update": last_update,
                "current_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, status_code=200)
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία ανάκτησης last update"},
                status_code=500
            )
    
    # ==================== EXPORT ====================
    
    @app.get("/sede/export/csv", tags=["Export"])
    async def export_csv():
        """Επιστρέφει δεδομένα σε CSV format"""
        try:
            from sede_report import get_daily_sede_report
            import csv
            import io
            
            report = get_daily_sede_report()
            incoming = report.get('incoming', {})
            records = incoming.get('records', [])
            
            # Δημιουργία CSV
            output = io.StringIO()
            if records:
                fieldnames = list(records[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)
            
            from fastapi.responses import StreamingResponse
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=sede_incoming_{incoming.get('date')}.csv"}
            )
        except Exception as e:
            return JSONResponse(
                content={"error": str(e), "message": "Αποτυχία export CSV"},
                status_code=500
            )
    
    return app


# Δημιουργία app instance για χρήση με uvicorn
# Εκτέλεση: uvicorn src.main:app --host 0.0.0.0 --port 8000
if FASTAPI_AVAILABLE:
    app = create_fastapi_app()


def main():
    args = parse_arguments()
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
    
    config = load_config(os.path.join(get_project_root(), 'config', 'config.yaml'))
    monitor = PKMMonitor(
        base_url=config.get('base_url', 'https://shde.pkm.gov.gr'),
        urls=config.get('urls', {}), api_params=config.get('api_params', {}),
        login_params=config.get('login_params', {}), check_interval=config.get('check_interval', 300),
        username=config.get('username'), password=config.get('password'),
        session_cookies=config.get('session_cookies'))
    
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