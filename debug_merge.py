#!/usr/bin/env python
import json
from pathlib import Path

# Check incoming_2025-12-09
with open('data/incoming_requests/incoming_2025-12-09.json', encoding='utf-8') as f:
    data_09 = json.load(f)
    
# Check incoming_2025-12-11
with open('data/incoming_requests/incoming_2025-12-11.json', encoding='utf-8') as f:
    data_11 = json.load(f)

recs_09 = {r.get('case_id'): r for r in data_09['records']}
recs_11 = {r.get('case_id'): r for r in data_11['records']}

print("Case 923034 in 2025-12-09:")
r09 = recs_09.get('923034')
if r09:
    print(f"  protocol_number: '{r09.get('protocol_number')}'")
    print(f"  procedure: '{r09.get('procedure')}'")
    print(f"  directory: '{r09.get('directory')}'")
else:
    print("  NOT FOUND")

print("\nCase 923034 in 2025-12-11:")
r11 = recs_11.get('923034')
if r11:
    print(f"  protocol_number: '{r11.get('protocol_number')}'")
    print(f"  procedure: '{r11.get('procedure')}'")
    print(f"  directory: '{r11.get('directory')}'")
else:
    print("  NOT FOUND")

# Check dates between them
all_files = sorted(Path('data/incoming_requests').glob('incoming_*.json'))
print("\nAll snapshot files:")
for f in all_files:
    print(f"  {f.name}")
