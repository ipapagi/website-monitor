"""Ενημέρωση παλαιότερων snapshots με στοιχεία από το πιο πρόσφατο"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_project_root
from incoming import list_incoming_snapshot_dates, load_incoming_snapshot, save_incoming_snapshot

def backfill_snapshots(source_date_str=None, dry_run=True):
    """Ενημερώνει παλαιότερα snapshots με στοιχεία από το πιο πρόσφατο"""
    
    dates = list_incoming_snapshot_dates()
    if not dates:
        print("❌ Δεν βρέθηκαν snapshots")
        return
    
    # Χρήση του πιο πρόσφατου αν δεν δόθηκε
    if source_date_str is None:
        source_date = dates[-1]
        source_date_str = source_date.strftime("%Y-%m-%d")
    
    print(f"📂 Πηγή: {source_date_str}")
    source_snap = load_incoming_snapshot(source_date_str)
    if not source_snap:
        print(f"❌ Δεν βρέθηκε snapshot για {source_date_str}")
        return
    
    # Δημιουργία dict με case_id ως κλειδί
    source_dict = {}
    for rec in source_snap.get('records', []):
        case_id = rec.get('case_id')
        if case_id:
            source_dict[case_id] = rec
    
    print(f"📋 Εγγραφές πηγής: {len(source_dict)}")
    print(f"{'🔍 DRY RUN - Δεν θα γίνουν αλλαγές' if dry_run else '⚠️  LIVE MODE - Θα ενημερωθούν τα αρχεία'}")
    print("="*60)
    
    fields_to_copy = ['protocol_number', 'procedure', 'directory', 'document_category']
    
    for snapshot_date in dates:
        date_str = snapshot_date.strftime("%Y-%m-%d")
        if date_str == source_date_str:
            continue
        
        snap = load_incoming_snapshot(date_str)
        if not snap:
            continue
        
        records = snap.get('records', [])
        updated_count = 0
        
        for rec in records:
            case_id = rec.get('case_id')
            if case_id and case_id in source_dict:
                source_rec = source_dict[case_id]
                changed = False
                for field in fields_to_copy:
                    source_val = source_rec.get(field, '')
                    current_val = rec.get(field, '')
                    # Ενημέρωση μόνο αν η πηγή έχει τιμή και η τρέχουσα είναι κενή
                    if source_val and not current_val:
                        rec[field] = source_val
                        changed = True
                if changed:
                    updated_count += 1
        
        if updated_count > 0:
            print(f"  📅 {date_str}: {updated_count} εγγραφές ενημερώθηκαν")
            if not dry_run:
                save_incoming_snapshot(date_str, records)
        else:
            print(f"  📅 {date_str}: καμία αλλαγή")
    
    print("="*60)
    if dry_run:
        print("✅ DRY RUN ολοκληρώθηκε. Τρέξε με --live για να εφαρμοστούν οι αλλαγές.")
    else:
        print("✅ Ενημέρωση ολοκληρώθηκε!")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Backfill παλαιότερων snapshots')
    parser.add_argument('--source', type=str, help='Ημερομηνία πηγής (YYYY-MM-DD)')
    parser.add_argument('--live', action='store_true', help='Εφαρμογή αλλαγών (όχι dry run)')
    args = parser.parse_args()
    
    backfill_snapshots(source_date_str=args.source, dry_run=not args.live)
