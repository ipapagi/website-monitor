"""Διαχείριση εισερχόμενων αιτήσεων"""
import os
import json
from datetime import datetime
from config import get_incoming_snapshot_path, get_project_root, INCOMING_DEFAULT_PARAMS
from api import sanitize_party_name

def load_incoming_snapshot(date_str):
    """Φορτώνει snapshot για συγκεκριμένη ημερομηνία"""
    path = get_incoming_snapshot_path(date_str)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_incoming_snapshot(date_str, records):
    """Αποθηκεύει snapshot"""
    payload = {'date': date_str, 'count': len(records), 'records': records}
    with open(get_incoming_snapshot_path(date_str), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def list_incoming_snapshot_dates():
    """Επιστρέφει λίστα ημερομηνιών με snapshots"""
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
    """Φορτώνει το προηγούμενο snapshot"""
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    for snapshot_date in reversed(list_incoming_snapshot_dates()):
        if snapshot_date < current_date:
            snapshot_str = snapshot_date.strftime("%Y-%m-%d")
            return snapshot_str, load_incoming_snapshot(snapshot_str)
    return None, None

def fetch_incoming_records(monitor, incoming_params):
    """Ανακτά εισερχόμενες αιτήσεις με pagination αν χρειάζεται"""
    params = incoming_params.copy()
    original_params = monitor.api_params.copy()
    all_records = []
    
    try:
        # Πρώτο request
        monitor.api_params = params
        data = monitor.fetch_page()
        
        if not data or not data.get('success'):
            return None
        
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
            print(f"  📥 Ανακτήθηκαν {len(all_records)}/{total} εγγραφές...")
        
        return {'success': True, 'data': all_records, 'total': total}
    finally:
        monitor.api_params = original_params

def simplify_incoming_records(records):
    """Απλοποιεί τις εγγραφές από το API"""
    simplified = []
    for rec in records:
        case_id_raw = (rec.get('W007_P_FLD21') or rec.get('Αρ. εγγράφου') or
                      rec.get('αρ. εγγράφου') or rec.get('αρ_εγγράφου') or
                      rec.get('DOCID') or rec.get('docid') or rec.get('CASE_ID'))
        case_id = str(case_id_raw or '').strip()
        if not case_id:
            continue
        submitted_at = (rec.get('DATE_INSERTED_ISO') or rec.get('W003_DATA_INSERT') or
                       rec.get('DATE_INSERT') or rec.get('SUBMIT_DATE') or '')
        party_raw = (rec.get('W007_P_FLD13') or rec.get('party') or
                    rec.get('customer') or rec.get('applicant') or '')
        doc_id = str(rec.get('DOCID') or rec.get('docid') or '').strip()
        simplified.append({
            'case_id': case_id, 'submitted_at': submitted_at,
            'party': sanitize_party_name(party_raw), 'doc_id': doc_id,
            'protocol_number': '', 'procedure': '', 'directory': ''
        })
    return simplified

def compare_incoming_records(current, previous):
    """Συγκρίνει τρέχουσες με προηγούμενες εγγραφές"""
    previous_records = previous.get('records', []) if previous else []
    prev_dict = {r['case_id']: r for r in previous_records if r.get('case_id')}
    curr_dict = {r['case_id']: r for r in current if r.get('case_id')}
    new_docs = [r for cid, r in curr_dict.items() if cid not in prev_dict]
    removed_docs = [r for cid, r in prev_dict.items() if cid not in curr_dict]
    modified = [{'old': prev_dict[cid], 'new': record} 
                for cid, record in curr_dict.items() 
                if cid in prev_dict and record.get('submitted_at') != prev_dict[cid].get('submitted_at')]
    return {'new': new_docs, 'removed': removed_docs, 'modified': modified}

def merge_with_previous_snapshot(current_records, previous_snapshot):
    """Συγχωνεύει τρέχουσες εγγραφές με προηγούμενο snapshot για να μην χαθούν παλιές"""
    if not previous_snapshot:
        return current_records
    
    # Dict με τρέχουσες εγγραφές
    current_dict = {r['case_id']: r for r in current_records if r.get('case_id')}
    
    # Πρόσθεσε εγγραφές από το προηγούμενο snapshot που δεν υπάρχουν στις τρέχουσες
    # (παλαιότερες που έφυγαν από το API limit αλλά δεν έχουν διαγραφεί)
    prev_records = previous_snapshot.get('records', [])
    for prev_rec in prev_records:
        case_id = prev_rec.get('case_id')
        if case_id and case_id not in current_dict:
            # Κρατάμε την παλιά εγγραφή (δεν είναι "αφαιρεμένη", απλά δεν επιστράφηκε)
            current_dict[case_id] = prev_rec
    
    # Επιστροφή ως λίστα, ταξινομημένη με τις νεότερες πρώτα
    merged = list(current_dict.values())
    merged.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
    return merged
