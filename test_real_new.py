from src.incoming import load_incoming_snapshot
from src.test_users import classify_records

snap = load_incoming_snapshot('2025-12-04')
prev = load_incoming_snapshot('2025-12-03')

records = snap.get('records', [])
prev_records = prev.get('records', [])

prev_dict = {r['case_id']: r for r in prev_records if r.get('case_id')}
curr_dict = {r['case_id']: r for r in records if r.get('case_id')}
new_docs = [r for cid, r in curr_dict.items() if cid not in prev_dict]

print(f'Νέες εγγραφές: {len(new_docs)}')

real_new, test_new = classify_records(new_docs)
print(f'Νέες πραγματικές: {len(real_new)}')
print(f'Νέες δοκιμαστικές: {len(test_new)}')

print('\nReal:')
for r in real_new:
    print(f'  - {r.get("case_id")} - {r.get("party")}')
