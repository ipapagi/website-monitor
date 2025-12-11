#!/usr/bin/env python
import json
import os
from pathlib import Path

incoming_dir = Path('data/incoming_requests')

for f in sorted(incoming_dir.glob('*.json')):
    try:
        with open(f, encoding='utf-8') as fp:
            data = json.load(fp)
        recs = [r for r in data['records'] if r.get('case_id') == '923034']
        if recs:
            rec = recs[0]
            protocol = rec.get('protocol_number', '')
            procedure = rec.get('procedure', '')
            directory = rec.get('directory', '')
            print(f"{f.name}: protocol='{protocol}', procedure='{procedure}', directory='{directory}'")
    except Exception as e:
        pass
