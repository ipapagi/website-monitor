"""
Εισερχόμενα από Πρωτόκολλο (OTS) - Ανάκτηση και συσχέτιση ανάθεσης υπαλλήλων

Παρέχει λειτουργικότητα για:
- Ανάκτηση OTS εισερχομένων από queryId=2 (W001_P_FLD10 = Employee)
- Συσχέτιση OTS με εκκρεμείς αιτήσεις (matching via PKM)
- Προσθήκη πληροφοριών ανάθεσης υπαλλήλου στα records
"""
import html
import re
from api import extract_field
from typing import Dict, List, Optional, Tuple


# Παράμετροι για ανάκτηση OTS (Εισερχόμενα από Πρωτόκολλο) (queryId=2)
# Επιστρέφει εγγραφές με W001_P_FLD10 = όνομα υπαλλήλου που χρεώθηκε
CHARGES_PARAMS = {
    'queryId': '2',  # Εισερχόμενα από Πρωτόκολλο (OTS)
    'queryOwner': '2',
    'isCase': 'false',
    'stateId': 'welcomeGrid-45_dashboard0',
    'page': '1',
    'start': '0',
    'limit': '100',
    'isPoll': 'true'
}


def fetch_charges(session) -> Tuple[List[dict], Dict[str, dict]]:
    """
    Ανακτά OTS (queryId=2) και δημιουργεί mapping
    
    Κάθε εγγραφή περιέχει το W001_P_FLD10 (όνομα υπαλλήλου που χρεώθηκε)
    
    Args:
        session: PKMSession instance
        
    Returns:
        tuple: (charges_records, charges_by_pkm)
            - charges_records: Λίστα με όλες τις OTS εγγραφές
            - charges_by_pkm: Dict με {pkm: charge_record} για γρήγορη αναζήτηση
    """
    charges_data = session.fetch_data(CHARGES_PARAMS)
    charges_records = charges_data.get('data', []) if charges_data and charges_data.get('success') else []
    
    # Δημιουργία mapping από PKM που εξάγουμε από το DESCRIPTION
    charges_by_pkm = {}
    for rec in charges_records:
        # Δοκιμή 1: Από W007_P_FLD21
        pkm = str(rec.get('W007_P_FLD21', '')).strip()
        
        # Δοκιμή 2: Εξαγωγή από DESCRIPTION (π.χ. "Αίτημα 2026/106653 ....")
        if not pkm:
            pkm = _extract_pkm_from_description(rec.get('DESCRIPTION', ''))
        
        if pkm:
            charges_by_pkm[pkm] = rec
    
    return charges_records, charges_by_pkm


def _extract_pkm_from_description(description: str) -> Optional[str]:
    """
    Εξάγει τον αριθμό ΠΚΜ από το DESCRIPTION
    
    Args:
        description: DESCRIPTION field (π.χ. "Αίτημα 2026/106653 ΚΗΠΟΣ-258403847")
        
    Returns:
        str: Αριθμός ΠΚΜ (π.χ. "106653") ή None
    """
    # Decode HTML entities
    description = html.unescape(description)
    
    # Extract PKM: "Αίτημα 2026/106653 ..." -> 106653
    import re
    match = re.search(r'Αίτημα\s+\d+/(\d+)', description)
    return match.group(1) if match else None


def get_employee_from_charge(charge: dict) -> Optional[str]:
    """
    Εξάγει το όνομα του υπαλλήλου που χρεώθηκε την υπόθεση
    
    Προέρχεται από το πεδίο W001_P_FLD10 των OTS εγγραφών
    
    Args:
        charge: OTS record (record από queryId=2)
        
    Returns:
        str: Όνομα υπαλλήλου (π.χ. "ΓΑΛΟΥΠΗ ΕΥΑΓΓΕΛΙΑ") ή None
    """
    employee = charge.get('W001_P_FLD10', '')
    if employee and isinstance(employee, str):
        # Decode HTML entities
        employee = html.unescape(employee).strip()
        return employee if employee else None
    return None


