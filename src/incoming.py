"""Διαχείριση εισερχόμενων αιτήσεων"""
import os
import json
import sys
from datetime import datetime
from config import get_incoming_snapshot_path, get_project_root, INCOMING_DEFAULT_PARAMS
from api import sanitize_party_name

# Enable imports from root for test_users
sys.path.insert(0, get_project_root())

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

def get_all_incoming_dates():
    """Επιστρέφει λίστα ημερομηνιών με snapshots ως strings (YYYY-MM-DD)"""
    dates = list_incoming_snapshot_dates()
    return [d.strftime("%Y-%m-%d") for d in dates]

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
    from api import sanitize_party_name
    from collections import Counter
    
    simplified = []
    case_id_counter = Counter()
    for rec in records:
        case_id_raw = (rec.get('W007_P_FLD21') or rec.get('Αρ. εγγράφου') or
                      rec.get('αρ. εγγράφου') or rec.get('αρ_εγγράφου') or
                      rec.get('DOCID') or rec.get('docid') or rec.get('CASE_ID'))
        case_id = str(case_id_raw or '').strip()
        if not case_id:
            continue
        
        # Καταμέτρηση όλων των case_id
        case_id_counter[case_id] += 1
        submitted_at = (rec.get('DATE_INSERTED_ISO') or rec.get('W003_DATA_INSERT') or
                       rec.get('DATE_INSERT') or rec.get('SUBMIT_DATE') or '')
        party_raw = (rec.get('W007_P_FLD13') or rec.get('party') or
                    rec.get('customer') or rec.get('applicant') or '')
        doc_id = str(rec.get('DOCID') or rec.get('docid') or '').strip()
        doc_category = rec.get('W007_P_FLD30', '')
        # Θέμα/Τίτλος της αίτησης - W007_P_FLD6 είναι το σωστό πεδίο
        subject_raw = rec.get('W007_P_FLD6') or ''
        # Αφαίρεση ΑΦΜ από το θέμα (όπως και από το party)
        subject = sanitize_party_name(subject_raw)
        # Έτος υποβολής - από W007_P_FLD2 (π.χ. "2026" ή "2026-02-17")
        submission_year_raw = str(rec.get('W007_P_FLD2', '')).strip()
        submission_year = submission_year_raw[:4] if submission_year_raw and submission_year_raw[0].isdigit() else ''
        
        # Διαδικασία - από API ή από enrichment
        procedure = rec.get('procedure', '') or rec.get('W007_P_FLD23', '') or ''
        # Διεύθυνση - από API ή από enrichment (αφαίρεση παρένθεσης με Γενική Δ/νση)
        directory_raw = rec.get('directory', '') or rec.get('W007_P_FLD17', '') or ''
        if '(' in directory_raw:
            directory = directory_raw.split('(', 1)[0].strip()
        else:
            directory = directory_raw
        # Γενική Διεύθυνση - από API ή από enrichment
        general_directorate = rec.get('general_directorate', '') or rec.get('W007_P_FLD16', '') or ''
        # Τμήμα (κρατάμε μόνο το τμήμα χωρίς Γενική Δ/νση και Δ/νση) - από API ή enrichment
        department_raw = rec.get('department', '') or rec.get('W007_P_FLD18', '') or ''
        if '(' in department_raw:
            department = department_raw.split('(', 1)[0].strip()
        else:
            department = department_raw
        # Αριθμός πρωτοκόλλου - από API ή enrichment
        protocol_number = rec.get('protocol_number', '') or rec.get('W007_P_FLD22', '') or ''
        # Ημερομηνία πρωτοκόλλου - από enrichment (δεν υπάρχει στο raw API)
        protocol_date = rec.get('protocol_date', '') or ''
        
        # Συσχέτιση με αρχική υπόθεση (για συμπληρωματικά αιτήματα) - W007_P_FLD7
        related_case = str(rec.get('W007_P_FLD7', '') or '').strip()
        
        simplified.append({
            'case_id': case_id, 'submitted_at': submitted_at,
            'party': sanitize_party_name(party_raw), 'doc_id': doc_id,
            'protocol_number': protocol_number, 'protocol_date': protocol_date,
            'procedure': procedure or '', 'directory': directory or '',
            'general_directorate': general_directorate or '', 'department': department or '',
            'document_category': doc_category, 'subject': subject,
            'submission_year': submission_year, 'related_case': related_case
        })
    
    # Εμφάνιση πληροφοριών για case_id με πολλαπλές εγγραφές
    duplicates = {cid: count for cid, count in case_id_counter.items() if count > 1}
    if duplicates:
        print(f"  ℹ️  Βρέθηκαν εγγραφές με διπλότυπα case_id:")
        for case_id, count in sorted(duplicates.items(), key=lambda x: (-x[1], x[0])):
            if case_id == '0':
                print(f"     • case_id='{case_id}': {count} εγγραφές (καταγγελίες - χρήση doc_id ως unique key)")
            else:
                print(f"     • case_id='{case_id}': {count} εγγραφές (κρατείται η τελευταία)")
    
    return simplified


