"""Debug case 93159 - charge not found."""
import sys
import os
sys.path.insert(0, 'src')

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from monitor import PKMMonitor
from utils import load_config
from charges import fetch_case_detail_payload, get_doc_id_from_w007_p_fld7, enrich_charge_with_employee
from incoming import simplify_incoming_records

def main():
    print("=" * 80)
    print("DEBUG: Case ID 93159 - Charge Not Found")
    print("=" * 80)
    print()
    
    # Load config and create monitor
    config = load_config('config/config.yaml')
    monitor = PKMMonitor(
        base_url=config['base_url'],
        urls=config['urls'],
        username=config['username'],
        password=config['password']
    )
    
    if not monitor.login():
        print("❌ Login failed")
        return
    
    print("✅ Login successful")
    print()
    
    # Fetch incoming records
    params = {'queryId': 6, 'limit': 100}  # More records to find case 93159
    incoming_data = monitor.fetch_data(params)
    incoming_records = incoming_data.get('data', []) if incoming_data else []
    simplified = simplify_incoming_records(incoming_records)
    
    print(f"📥 Fetched {len(simplified)} incoming records")
    print()
    
    # Find case (check multiple - prioritize 93159 which worked)
    test_case_ids = ['93159', '125695', '117649', '128916']
    target_case = None
    
    for case_id in test_case_ids:
        for rec in simplified:
            if rec.get('case_id') == case_id:
                target_case = rec
                break
        if target_case:
            break
    
    if not target_case:
        print(f"❌ None of test cases {test_case_ids} found in incoming records")
        print(f"Available case IDs: {[r.get('case_id') for r in simplified[:20]]}")
        return
    
    print(f"✅ Found Case ID: {target_case.get('case_id')}")
    print(f"   Doc ID: {target_case.get('doc_id')}")
    print(f"   Party: {target_case.get('party', 'N/A')}")
    print(f"   Type: {target_case.get('document_category', 'N/A')}")
    print(f"   Related Case: {target_case.get('related_case', 'N/A')}")
    print()
    
    doc_id = target_case.get('doc_id')
    if not doc_id:
        print("❌ No doc_id found in record")
        return
    
    print(f"🔍 Testing enrichment for doc_id: {doc_id}")
    print()
    
    # Step 1: Fetch case detail
    print("Step 1: Calling endpoint /7 with doc_id...")
    payload = fetch_case_detail_payload(monitor, doc_id)
    
    if not payload:
        print("❌ No payload returned from endpoint /7")
        return
    
    print(f"✅ Got payload: success={payload.get('success')}")
    
    # Check data structure
    data = payload.get('data')
    if isinstance(data, list):
        print(f"   Data: list with {len(data)} items")
        if data:
            print(f"   First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
            if isinstance(data[0], dict):
                w007_p_fld7 = data[0].get('W007_P_FLD7')
                if w007_p_fld7:
                    print(f"   W007_P_FLD7 type: {type(w007_p_fld7).__name__}")
                    if isinstance(w007_p_fld7, dict):
                        print(f"   W007_P_FLD7 keys: {list(w007_p_fld7.keys())}")
                        print(f"   W007_P_FLD7.docIds: {w007_p_fld7.get('docIds')}")
                    else:
                        print(f"   W007_P_FLD7 value: {w007_p_fld7}")
                else:
                    print("   ⚠️  No W007_P_FLD7 in data")
    elif isinstance(data, dict):
        print(f"   Data: dict with keys {list(data.keys())}")
    else:
        print(f"   Data: {type(data).__name__}")
    print()
    
    # Step 2: Extract charge DOCID
    print("Step 2: Extracting charge DOCID from W007_P_FLD7...")
    charge_doc_id = get_doc_id_from_w007_p_fld7(payload)
    
    if charge_doc_id:
        print(f"✅ Charge DOCID: {charge_doc_id}")
    else:
        print("❌ No charge DOCID found in W007_P_FLD7.docIds")
        return
    print()
    
    # Step 3: Enrich with employee
    print("Step 3: Getting employee via enrichment...")
    
    # Manually check endpoint /2 response
    from charges import fetch_ots_detail_payload, extract_field
    print(f"   Calling endpoint /2 with charge DOCID {charge_doc_id}...")
    
    ots_payload = fetch_ots_detail_payload(monitor, charge_doc_id)
    if ots_payload:
        print(f"   ✅ Got OTS payload: success={ots_payload.get('success')}")
        data = ots_payload.get('data')
        if isinstance(data, list):
            print(f"   Data: list with {len(data)} items")
            if data and isinstance(data[0], dict):
                record = data[0]
                print(f"   First item has {len(record)} fields")
                
                # Print ALL fields to find employee
                print()
                print("   ALL FIELDS:")
                for key in sorted(record.keys()):
                    val = record.get(key)
                    if isinstance(val, dict):
                        val_str = val.get('value', val.get('text', str(val)[:50]))
                    else:
                        val_str = str(val)[:80]
                    print(f"   - {key}: {val_str}")
                print()
                
                # Check for W001_P_FLD10
                if 'W001_P_FLD10' in record:
                    w001_p_fld10 = record.get('W001_P_FLD10')
                    print(f"   ✅ W001_P_FLD10 found: {w001_p_fld10}")
                else:
                    print(f"   ❌ W001_P_FLD10 NOT in data")
        elif isinstance(data, dict):
            print(f"   Data: dict with {len(data)} fields")
            if 'W001_P_FLD10' in data:
                print(f"   ✅ W001_P_FLD10 found: {data.get('W001_P_FLD10')}")
            else:
                print(f"   ❌ W001_P_FLD10 NOT in data")
                print(f"   Available fields: {list(data.keys())[:20]}")
    else:
        print(f"   ❌ No payload from endpoint /2")
    
    print()
    
    employee = enrich_charge_with_employee(monitor, doc_id)
    
    if employee:
        print(f"✅ Employee: {employee}")
    else:
        print("❌ No employee found")
    print()
    
    print("=" * 80)
    print("Debug Complete")
    print("=" * 80)

if __name__ == '__main__':
    main()