def fetch_ots_detail_payload(monitor, doc_id: str) -> Optional[dict]:
    """Fetch OTS detail payload from DataServices for a given doc_id.

    Uses: /services/DataServices/fetchDataTableRecord/2/{doc_id}
    """
    if not doc_id:
        return None

    session = getattr(monitor, 'session', None)
    base_url = getattr(monitor, 'base_url', '')
    jwt_token = getattr(monitor, 'jwt_token', None)
    main_page_url = getattr(monitor, 'main_page_url', '')

    if not session or not base_url:
        return None

    url = base_url.rstrip('/') + f"/services/DataServices/fetchDataTableRecord/2/{doc_id}"
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
    except Exception:
        return None

    if not payload.get('success', False):
        return None

    return payload


def get_employee_from_ots_detail(monitor, doc_id: str) -> Optional[str]:
    """Extract W001_P_FLD10 (employee) from OTS detail payload."""
    payload = fetch_ots_detail_payload(monitor, doc_id)
    employee = extract_field(payload, 'W001_P_FLD10') if payload else None
    return html.unescape(employee).strip() if employee else None


def add_charge_info(incoming_records: List[dict], charges_by_pkm: Dict[str, dict], monitor=None, enrich_missing: bool = False) -> List[dict]:
    """
    Προσθέτει πληροφορίες OTS ανάθεσης στα incoming records
    
    Ταιριάζει εισερχόμενες αιτήσεις με OTS εγγραφές via PKM matching.
    Αν βρεθεί αντιστοίχηση, προσθέτει το W001_P_FLD10 (όνομα υπαλλήλου).
    
    Args:
        incoming_records: Portal incoming records (queryId=6)
        charges_by_pkm: Dict με {pkm: charge_record} από queryId=2
        monitor: PKMMonitor instance (optional, για enrichment)
        enrich_missing: Αν True, χρησιμοποιεί API calls για να βρει χρεώσεις που λείπουν
        
    Returns:
        list: Incoming records εμπλουτισμένα με _charge metadata
    """
    enriched = []
    
    for rec in incoming_records:
        # Αντιγραφή original record
        enriched_rec = rec.copy()
        
        # Ανάκτηση PKM - το case_id στα simplified records είναι το W007_P_FLD21 (το PKM)
        # Στόχος: ταίριασμα με OTS εγγραφές που έχουν PKM στο DESCRIPTION
        pkm = str(rec.get('case_id', '')).strip()
        if not pkm:
            # Fallback: protocol_number
            pkm = str(rec.get('protocol_number', '')).strip()
        if not pkm:
            # Fallback: W007_P_FLD21 αν υπάρχει
            pkm = str(rec.get('W007_P_FLD21', '')).strip()
        
        # Προσθήκη charge info αν υπάρχει OTS εγγραφή
        if pkm and pkm in charges_by_pkm:
            charge = charges_by_pkm[pkm]
            employee = get_employee_from_charge(charge)
            
            enriched_rec['_charge'] = {
                'charged': True,
                'employee': employee,  # ← W001_P_FLD10 από queryId=2
                'doc_id': charge.get('DOCID', ''),
                'case_id': charge.get('W001_P_FLD1', ''),
                'description': charge.get('DESCRIPTION', '')
            }
        else:
            # Αν δεν βρέθηκε στα charges, δοκιμή enrichment με API calls
            employee = None
            if enrich_missing and monitor:
                # Χρησιμοποιούμε το doc_id από το record (όχι το pkm/case_id)
                doc_id = str(rec.get('doc_id', '')).strip()
                if doc_id:
                    employee = enrich_charge_with_employee(monitor, doc_id)
            
            enriched_rec['_charge'] = {
                'charged': bool(employee),  # True αν βρέθηκε από enrichment
                'employee': employee,
                'doc_id': rec.get('doc_id'),
                'case_id': pkm if employee else None,
                'description': None,
                'enriched': bool(employee)  # Flag για να ξέρουμε ότι προήλθε από enrichment
            }
        
        enriched.append(enriched_rec)
    
    return enriched


def get_charge_info(record: dict, charges_by_pkm: Dict[str, dict]) -> Optional[dict]:
    """
    Επιστρέφει πληροφορίες OTS ανάθεσης για συγκεκριμένο incoming record
    
    Αναζητά OTS εγγραφή από queryId=2 που ταιριάζει με το PKM της εισερχόμενης αιτήσης.
    
    Args:
        record: Portal incoming record
        charges_by_pkm: Dict με {pkm: charge_record} από queryId=2
        
    Returns:
        dict: Πληροφορίες (employee, pkm, κλπ) ή None αν δεν βρεθεί
    """
    # Το case_id στα simplified records είναι το PKM (W007_P_FLD21)
    pkm = str(record.get('case_id', '')).strip()
    if not pkm:
        pkm = str(record.get('protocol_number', '')).strip()
    if not pkm:
        pkm = str(record.get('W007_P_FLD21', '')).strip()
    
    if pkm and pkm in charges_by_pkm:
        charge = charges_by_pkm[pkm]
        employee = get_employee_from_charge(charge)
        
        return {
            'pkm': pkm,
            'employee': employee,
            'doc_id': charge.get('DOCID', ''),
            'case_id': charge.get('W001_P_FLD1', ''),
            'description': html.unescape(charge.get('DESCRIPTION', ''))
        }
    return None


