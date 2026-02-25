"""Διαχείριση δοκιμαστικών χρηστών"""
import os
import json
from config import get_data_path

def get_test_users_config_path():
    return get_data_path('test_users.json')

def load_test_users_config():
    """Φορτώνει τη ρύθμιση δοκιμαστικών χρηστών"""
    path = get_test_users_config_path()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Default config
    return {
        'internal_user_suffix': '(Εσωτ. χρήστης)',
        'test_users': [],
        'test_companies': []
    }

def is_test_record(record, config=None):
    """Ελέγχει αν μια εγγραφή είναι δοκιμαστική"""
    if config is None:
        config = load_test_users_config()
    
    party = record.get('party', '')
    
    # Εσωτερικός χρήστης
    internal_suffix = config.get('internal_user_suffix', '(Εσωτ. χρήστης)')
    if internal_suffix and internal_suffix in party:
        return True, 'internal_user'
    
    # Συγκεκριμένοι δοκιμαστικοί χρήστες
    for test_user in config.get('test_users', []):
        if test_user.upper() in party.upper():
            return True, 'test_user'
    
    # Εταιρείες υποστήριξης
    for company in config.get('test_companies', []):
        if company.upper() in party.upper():
            return True, 'test_company'
    
    return False, None

def classify_records(records):
    """Κατηγοριοποιεί εγγραφές σε πραγματικές και δοκιμαστικές"""
    config = load_test_users_config()
    real = []
    test = []
    
    for rec in records:
        is_test, reason = is_test_record(rec, config)
        rec['is_test'] = is_test
        rec['test_reason'] = reason
        if is_test:
            test.append(rec)
        else:
            real.append(rec)
    
    return real, test

def get_record_stats(records):
    """Επιστρέφει στατιστικά για τις εγγραφές"""
    real, test = classify_records(records)
    
    # Ανάλυση δοκιμαστικών
    test_by_reason = {}
    for rec in test:
        reason = rec.get('test_reason', 'unknown')
        test_by_reason[reason] = test_by_reason.get(reason, 0) + 1
    
    return {
        'total': len(records),
        'real': len(real),
        'test': len(test),
        'test_breakdown': test_by_reason
    }
