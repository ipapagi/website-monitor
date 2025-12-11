#!/usr/bin/env python
import json

with open('data/incoming_requests/incoming_2025-12-11.json', encoding='utf-8') as f:
    data = json.load(f)

# Find case 923034
for rec in data['records']:
    if rec.get('case_id') == '923034':
        print(f"Case 923034:")
        print(f"  protocol_number: '{rec.get('protocol_number')}'")
        print(f"  procedure: '{rec.get('procedure')}'")
        print(f"  directory: '{rec.get('directory')}'")
        print(f"  party: '{rec.get('party')}'")
        break
