"""Διαχείριση διεκπεραιωμένων υποθέσεων"""
import os
import json
from datetime import datetime
from config import get_project_root, SETTLED_CASES_DEFAULT_PARAMS
from api import sanitize_party_name

def get_settled_cases_snapshot_path(date_str):
    """Path για settled cases snapshot συγκεκριμένης ημερομηνίας"""
    settled_dir = os.path.join(get_project_root(), 'data', 'settled_cases')
    os.makedirs(settled_dir, exist_ok=True)
    return os.path.join(settled_dir, f'settled_{date_str}.json')

def load_settled_cases_snapshot(date_str):
    """Φορτώνει snapshot διεκπεραιωμένων υποθέσεων"""
    path = get_settled_cases_snapshot_path(date_str)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_settled_cases_snapshot(date_str, records):
    """Αποθηκεύει snapshot διεκπεραιωμένων υποθέσεων"""
    payload = {'date': date_str, 'count': len(records), 'records': records}
    path = get_settled_cases_snapshot_path(date_str)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path

def list_settled_cases_snapshot_dates():
    """Επιστρέφει λίστα ημερομηνιών με settled cases snapshots"""
    settled_dir = os.path.join(get_project_root(), 'data', 'settled_cases')
    if not os.path.exists(settled_dir):
        return []
    dates = []
    for filename in os.listdir(settled_dir):
        if filename.startswith('settled_') and filename.endswith('.json'):
            date_part = filename[len('settled_'):-5]
            try:
                dates.append(datetime.strptime(date_part, "%Y-%m-%d").date())
            except ValueError:
                continue
    return sorted(dates)

def fetch_settled_cases(monitor, settled_params=None):
    """Ανακτά διεκπεραιωμένες υποθέσεις με pagination αν χρειάζεται
    
    Args:
        monitor: PKMMonitor instance με ενεργή session
        settled_params: Custom parameters (χρησιμοποιεί defaults αν όχι)
    
    Returns:
        dict: {'success': bool, 'data': [...], 'total': int}
    """
    if settled_params is None:
        settled_params = SETTLED_CASES_DEFAULT_PARAMS.copy()
    else:
        settled_params = settled_params.copy()
    
    params = settled_params.copy()
    original_params = monitor.api_params.copy()
    all_records = []
    
    try:
        # Πρώτο request
        monitor.api_params = params
        data = monitor.fetch_page()
        
        if not data or not data.get('success'):
            print("  ❌ Αποτυχία ανάκτησης διεκπεραιωμένων υποθέσεων")
            return {'success': False, 'data': [], 'total': 0}
        
        all_records.extend(data.get('data', []))
        total = data.get('total', len(all_records))
        
        # Pagination αν υπάρχουν περισσότερες εγγραφές
        limit = params.get('limit', 200)
        while len(all_records) < total:
            params['start'] = len(all_records)
            monitor.api_params = params
            data = monitor.fetch_page()
            if not data or not data.get('success'):
                break
            new_records = data.get('data', [])
            if not new_records:
                break
            all_records.extend(new_records)
            print(f"  📋 Ανακτήθηκαν {len(all_records)}/{total} διεκπεραιωμένες υποθέσεις...")
        
        print(f"  ✅ Ολοκληρώθηκε: {len(all_records)} εγγραφές")
        return {'success': True, 'data': all_records, 'total': total}
    except Exception as e:
        print(f"  ❌ Σφάλμα κατά την ανάκτηση: {e}")
        return {'success': False, 'data': [], 'total': 0}
    finally:
        monitor.api_params = original_params

def simplify_settled_records(records):
    """Απλοποιεί τις εγγραφές διεκπεραιωμένων υποθέσεων
    
    Mapping πεδίων (W001 - Διεκπεραιωμένες Υποθέσεις):
    - W001_P_FLD2: Κωδ. Υπόθεσης
    - W001_P_FLD3: Ημ/νία Καταχ.
    - W001_P_FLD4: Χρήστης Καταχ.
    - W001_P_FLD5: Τμήμα Καταχ.
    - W001_P_FLD6: Ημ/νία Υποβολής
    - W001_P_FLD7: Ημ/νία Έναρξης
    - W001_P_FLD8: Ημ/νία Διεκπεραίωσης
    - W001_P_FLD9: Κατάσταση
    - W001_P_FLD11: Θέμα
    - W001_P_FLD13: Διαδικασία
    - W001_P_FLD21: Συναλλασσόμενος
    - W001_P_FLD29: Portal
    """
    simplified = []
    for rec in records:
        # Κωδικός υπόθεσης (case_code)
        case_code = str(rec.get('W001_P_FLD2', '')).strip()
        if not case_code:
            continue
        
        # Ημερομηνία διεκπεραίωσης
        completion_date = rec.get('W001_P_FLD8', '')
        
        # Ημερομηνία υποβολής
        submission_date = rec.get('W001_P_FLD6', '')
        
        # Πεδία που μας ενδιαφέρουν
        simplified.append({
            'case_code': case_code,
            'registration_date': rec.get('W001_P_FLD3', ''),
            'submission_date': submission_date,
            'start_date': rec.get('W001_P_FLD7', ''),
            'completion_date': completion_date,
            'status': rec.get('W001_P_FLD9', ''),
            'subject': sanitize_party_name(rec.get('W001_P_FLD11', '')),
            'procedure': rec.get('W001_P_FLD13', ''),
            'party_name': sanitize_party_name(rec.get('W001_P_FLD21', '')),
            'portal': rec.get('W001_P_FLD29', ''),
            'department': rec.get('W001_P_FLD5', ''),
            'days_to_complete': _calculate_days_to_settle(submission_date, completion_date),
        })
    
    return simplified

