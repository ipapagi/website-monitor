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

def _remove_parentheses(text: str | None) -> str | None:
    """Αφαιρεί παρένθεση και το περιεχόμενό της από string.
    
    Used for cleaning directory/department names that contain organizational paths.
    Example: 'ΔΙΕΥΘΥΝΣΗ ΚΤΗΝΙΑΤΡΙΚΗΣ (ΓΕΝΙΚΗ ΔΙΕΥΘΥΝΣΗ)' → 'ΔΙΕΥΘΥΝΣΗ ΚΤΗΝΙΑΤΡΙΚΗΣ'
    """
    if not text:
        return None
    text_str = str(text).strip()
    if not text_str:
        return None
    # Remove parentheses and content
    if '(' in text_str:
        text_str = text_str.split('(', 1)[0].strip()
    return text_str or None

def _extract_department_name(raw_department: str | None) -> tuple[str | None, str | None]:
    """Εξάγει τμήμα και γενική διεύθυνση από το W007_P_FLD18 field.
    
    Returns:
        tuple[department, general_directorate_from_parentheses]
        
    Format: 'ΤΜΗΜΑ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ (ΓΕΝΙΚΗ ΔΙΕΥΘΥΝΣΗ\\ΔΙΕΥΘΥΝΣΗ)'
    Extracts:
        - department: 'ΤΜΗΜΑ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ' (text before parenthesis)
        - general_directorate: 'ΓΕΝΙΚΗ ΔΙΕΥΘΥΝΣΗ' (first part in parenthesis path)
    """
    if not raw_department:
        return None, None
    text = str(raw_department).strip()
    if not text:
        return None, None
    
    department = text
    general_directorate_fallback = None
    
    # Εξαγωγή από παρένθεση
    if '(' in text:
        parts = text.split('(', 1)
        department = parts[0].strip()
        
        # Εξαγωγή Γενικής Διεύθυνσης από την παρένθεση
        if len(parts) > 1:
            in_paren = parts[1].rsplit(')', 1)[0].strip() if ')' in parts[1] else parts[1].strip()
            # Format: 'ΓΕΝΙΚΗ ΔΙΕΥΘΥΝΣΗ\\ΔΙΕΥΘΥΝΣΗ\\ΤΜΗΜΑ'
            if '\\' in in_paren:
                path_parts = [p.strip() for p in in_paren.split('\\')]
                if path_parts and path_parts[0]:
                    general_directorate_fallback = path_parts[0]
    
    return (department or None, general_directorate_fallback)

def fetch_record_details(monitor, doc_id):
    """Ανακτά λεπτομέρειες εγγραφής"""
    if not doc_id:
        return None, None, None, None, None, None, None, None
    
    session = getattr(monitor, 'session', None)
    base_url = getattr(monitor, 'base_url', '')
    jwt_token = getattr(monitor, 'jwt_token', None)
    main_page_url = getattr(monitor, 'main_page_url', '')
    
    if not session or not base_url:
        return None, None, None, None, None, None, None, None
    
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
        return None, None, None, None, None, None, None, None
    
    if not payload.get('success', False):
        print(f"⚠️  API returned success=false for DOCID {doc_id}")
        return None, None, None, None, None, None, None, None

    # Extract department and general_directorate from W007_P_FLD18
    department, gd_from_dept = _extract_department_name(extract_field(payload, 'W007_P_FLD18'))
    general_directorate = extract_field(payload, 'W007_P_FLD16') or gd_from_dept
    # Extract directory and remove parentheses
    directory = _remove_parentheses(extract_field(payload, 'W007_P_FLD17'))
    
    return (extract_field(payload, 'W007_P_FLD61'),      # protocol_number
            extract_field(payload, 'W007_P_FLD3'),       # protocol_date (DD-MM-YYYY)
            extract_field(payload, 'W007_P_FLD23'),      # procedure
            directory,                                   # directory (W007_P_FLD17 without parentheses)
            extract_field(payload, 'W003_P_FLD75'),      # procedure_id
            extract_field(payload, 'W007_P_FLD30'),      # document_category
            general_directorate,                         # general_directorate (W007_P_FLD16 or from parentheses)
            department)                                  # department (W007_P_FLD18 without parentheses)

def enrich_record_details(monitor, records, procedures_cache=None):
    """Εμπλουτίζει τις εγγραφές με πρωτόκολλο, διαδικασία, διεύθυνση και οργανωτική μονάδα"""
    if procedures_cache is None:
        procedures_cache = load_procedures_cache()
    
    cache_updated = False
    for rec in records or []:
        if not rec or not rec.get('doc_id'):
            continue
        # Ελέγχουμε τα κρίσιμα πεδία (χωρίς protocol_date που είναι προαιρετικό)
        if (rec.get('protocol_number') and rec.get('procedure') and rec.get('directory')
            and rec.get('document_category') and rec.get('general_directorate') and rec.get('department')):
            continue
        
        result = fetch_record_details(monitor, rec.get('doc_id'))
        if result is None or result[0] is None:  # Αν η ανάκτηση απέτυχε
            continue
         
        protocol, protocol_date, procedure, directory, procedure_id, doc_category, general_directorate, department = result
        
        if protocol and not rec.get('protocol_number'):
            rec['protocol_number'] = protocol
        if protocol_date and not rec.get('protocol_date'):
            rec['protocol_date'] = protocol_date
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
        if general_directorate and not rec.get('general_directorate'):
            rec['general_directorate'] = general_directorate
        if department and not rec.get('department'):
            rec['department'] = department
    
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