def build_docid_caseid_maps(records):
    """Build maps between doc_id and case_id from simplified incoming records."""
    docid_to_case = {}
    case_to_docid = {}
    for rec in records or []:
        doc_id = str(rec.get('doc_id', '')).strip()
        case_id = str(rec.get('case_id', '')).strip()
        if doc_id:
            docid_to_case[doc_id] = case_id
        if case_id:
            case_to_docid[case_id] = doc_id
    return docid_to_case, case_to_docid


def get_docid_for_case_id(records, case_id: str) -> str | None:
    """Return doc_id for a given case_id from simplified incoming records."""
    _, case_to_docid = build_docid_caseid_maps(records)
    return case_to_docid.get(str(case_id).strip())


def get_case_id_for_docid(records, doc_id: str) -> str | None:
    """Return case_id for a given doc_id from simplified incoming records."""
    docid_to_case, _ = build_docid_caseid_maps(records)
    return docid_to_case.get(str(doc_id).strip())

def _get_unique_key(record):
    """Επιστρέφει μοναδικό key για την εγγραφή.
    Για case_id='0' (καταγγελίες) χρησιμοποιεί το doc_id, αλλιώς το case_id.
    """
    case_id = record.get('case_id', '')
    if case_id == '0':
        return f"docid_{record.get('doc_id', '')}"
    return f"case_{case_id}"

def compare_incoming_records(current, previous):
    """Συγκρίνει τρέχουσες με προηγούμενες εγγραφές"""
    previous_records = previous.get('records', []) if previous else []
    prev_dict = {_get_unique_key(r): r for r in previous_records if r.get('case_id') or r.get('doc_id')}
    curr_dict = {_get_unique_key(r): r for r in current if r.get('case_id') or r.get('doc_id')}
    new_docs = [r for key, r in curr_dict.items() if key not in prev_dict]
    removed_docs = [r for key, r in prev_dict.items() if key not in curr_dict]
    modified = [{'old': prev_dict[key], 'new': record} 
                for key, record in curr_dict.items() 
                if key in prev_dict and record.get('submitted_at') != prev_dict[key].get('submitted_at')]
    return {'new': new_docs, 'removed': removed_docs, 'modified': modified}

def merge_with_previous_snapshot(current_records, previous_snapshot):
    """Συγχωνεύει τρέχουσες εγγραφές με προηγούμενο snapshot για να μην χαθούν παλιές.
    
    Για case_id='0' (καταγγελίες), χρησιμοποιεί το doc_id ως unique key,
    ώστε να κρατούνται όλες οι καταγγελίες και όχι μόνο η τελευταία.
    """
    if not previous_snapshot:
        return current_records
    
    # Dict με τρέχουσες εγγραφές (χρήση composite key)
    current_dict = {_get_unique_key(r): r for r in current_records if r.get('case_id') or r.get('doc_id')}
    
    # Dict με προηγούμενες εγγραφές
    prev_records = previous_snapshot.get('records', [])
    prev_dict = {_get_unique_key(r): r for r in prev_records if r.get('case_id') or r.get('doc_id')}
    
    # Ενημέρωση: αν η τρέχουσα εγγραφή υπάρχει και στο προηγούμενο, κρατάμε τα πλήρη δεδομένα
    for key, curr_rec in current_dict.items():
        if key in prev_dict:
            prev_rec = prev_dict[key]
            # Συμπληρώνουμε κενά πεδία από το προηγούμενο
            for field in ['protocol_number', 'protocol_date', 'procedure', 'directory', 'general_directorate', 'department']:
                if not curr_rec.get(field) and prev_rec.get(field):
                    curr_rec[field] = prev_rec.get(field)
    
    # Πρόσθεσε εγγραφές από το προηγούμενο snapshot που δεν υπάρχουν στις τρέχουσες
    # (παλαιότερες που έφυγαν από το API limit αλλά δεν έχουν διαγραφεί)
    for key, prev_rec in prev_dict.items():
        if key not in current_dict:
            # Κρατάμε την παλιά εγγραφή (δεν είναι "αφαιρεμένη", απλά δεν επιστράφηκε)
            current_dict[key] = prev_rec
    
    # Επιστροφή ως λίστα, ταξινομημένη με τις νεότερες πρώτα
    merged = list(current_dict.values())
    merged.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
    return merged
