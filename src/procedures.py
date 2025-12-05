"""Διαχείριση procedures cache"""
import os
import json
from datetime import datetime
from config import get_procedures_cache_path

def load_procedures_cache():
    """Φορτώνει το procedures cache"""
    path = get_procedures_cache_path()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_procedures_cache(cache):
    """Αποθηκεύει το procedures cache"""
    path = get_procedures_cache_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def update_procedures_cache_from_procedures(procedures):
    """Ενημερώνει το procedures_cache από τη λίστα διαδικασιών"""
    procedures_cache = load_procedures_cache()
    cache_updated = False
    
    for proc in procedures:
        title = proc.get('περιγραφή', '')
        if not title:
            continue
        
        procedure_id = proc.get('αρ_διαδικασίας', '')
        code = proc.get('κωδικός', '')
        is_active = proc.get('ενεργή', '') == 'ΝΑΙ'
        
        if title not in procedures_cache:
            procedures_cache[title] = {
                'title': title,
                'procedure_id': procedure_id,
                'code': code,
                'is_active': is_active,
                'first_seen': datetime.now().isoformat(),
                'directories': []
            }
            cache_updated = True
        else:
            if procedure_id and procedures_cache[title].get('procedure_id') != procedure_id:
                procedures_cache[title]['procedure_id'] = procedure_id
                cache_updated = True
            if code and procedures_cache[title].get('code') != code:
                procedures_cache[title]['code'] = code
                cache_updated = True
            if procedures_cache[title].get('is_active') != is_active:
                procedures_cache[title]['is_active'] = is_active
                cache_updated = True
    
    if cache_updated:
        save_procedures_cache(procedures_cache)
        print(f"📝 Ενημερώθηκε το procedures_cache με {len(procedures)} διαδικασίες")
    
    return procedures_cache
