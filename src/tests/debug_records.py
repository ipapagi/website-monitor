import json
from src.incoming import simplify_incoming_records
from src.config import get_project_root
import os

resp_file = os.path.join(get_project_root(), 'api_response.json')
with open(resp_file, 'r', encoding='utf-8') as f:
    api_data = json.load(f)

records = simplify_incoming_records(api_data.get('data', []))
if records:
    rec = records[0]
    print('First record from simplify:')
    print(f'  case_id: {rec.get("case_id")}')
    print(f'  directory: {rec.get("directory")}')
    print(f'  procedure: {rec.get("procedure")}')
    print(f'  protocol_number: {rec.get("protocol_number")}')
    print(f'  protocol_date: {rec.get("protocol_date")}')
    print(f'  general_directorate: {rec.get("general_directorate")}')
    print(f'  department: {rec.get("department")}')
