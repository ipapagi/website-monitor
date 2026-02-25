"""
OTS Assignments Module - Συσχέτιση εισερχόμενων με αναθέσεις τμημάτων

Παρέχει λειτουργικότητα για:
- Ανάκτηση OTS εισερχόμενων (Πρωτόκολλο)
- Συσχέτιση με Portal εισερχόμενα μέσω ΠΚΜ
- Προσθήκη πληροφοριών ανάθεσης στα records
"""
import html
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# OTS Configuration
OTS_INCOMING_PARAMS = {
    'queryId': '2',
    'queryOwner': '3',
    'isCase': 'false',
    'stateId': 'welcomeGrid-18_dashboard0',
    'page': '1',
    'start': '0',
    'limit': '100',
    'isPoll': 'false'
}


def fetch_ots_assignments(session) -> Tuple[List[dict], Dict[str, dict]]:
    """
    Ανακτά OTS εισερχόμενα και δημιουργεί mapping με ΠΚΜ
    
    Args:
        session: PKMSession instance
        
    Returns:
        tuple: (ots_records, ots_by_pkm)
            - ots_records: Λίστα με όλα τα OTS records
            - ots_by_pkm: Dict με {pkm: ots_record}
    """
    ots_data = session.fetch_data(OTS_INCOMING_PARAMS)
    ots_records = ots_data.get('data', []) if ots_data and ots_data.get('success') else []
    
    # Δημιουργία mapping από ΠΚΜ
    ots_by_pkm = {}
    for rec in ots_records:
        pkm = _extract_pkm_from_description(rec.get('DESCRIPTION', ''))
        if pkm:
            ots_by_pkm[pkm] = rec
    
    return ots_records, ots_by_pkm


def _extract_pkm_from_description(description: str) -> Optional[str]:
    """
    Εξάγει τον αριθμό ΠΚΜ από το DESCRIPTION
    
    Args:
        description: OTS DESCRIPTION field (π.χ. "Αίτημα 2026/106653 ΨΥΤΙΛΛΗΣ-136290675")
        
    Returns:
        str: Αριθμός ΠΚΜ (π.χ. "106653") ή None
    """
    # Decode HTML entities
    description = html.unescape(description)
    
    # Extract PKM: "Αίτημα 2026/106653 ..." -> 106653
    match = re.search(r'Αίτημα\s+\d+/(\d+)', description)
    return match.group(1) if match else None


def add_assignment_info(incoming_records: List[dict], ots_by_pkm: Dict[str, dict]) -> List[dict]:
    """
    Προσθέτει πληροφορίες ανάθεσης στα incoming records
    
    Args:
        incoming_records: Portal incoming records
        ots_by_pkm: Dict με {pkm: ots_record}
        
    Returns:
        list: Incoming records εμπλουτισμένα με assignment info
    """
    enriched = []
    
    for rec in incoming_records:
        pkm = str(rec.get('W007_P_FLD21', '')).strip()
        
        # Αντιγραφή original record
        enriched_rec = rec.copy()
        
        # Προσθήκη assignment info αν υπάρχει
        if pkm and pkm in ots_by_pkm:
            ots = ots_by_pkm[pkm]
            enriched_rec['_assignment'] = {
                'assigned': True,
                'department': ots.get('USER_GROUP_ID_TO', ''),
                'department_id': ots.get('USER_GROUP_ID_TO_ID', ''),
                'date_assigned': ots.get('DATE_START_ISO', ''),
                'status': ots.get('ACTIONS', ''),
                'assigned_by': ots.get('USER_ID_FROM', ''),
                'ots_docid': ots.get('DOCID', '')
            }
        else:
            enriched_rec['_assignment'] = {
                'assigned': False,
                'department': None,
                'department_id': None,
                'date_assigned': None,
                'status': None,
                'assigned_by': None,
                'ots_docid': None
            }
        
        enriched.append(enriched_rec)
    
    return enriched


def get_assignment_info(record: dict, ots_by_pkm: Dict[str, dict]) -> Optional[dict]:
    """
    Επιστρέφει πληροφορίες ανάθεσης για συγκεκριμένο incoming record
    
    Args:
        record: Portal incoming record
        ots_by_pkm: Dict με {pkm: ots_record}
        
    Returns:
        dict: Assignment info ή None
    """
    pkm = str(record.get('W007_P_FLD21', '')).strip()
    
    if pkm and pkm in ots_by_pkm:
        ots = ots_by_pkm[pkm]
        return {
            'pkm': pkm,
            'department': ots.get('USER_GROUP_ID_TO', ''),
            'department_short': _shorten_department(ots.get('USER_GROUP_ID_TO', '')),
            'department_id': ots.get('USER_GROUP_ID_TO_ID', ''),
            'date_assigned': ots.get('DATE_START_ISO', ''),
            'date_assigned_formatted': ots.get('DATE_START', ''),
            'status': ots.get('ACTIONS', ''),
            'assigned_by': ots.get('USER_ID_FROM', ''),
            'ots_docid': ots.get('DOCID', ''),
            'instance_id': ots.get('INSTANCEID', ''),
            'route_id': ots.get('ROUTID', '')
        }
    return None