def filter_charged(records: List[dict]) -> List[dict]:
    """
    Φιλτράρει records που έχουν OTS ανάθεση (χρεώθηκαν)
    
    Args:
        records: Incoming records με _charge info
        
    Returns:
        list: Records που έχουν ανάθεση υπαλλήλου
    """
    return [r for r in records if r.get('_charge', {}).get('charged')]


def filter_uncharged(records: List[dict]) -> List[dict]:
    """
    Φιλτράρει records που ΔΕΝ έχουν OTS ανάθεση (δεν χρεώθηκαν)
    
    Args:
        records: Incoming records με _charge info
        
    Returns:
        list: Records που ΔΕΝ έχουν ανάθεση υπαλλήλου
    """
    return [r for r in records if not r.get('_charge', {}).get('charged')]


def get_charge_statistics(records: List[dict]) -> dict:
    """
    Υπολογίζει στατιστικά OTS αναθέσεων υπαλλήλων
    
    Args:
        records: Incoming records με _charge info
        
    Returns:
        dict: Στατιστικά (σύνολο, αναθέσεις, μη αναθέσεις, κλπ)
    """
    total = len(records)
    charged = len(filter_charged(records))
    uncharged = total - charged
    
    # Μοναδικοί υπάλληλοι που χρεώθηκαν υποθέσεις
    employees = set()
    for rec in filter_charged(records):
        employee = rec.get('_charge', {}).get('employee')
        if employee:
            employees.add(employee)
    
    return {
        'total': total,
        'charged': charged,
        'uncharged': uncharged,
        'charged_percentage': (charged / total * 100) if total > 0 else 0,
        'unique_employees': len(employees),
        'employees': sorted(list(employees))
    }


def fetch_charges_from_queryid3(session) -> Tuple[List[dict], Dict[str, dict]]:
    """
    Ανακτά Routing/Forwarding εγγραφές από queryId=3
    
    Χρησιμοποιεί USER_GROUP_ID_TO (ο ανατιθέμενος) ως χρέωση/ανάθεση.
    
    Args:
        session: PKMSession instance
        
    Returns:
        tuple: (routing_records, charges_by_pkm)
            - routing_records: Λίστα με όλες τις Routing εγγραφές
            - charges_by_pkm: Dict με {pkm: routing_record} για γρήγορη αναζήτηση
    """
    params_q3 = {
        'queryId': '3',
        'queryOwner': '3',
        'isCase': 'false',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '100',
        'isPoll': 'true'
    }
    
    routing_data = session.fetch_data(params_q3)
    routing_records = routing_data.get('data', []) if routing_data and routing_data.get('success') else []
    
    # Δημιουργία mapping από PKM που εξάγουμε από το DESCRIPTION
    charges_by_pkm = {}
    for rec in routing_records:
        # Εξαγωγή PKM από DESCRIPTION (π.χ. "Αίτημα 2026/106129 ...")
        description = rec.get('DESCRIPTION', '')
        pkm = _extract_pkm_from_description(description)
        
        if pkm:
            # Χρησιμοποιούμε USER_GROUP_ID_TO ως χρέωση (ο ανατιθέμενος)
            charges_by_pkm[pkm] = rec
    
    return routing_records, charges_by_pkm


def get_employee_from_queryid3_charge(charge: dict) -> Optional[str]:
    """
    Εξάγει το όνομα του υπαλλήλου που ανατέθηκε (USER_GROUP_ID_TO)
    
    Args:
        charge: Routing record από queryId=3
        
    Returns:
        str: Όνομα υπαλλήλου ή None
    """
    employee = charge.get('USER_GROUP_ID_TO', '')
    if employee and isinstance(employee, str):
        employee = employee.strip()
        return employee if employee else None
    return None


