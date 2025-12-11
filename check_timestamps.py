#!/usr/bin/env python
import json
from pathlib import Path

files = sorted(Path('data/incoming_requests').glob('*.json'))
for f in files:
    data = json.load(open(f, encoding='utf-8'))
    generated_at = data.get('generated_at', 'N/A')
    print(f"{f.name}: {generated_at}")
