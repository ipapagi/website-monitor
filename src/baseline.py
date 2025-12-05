"""Διαχείριση baselines για διαδικασίες"""
import os
import json
from datetime import datetime
from config import get_baseline_path, get_all_procedures_baseline_path

def save_baseline(active_procedures):
    """Αποθηκεύει τις ενεργές διαδικασίες ως baseline"""
    baseline_path = get_baseline_path()
    os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
    baseline_data = {
        'timestamp': datetime.now().isoformat(),
        'count': len(active_procedures),
        'procedures': active_procedures
    }
    with open(baseline_path, 'w', encoding='utf-8') as f:
        json.dump(baseline_data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Baseline αποθηκεύτηκε: {baseline_path}")
    print(f"📋 Ενεργές διαδικασίες: {len(active_procedures)}")
    return baseline_path

def load_baseline():
    """Φορτώνει το baseline ενεργών διαδικασιών"""
    baseline_path = get_baseline_path()
    if not os.path.exists(baseline_path):
        return None
    with open(baseline_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_all_procedures_baseline(all_procedures):
    """Αποθηκεύει όλες τις διαδικασίες ως baseline"""
    baseline_path = get_all_procedures_baseline_path()
    os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
    baseline_data = {
        'timestamp': datetime.now().isoformat(),
        'count': len(all_procedures),
        'procedures': all_procedures
    }
    with open(baseline_path, 'w', encoding='utf-8') as f:
        json.dump(baseline_data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Baseline όλων των διαδικασιών αποθηκεύτηκε: {baseline_path}")
    print(f"📋 Σύνολο διαδικασιών: {len(all_procedures)}")
    return baseline_path

def load_all_procedures_baseline():
    """Φορτώνει το baseline όλων των διαδικασιών"""
    baseline_path = get_all_procedures_baseline_path()
    if not os.path.exists(baseline_path):
        return None
    with open(baseline_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_with_baseline(current_procedures, baseline_data):
    """Συγκρίνει τις τρέχουσες διαδικασίες με το baseline"""
    baseline_procedures = baseline_data.get('procedures', [])
    baseline_dict = {p['docid']: p for p in baseline_procedures}
    current_dict = {p['docid']: p for p in current_procedures}
    changes = {'new': [], 'removed': [], 'activated': [], 'deactivated': [], 'modified': []}
    
    for docid, proc in current_dict.items():
        if docid not in baseline_dict:
            if proc.get('ενεργή') == 'ΝΑΙ':
                changes['new'].append(proc)
        else:
            old_proc = baseline_dict[docid]
            if old_proc.get('ενεργή') != proc.get('ενεργή'):
                if proc.get('ενεργή') == 'ΝΑΙ':
                    changes['activated'].append({'old': old_proc, 'new': proc})
                else:
                    changes['deactivated'].append({'old': old_proc, 'new': proc})
            elif proc.get('ενεργή') == 'ΝΑΙ' and old_proc != proc:
                field_changes = {k: {'old': old_proc.get(k, ''), 'new': proc.get(k, '')} 
                               for k in proc.keys() if old_proc.get(k) != proc.get(k)}
                changes['modified'].append({'old': old_proc, 'new': proc, 'field_changes': field_changes})
    
    for docid, proc in baseline_dict.items():
        if docid not in current_dict:
            changes['removed'].append(proc)
    return changes

def compare_all_procedures_with_baseline(current_procedures, baseline_data):
    """Συγκρίνει όλες τις διαδικασίες με το baseline"""
    baseline_procedures = baseline_data.get('procedures', [])
    baseline_dict = {p['docid']: p for p in baseline_procedures}
    current_dict = {p['docid']: p for p in current_procedures}
    changes = {'new': [], 'removed': [], 'activated': [], 'deactivated': [], 'modified': []}
    
    for docid, proc in current_dict.items():
        if docid not in baseline_dict:
            changes['new'].append(proc)
        else:
            old_proc = baseline_dict[docid]
            if old_proc.get('ενεργή') != proc.get('ενεργή'):
                if proc.get('ενεργή') == 'ΝΑΙ':
                    changes['activated'].append({'old': old_proc, 'new': proc})
                else:
                    changes['deactivated'].append({'old': old_proc, 'new': proc})
            elif old_proc != proc:
                field_changes = {k: {'old': old_proc.get(k, ''), 'new': proc.get(k, '')} 
                               for k in set(list(proc.keys()) + list(old_proc.keys())) 
                               if old_proc.get(k) != proc.get(k)}
                changes['modified'].append({'old': old_proc, 'new': proc, 'field_changes': field_changes})
    
    for docid, proc in baseline_dict.items():
        if docid not in current_dict:
            changes['removed'].append(proc)
    return changes
