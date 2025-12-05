"""API calls για ανάκτηση δεδομένων"""
import re
from datetime import datetime
from procedures import load_procedures_cache, save_procedures_cache

def extract_field(payload, field_name):
    """Εξάγει πεδίο από API response"""
    if not isinstance(payload, dict):
        return None
    
    if field_name in payload:
        value = payload[field_name]
        if isinstance(value, dict) and 'value' in value:
            return str(value['value']).strip() if value['value'] not in (None, '') else None
        elif value not in (None, ''):
            return str(value).strip()
    
    data = payload.get('data')
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    
    if isinstance(data, dict) and field_name in data:
        value = data[field_name]
        if isinstance(value, dict) and 'value' in value:
            return str(value['value']).strip() if value['value'] not in (None, '') else None
        elif value not in (None, ''):
            return str(value).strip()
    
    record = payload.get('record')
    if isinstance(record, dict) and field_name in record:
        value = record[field_name]
        if isinstance(value, dict) and 'value' in value:
            return str(value['value']).strip() if value['value'] not in (None, '') else None
        elif value not in (None, ''):
            return str(value).strip()
    
    return None

def fetch_record_details(monitor, doc_id):
    """Ανακτά λεπτομέρειες εγγραφής"""
    if not doc_id:
        return None, None, None, None, None
    
    session = getattr(monitor, 'session', None)
    base_url = getattr(monitor, 'base_url', '')
    jwt_token = getattr(monitor, 'jwt_token', None)
    main_page_url = getattr(monitor, 'main_page_url', '')
    
    if not session or not base_url:
        return None, None, None, None, None
    
    url = base_url.rstrip('/') + f"/services/DataServices/fetchDataTableRecord/7/{doc_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Accept': '*/*',
        'Accept-Language': 'el',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': main_page_url or base_url,
    }
    if jwt_token:
        headers['Authorization'] = f'Bearer {jwt_token}'
    
    try:
        response = session.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        print(f"⚠️  Αποτυχία ανάκτησης στοιχείων για DOCID {doc_id}: {exc}")
        return None, None, None, None, None
    
    if not payload.get('success', False):
        return None, None, None, None, None
    
    return (extract_field(payload, 'W007_P_FLD61'),      # protocol
            extract_field(payload, 'W007_P_FLD23'),      # procedure
            extract_field(payload, 'W007_P_FLD17'),      # directory
            extract_field(payload, 'W003_P_FLD75'),      # procedure_id
            extract_field(payload, 'W007_P_FLD30'))      # document_category

def enrich_record_details(monitor, records, procedures_cache=None):
    """Εμπλουτίζει τις εγγραφές με πρωτόκολλο, διαδικασία και διεύθυνση"""
    if procedures_cache is None:
        procedures_cache = load_procedures_cache()
    
    cache_updated = False
    for rec in records or []:
        if not rec or not rec.get('doc_id'):
            continue
        if rec.get('protocol_number') and rec.get('procedure') and rec.get('directory') and rec.get('document_category'):
            continue
        
        protocol, procedure, directory, procedure_id, doc_category = fetch_record_details(monitor, rec.get('doc_id'))
        
        if protocol and not rec.get('protocol_number'):
            rec['protocol_number'] = protocol
        if doc_category and not rec.get('document_category'):
            rec['document_category'] = doc_category
        if procedure and not rec.get('procedure'):
            rec['procedure'] = procedure
            if procedure not in procedures_cache:
                procedures_cache[procedure] = {
                    'title': procedure, 'procedure_id': procedure_id or '',
                    'first_seen': datetime.now().isoformat()
                }
                cache_updated = True
            elif procedure_id and not procedures_cache[procedure].get('procedure_id'):
                procedures_cache[procedure]['procedure_id'] = procedure_id
                cache_updated = True
        if directory and not rec.get('directory'):
            rec['directory'] = directory
            if procedure and procedure in procedures_cache:
                if 'directories' not in procedures_cache[procedure]:
                    procedures_cache[procedure]['directories'] = []
                if directory not in procedures_cache[procedure]['directories']:
                    procedures_cache[procedure]['directories'].append(directory)
                    cache_updated = True
    
    if cache_updated:
        save_procedures_cache(procedures_cache)
    return procedures_cache

def sanitize_party_name(raw_party):
    """Καθαρίζει το όνομα συναλλασσόμενου"""
    if not raw_party:
        return ''
    text = str(raw_party)
    text = re.sub(r'\s*[-–]?\s*\(?\b\d{9}\b\)?', '', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()