def fetch_charges_combined(session) -> Tuple[List[dict], Dict[str, dict]]:
    """
    Ανακτά χρεώσεις από ΣΥΝΔΥΑΣΜΟ queryId=2 (OTS) και queryId=3 (Routing)
    
    Δίνει προτεραιότητα σε queryId=3, fallback σε queryId=2.
    Συνδυάζει και τις δύο πηγές για καλύτερη κάλυψη.
    
    Args:
        session: PKMSession instance
        
    Returns:
        tuple: (combined_records, charges_by_pkm)
            - combined_records: Λίστα με OTS + Routing εγγραφές
            - charges_by_pkm: Dict με {pkm: record} (προτεραιότητα queryId=3)
    """
    # Ανάκτηση από queryId=2 (OTS)
    ots_records, ots_by_pkm = fetch_charges(session)
    
    # Ανάκτηση από queryId=3 (Routing)
    routing_records, q3_by_pkm = fetch_charges_from_queryid3(session)
    
    # Συνδυασμός: queryId=3 πρώτα, fallback σε queryId=2
    combined_charges_by_pkm = {}
    combined_charges_by_pkm.update(ots_by_pkm)  # Base: OTS
    combined_charges_by_pkm.update(q3_by_pkm)   # Override with queryId=3
    
    # Λίστα με όλες τις εγγραφές
    combined_records = ots_records + routing_records
    
    return combined_records, combined_charges_by_pkm


def add_charge_info_from_combined(incoming_records: List[dict], charges_by_pkm: Dict[str, dict], monitor=None, enrich_missing: bool = False) -> List[dict]:
    """
    Προσθέτει χρέωση info από συνδυασμό queryId=2 + queryId=3
    
    Σε περίπτωση που το PKM υπάρχει και στις δύο πηγές, χρησιμοποιεί:
    - USER_GROUP_ID_TO από queryId=3 (Routing) αν υπάρχει
    - W001_P_FLD10 από queryId=2 (OTS) αν queryId=3 δεν το έχει
    
    Args:
        incoming_records: Portal incoming records (queryId=6)
        charges_by_pkm: Dict με συνδυασμένα {pkm: record}
        monitor: PKMMonitor instance (optional, για enrichment)
        enrich_missing: Αν True, χρησιμοποιεί API calls για να βρει χρεώσεις που λείπουν
        
    Returns:
        list: Enriched incoming records με _charge metadata
    """
    enriched = []
    
    for rec in incoming_records:
        enriched_rec = rec.copy()
        
        # Ανάκτηση PKM
        pkm = str(rec.get('case_id', '')).strip()
        if not pkm:
            pkm = str(rec.get('protocol_number', '')).strip()
        if not pkm:
            pkm = str(rec.get('W007_P_FLD21', '')).strip()
        
        # Προσθήκη charge info
        if pkm and pkm in charges_by_pkm:
            charge = charges_by_pkm[pkm]
            
            # Χρησιμοποιούμε ΜΟΝΟ W001_P_FLD10 (employee name), ΟΧΙ USER_GROUP_ID_TO (department/team)
            employee = get_employee_from_charge(charge)
            
            # Αν δεν υπάρχει employee, δοκιμή enrichment
            if not employee and enrich_missing and monitor:
                doc_id = str(enriched_rec.get('doc_id', '')).strip()
                if doc_id:
                    employee = enrich_charge_with_employee(monitor, doc_id)
            
            enriched_rec['_charge'] = {
                'charged': bool(employee),
                'employee': employee,
                'doc_id': charge.get('DOCID', ''),
                'case_id': charge.get('W001_P_FLD1', charge.get('W001_P_FLD17', '')),
                'description': html.unescape(charge.get('DESCRIPTION', '')),
                'enriched': False  # Will be True only if came from API enrichment below
            }
        else:
            # Αν δεν βρέθηκε στα charges, δοκιμή enrichment με API calls
            employee = None
            if enrich_missing and monitor:
                # Χρησιμοποιούμε το doc_id από το record (όχι το pkm/case_id)
                doc_id = str(enriched_rec.get('doc_id', '')).strip()
                if doc_id:
                    employee = enrich_charge_with_employee(monitor, doc_id)
            
            enriched_rec['_charge'] = {
                'charged': bool(employee),  # True αν βρέθηκε από enrichment
                'employee': employee,
                'doc_id': enriched_rec.get('doc_id'),
                'case_id': pkm if employee else None,
                'description': None,
                'enriched': bool(employee)  # Flag για να ξέρουμε ότι προήλθε από enrichment
            }
        
        enriched.append(enriched_rec)
    
    return enriched