def _shorten_department(full_department: str) -> str:
    """
    Συντομεύει το όνομα τμήματος
    
    Examples:
        "ΤΜΗΜΑ ΧΟΡΗΓΗΣΗΣ ΑΔΕΙΩΝ ΒΙΟΜΗΧΑΝΙΑΣ..." -> "ΤΜΗΜΑ ΧΟΡΗΓΗΣΗΣ ΑΔΕΙΩΝ..."
    """
    if not full_department:
        return ''
    
    # Split και κρατάμε μέχρι την παρένθεση
    if '(' in full_department:
        full_department = full_department.split('(')[0].strip()
    
    # Κρατάμε πρώτες 60 χαρακτήρες
    if len(full_department) > 60:
        return full_department[:57] + '...'
    
    return full_department


def filter_assigned(incoming_records: List[dict]) -> List[dict]:
    """
    Φιλτράρει και επιστρέφει μόνο τα assigned records
    
    Args:
        incoming_records: Records με _assignment field
        
    Returns:
        list: Assigned records only
    """
    return [rec for rec in incoming_records if rec.get('_assignment', {}).get('assigned', False)]


def filter_unassigned(incoming_records: List[dict]) -> List[dict]:
    """
    Φιλτράρει και επιστρέφει μόνο τα unassigned records
    
    Args:
        incoming_records: Records με _assignment field
        
    Returns:
        list: Unassigned records only
    """
    return [rec for rec in incoming_records if not rec.get('_assignment', {}).get('assigned', False)]


def get_assignment_statistics(incoming_records: List[dict]) -> dict:
    """
    Υπολογίζει στατιστικά για assignments
    
    Args:
        incoming_records: Records με _assignment field
        
    Returns:
        dict: Statistics με counts, percentages, by_department
    """
    total = len(incoming_records)
    assigned = len(filter_assigned(incoming_records))
    unassigned = total - assigned
    
    # Group by department
    by_department = {}
    for rec in filter_assigned(incoming_records):
        dept = rec['_assignment'].get('department_short', 'Άγνωστο')
        by_department[dept] = by_department.get(dept, 0) + 1
    
    return {
        'total': total,
        'assigned': assigned,
        'unassigned': unassigned,
        'assigned_percentage': (assigned / total * 100) if total > 0 else 0,
        'unassigned_percentage': (unassigned / total * 100) if total > 0 else 0,
        'by_department': by_department,
        'unique_departments': len(by_department)
    }


def format_assignment_for_display(record: dict) -> str:
    """
    Μορφοποιεί assignment info για display
    
    Args:
        record: Record με _assignment field
        
    Returns:
        str: Formatted assignment string
    """
    assignment = record.get('_assignment', {})
    
    if not assignment.get('assigned'):
        return "⏳ Δεν έχει χρεωθεί"
    
    dept = _shorten_department(assignment.get('department', 'Άγνωστο'))
    date = assignment.get('date_assigned', '')[:10]
    status = assignment.get('status', '')
    
    return f"✅ {dept} ({date}) - {status}"


def simplify_ots_record(ots_record: dict) -> dict:
    """
    Απλοποιεί OTS record σε πιο readable μορφή
    
    Args:
        ots_record: OTS record
        
    Returns:
        dict: Simplified record
    """
    return {
        'docid': ots_record.get('DOCID'),
        'pkm': _extract_pkm_from_description(ots_record.get('DESCRIPTION', '')),
        'description': html.unescape(ots_record.get('DESCRIPTION', '')),
        'department': ots_record.get('USER_GROUP_ID_TO'),
        'department_short': _shorten_department(ots_record.get('USER_GROUP_ID_TO', '')),
        'department_id': ots_record.get('USER_GROUP_ID_TO_ID'),
        'date_assigned': ots_record.get('DATE_START_ISO'),
        'date_formatted': ots_record.get('DATE_START'),
        'status': ots_record.get('ACTIONS'),
        'assigned_by': ots_record.get('USER_ID_FROM'),
        'assigned_by_id': ots_record.get('USER_ID_FROM_ID'),
        'type': ots_record.get('TYPESTR'),
        'instance_id': ots_record.get('INSTANCEID'),
        'route_id': ots_record.get('ROUTID')
    }