def _calculate_days_to_settle(submission_date, settled_date):
    """Υπολογίζει τις ημέρες που χρειάστηκαν για την ολοκλήρωση"""
    if not submission_date or not settled_date:
        return None
    
    try:
        # Απλή εξαγωγή της ημερομηνίας (χωρίς ώρα)
        submit = datetime.strptime(str(submission_date)[:10], '%Y-%m-%d').date()
        settled = datetime.strptime(str(settled_date)[:10], '%Y-%m-%d').date()
        delta = (settled - submit).days
        return delta if delta >= 0 else None
    except:
        return None

def get_settled_cases_for_date(monitor, target_date):
    """Ανακτά διεκπεραιωμένες υποθέσεις που ολοκληρώθηκαν σε συγκεκριμένη ημερομηνία
    
    Args:
        monitor: PKMMonitor instance
        target_date: Ημέρα ως string (YYYY-MM-DD)
    
    Returns:
        dict: {'date': str, 'total': int, 'records': [...], 'fetched_at': str}
    """
    result = fetch_settled_cases(monitor, SETTLED_CASES_DEFAULT_PARAMS)
    
    if not result.get('success'):
        return {'date': target_date, 'total': 0, 'records': [], 'fetched_at': datetime.now().isoformat(), 'error': 'Failed to fetch'}
    
    records = simplify_settled_records(result.get('data', []))
    
    # Φίλτρο: Μόνο εγγραφές που ολοκληρώθηκαν την συγκεκριμένη ημερομηνία
    today_settled = [r for r in records if r.get('settled_date', '').startswith(target_date)]
    
    return {
        'date': target_date,
        'total': len(today_settled),
        'records': today_settled,
        'fetched_at': datetime.now().isoformat()
    }

def compare_settled_snapshots(date1, date2):
    """Συγκρίνει δύο snapshots διεκπεραιωμένων υποθέσεων
    
    Returns: {'new': [...], 'removed': [...], 'count_diff': int}
    """
    snapshot1 = load_settled_cases_snapshot(date1)
    snapshot2 = load_settled_cases_snapshot(date2)
    
    if not snapshot1 or not snapshot2:
        return None
    
    records1 = {r.get('case_id'): r for r in snapshot1.get('records', [])}
    records2 = {r.get('case_id'): r for r in snapshot2.get('records', [])}
    
    new_cases = [records2[cid] for cid in set(records2.keys()) - set(records1.keys())]
    removed_cases = [records1[cid] for cid in set(records1.keys()) - set(records2.keys())]
    
    return {
        'date1': date1,
        'date2': date2,
        'new': new_cases,
        'removed': removed_cases,
        'count_diff': len(records2) - len(records1),
    }

