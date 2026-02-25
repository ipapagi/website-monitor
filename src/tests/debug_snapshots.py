import json
import os
from datetime import datetime
from pathlib import Path

# Φόρτωση snapshots απ'ευθείας
def load_snapshot(date_str):
    path = Path(__file__).parent / 'data' / 'incoming_requests' / f'incoming_{date_str}.json'
    if path.exists():
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return None

# Φόρτωση snapshots για την εβδομάδα 02-02 ως 02-08
monday = datetime(2026, 2, 2)
for day_offset in range(7):
    current_date = datetime(2026, 2, 2 + day_offset)
    if current_date.month != 2:
        continue
    date_str = current_date.strftime("%Y-%m-%d")
    
    snap = load_snapshot(date_str)
    if snap:
        records = snap.get('records', [])
        print(f"\n📅 {date_str}: {len(records)} αιτήσεις")
        
        # Δείξε τις πρώτες 3 αιτήσεις
        for i, rec in enumerate(records[:3]):
            print(f"  {i+1}. Case ID: {rec.get('case_id')}")
            print(f"     Submitted: {rec.get('submitted_at')}")
            print(f"     Protocol: {rec.get('protocol_number')}")
            print(f"     Directory: {rec.get('directory')}")
            print(f"     Subject: {rec.get('subject')[:50] if rec.get('subject') else 'N/A'}")
