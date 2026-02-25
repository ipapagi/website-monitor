"""Find position of case 93159 in records."""
import sys
import os
sys.path.insert(0, 'src')

if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from monitor import PKMMonitor
from utils import load_config
from incoming import simplify_incoming_records

config = load_config('config/config.yaml')
monitor = PKMMonitor(
    base_url=config['base_url'],
    urls=config['urls'],
    username=config['username'],
    password=config['password']
)

if not monitor.login():
    print("❌ Login failed")
    sys.exit(1)

print("✅ Login successful\n")

# Fetch incoming records
params = {'queryId': 6, 'limit': 100}
incoming_data = monitor.fetch_data(params)
incoming_records = incoming_data.get('data', []) if incoming_data else []
simplified = simplify_incoming_records(incoming_records)

print(f"📥 Fetched {len(simplified)} incoming records\n")

# List all case IDs with position
for i, rec in enumerate(simplified, 1):
    case_id = rec.get('case_id')
    doc_id = rec.get('doc_id')
    if case_id == '93159':
        print(f"✅ Found at position {i}")
        print(f"   Case ID: {case_id}")
        print(f"   Doc ID: {doc_id}")
        print(f"   Party: {rec.get('party', 'N/A')}")
        break
else:
    print("Case 93159 not found in first 100 records")
    print(f"\nFirst 20 case IDs:")
    for i, rec in enumerate(simplified[:20], 1):
        print(f"  {i}. {rec.get('case_id')}")