def get_settlement_statistics(records):
    """Υπολογίζει στατιστικά για τις διεκπεραιωμένες υποθέσεις
    
    Returns: dict με min, max, avg days to settle, κλπ
    """
    if not records:
        return {'total': 0, 'avg_days': None, 'min_days': None, 'max_days': None}
    
    days_list = [r.get('days_to_settle') for r in records if r.get('days_to_settle') is not None]
    
    if not days_list:
        return {'total': len(records), 'avg_days': None, 'min_days': None, 'max_days': None}
    
    return {
        'total': len(records),
        'avg_days': sum(days_list) / len(days_list),
        'min_days': min(days_list),
        'max_days': max(days_list),
        'median_days': sorted(days_list)[len(days_list)//2] if days_list else None,
    }


def correlate_incoming_with_settled(incoming_records, settled_records):
    """
    Συσχετίζει εισερχόμενες αιτήσεις με διεκπεραιωμένες υποθέσεις.
    
    Η συσχέτιση γίνεται μέσω του πεδίου "Αφορά Υπόθεση" (W007_P_FLD7) στις εισερχόμενες,
    το οποίο περιέχει τον κωδικό υπόθεσης (W001_P_FLD2) από τις διεκπεραιωμένες.
    
    Args:
        incoming_records: Λίστα εισερχόμενων (raw ή simplified)
        settled_records: Λίστα διεκπεραιωμένων (raw ή simplified)
    
    Returns:
        dict: {
            'correlated': [
                {
                    'incoming': {...},
                    'settled': {...},
                    'case_code': '2026/105673'
                }
            ],
            'incoming_without_settled': [...],
            'settled_without_incoming': [...],
            'stats': {
                'total_incoming': int,
                'total_settled': int,
                'matched': int,
                'match_rate': float
            }
        }
    """
    # Ανίχνευση αν είναι simplified ή raw records
    is_settled_simplified = settled_records and 'case_code' in settled_records[0] if settled_records else False
    
    # Δημιουργία mapping: case_code -> settled record
    settled_by_code = {}
    for rec in settled_records:
        if is_settled_simplified:
            case_code = rec.get('case_code', '')
        else:
            case_code = rec.get('W001_P_FLD2', '')
        
        if case_code:
            settled_by_code[case_code.strip().upper()] = rec
    
    # Συσχέτιση
    correlated = []
    incoming_without_settled = []
    
    for inc_rec in incoming_records:
        # Εξαγωγή του πεδίου "Αφορά Υπόθεση"
        case_ref = inc_rec.get('W007_P_FLD7', '')
        
        if not case_ref:
            incoming_without_settled.append(inc_rec)
            continue
        
        # Εξαγωγή κωδικού υπόθεσης από το "Αφορά Υπόθεση"
        # Format: "Αίτημα 2026/105673 ΜΟΥΡΑΤΙΔΟΥ-128272645"
        case_code = _extract_case_code_from_reference(case_ref)
        
        if case_code and case_code in settled_by_code:
            correlated.append({
                'incoming': inc_rec,
                'settled': settled_by_code[case_code],
                'case_code': case_code
            })
        else:
            incoming_without_settled.append(inc_rec)
    
    # Βρες διεκπεραιωμένες που δεν έχουν εισερχόμενες
    matched_case_codes = {item['case_code'] for item in correlated}
    settled_without_incoming = [
        rec for code, rec in settled_by_code.items()
        if code not in matched_case_codes
    ]
    
    # Στατιστικά
    stats = {
        'total_incoming': len(incoming_records),
        'total_settled': len(settled_records),
        'matched': len(correlated),
        'match_rate': len(correlated) / len(incoming_records) if incoming_records else 0
    }
    
    return {
        'correlated': correlated,
        'incoming_without_settled': incoming_without_settled,
        'settled_without_incoming': settled_without_incoming,
        'stats': stats
    }


def _extract_case_code_from_reference(case_ref):
    """
    Εξάγει τον κωδικό υπόθεσης από το πεδίο "Αφορά Υπόθεση".
    
    Παραδείγματα:
    - "Αίτημα 2026/105673 ΜΟΥΡΑΤΙΔΟΥ-128272645" -> "2026/105673"
    - "2026/105673" -> "2026/105673"
    """
    import re
    if not case_ref:
        return None
    
    # Pattern: YYYY/NNNNNN
    match = re.search(r'(\d{4}/\d+)', str(case_ref))
    if match:
        return match.group(1).strip().upper()
    
    return None


def filter_out_settled_from_incoming(incoming_records, settled_records):
    """
    Αφαιρεί από τις εισερχόμενες αιτήσεις αυτές που έχουν ήδη διεκπεραιωθεί.
    
    Args:
        incoming_records: Λίστα εισερχόμενων
        settled_records: Λίστα διεκπεραιωμένων
    
    Returns:
        list: Εισερχόμενες που δεν έχουν διεκπεραιωθεί
    """
    correlation = correlate_incoming_with_settled(incoming_records, settled_records)
    return correlation['incoming_without_settled']


def get_settled_for_incoming(incoming_record, settled_records):
    """
    Βρίσκει τη διεκπεραιωμένη υπόθεση που αντιστοιχεί σε μια εισερχόμενη αίτηση.
    
    Args:
        incoming_record: Μια εισερχόμενη αίτηση
        settled_records: Λίστα διεκπεραιωμένων
    
    Returns:
        dict ή None: Η διεκπεραιωμένη υπόθεση αν βρεθεί
    """
    # Εξαγωγή case reference
    case_ref = incoming_record.get('W007_P_FLD7', '')
    if not case_ref:
        return None
    
    case_code = _extract_case_code_from_reference(case_ref)
    if not case_code:
        return None
    
    # Αναζήτηση στις διεκπεραιωμένες
    is_simplified = settled_records and 'case_code' in settled_records[0] if settled_records else False
    
    for rec in settled_records:
        if is_simplified:
            rec_code = rec.get('case_code', '')
        else:
            rec_code = rec.get('W001_P_FLD2', '')
        
        if rec_code and rec_code.strip().upper() == case_code:
            return rec
    
    return None