def print_charge_statistics(records: List[dict]) -> None:
    """
    Εκτυπώνει στατιστικά OTS αναθέσεων υπαλλήλων
    
    Args:
        records: Incoming records με _charge info
    """
    stats = get_charge_statistics(records)
    
    print("\n" + "="*60)
    print("📊 ΣΤΑΤΙΣΤΙΚΑ OTS ΑΝΑΘΕΣΕΩΝ".center(60))
    print("="*60)
    print(f"Σύνολο αιτήσεων:      {stats['total']}")
    print(f"Αναθεμένες:           {stats['charged']} ({stats['charged_percentage']:.1f}%)")
    print(f"Μη αναθεμένες:        {stats['uncharged']}")
    print(f"Μοναδικοί υπάλληλοι:  {stats['unique_employees']}")
    
    if stats['employees']:
        print("\nΥπάλληλοι:")
        for emp in stats['employees']:
            emp_records = [r for r in filter_charged(records) 
                          if r.get('_charge', {}).get('employee') == emp]
            print(f"  • {emp}: {len(emp_records)} αιτήσεις")
    print("="*60)


def fetch_case_detail_payload(monitor, doc_id: str) -> Optional[dict]:
    """Fetch case detail from DataServices endpoint 7.
    
    Uses: /services/DataServices/fetchDataTableRecord/7/{doc_id}
    Returns W007_P_FLD7 which contains docIds array.
    
    Args:
        monitor: PKMMonitor instance
        doc_id: Document ID (DOCID from incoming record)
        
    Returns:
        dict: API response payload or None
    """
    if not doc_id:
        return None

    session = getattr(monitor, 'session', None)
    base_url = getattr(monitor, 'base_url', '')
    jwt_token = getattr(monitor, 'jwt_token', None)
    main_page_url = getattr(monitor, 'main_page_url', '')

    if not session or not base_url:
        return None

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
        print(f"[DEBUG] Failed to fetch case detail for doc_id {doc_id}: {exc}")
        return None

    if not payload.get('success', False):
        print(f"[DEBUG] API returned success=false for doc_id {doc_id}: {payload.get('message', 'No message')}")
        return None

    return payload


def get_doc_id_from_w007_p_fld7(payload: dict) -> Optional[str]:
    """Extract DOCID from W007_P_FLD7.docIds array.
    
    Args:
        payload: API response from fetchDataTableRecord/7
        
    Returns:
        str: First DOCID from docIds array or None
    """
    if not payload:
        return None
    
    # Handle both dict and list response formats
    data = payload.get('data')
    if isinstance(data, list):
        # If data is a list, get first item
        if not data or len(data) == 0:
            return None
        data = data[0]
    
    if not isinstance(data, dict):
        return None
    
    w007_p_fld7 = data.get('W007_P_FLD7')
    if not w007_p_fld7 or not isinstance(w007_p_fld7, dict):
        return None
    
    doc_ids = w007_p_fld7.get('docIds', [])
    if doc_ids and isinstance(doc_ids, list) and len(doc_ids) > 0:
        return str(doc_ids[0]).strip()
    
    return None


def enrich_charge_with_employee(monitor, doc_id: str) -> Optional[str]:
    """Fetch employee for a charged case using two-step API calls.
    
    Step 1: GET /services/DataServices/fetchDataTableRecord/7/{doc_id}
            → Extract charge DOCID from W007_P_FLD7.docIds[0]
    
    Step 2: GET /services/DataServices/fetchDataTableRecord/2/{charge_docId}
            → Extract employee from W001_P_FLD10
    
    Args:
        monitor: PKMMonitor instance
        doc_id: Document ID (DOCID from incoming record)
        
    Returns:
        str: Employee name or None
    """
    # Step 1: Get charge DOCID from case detail
    case_payload = fetch_case_detail_payload(monitor, doc_id)
    charge_doc_id = get_doc_id_from_w007_p_fld7(case_payload)
    
    if not charge_doc_id:
        return None
    
    # Step 2: Get employee from OTS detail using the charge DOCID
    employee = get_employee_from_ots_detail(monitor, charge_doc_id)
    return employee

