import json

with open('data/incoming_requests/incoming_2025-12-03.json', 'r', encoding='utf-8') as f:
    incoming_03 = json.load(f)

with open('data/incoming_requests/incoming_2025-12-11.json', 'r', encoding='utf-8') as f:
    incoming_11 = json.load(f)

rec_03 = incoming_03['records'][0]
rec_11 = [r for r in incoming_11['records'] if r['case_id'] == '923034'][0]

print('Record from incoming_2025-12-03.json (first record):')
print(f"  case_id: {rec_03['case_id']}")
print(f"  protocol: {rec_03.get('protocol_number', 'EMPTY')}")
proc = rec_03.get('procedure', 'EMPTY')
print(f"  procedure: {proc[:40] if proc != 'EMPTY' else 'EMPTY'}")
dir_str = rec_03.get('directory', 'EMPTY')
print(f"  directory: {dir_str[:40] if dir_str != 'EMPTY' else 'EMPTY'}")

print()
print('Record 923034 from incoming_2025-12-11.json:')
print(f"  case_id: {rec_11['case_id']}")
print(f"  protocol: '{rec_11.get('protocol_number', '')}'")
proc = rec_11.get('procedure', '')
print(f"  procedure: '{proc[:40] if proc else 'EMPTY'}'")
dir_str = rec_11.get('directory', '')
print(f"  directory: '{dir_str[:40] if dir_str else 'EMPTY'}'")
