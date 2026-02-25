#!/usr/bin/env python3
"""Show cases where USER_GROUP_ID_TO differs from USER_ID_FROM"""

import json

with open('data/outputs/queryid3_user_comparison_2026-02-16_150537.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('\n⚠️  ΠΕΡΙΠΤΩΣΕΙΣ ΔΙΑΦΟΡΕΤΙΚΩΝ ΧΡΗΣΤΩΝ:')
print('='*80)
different_cases = [d for d in data['details'] if not d['are_same']]
for i, case in enumerate(different_cases, 1):
    print(f'{i}. Υπόθεση: {case["pkm"]:>6}')
    print(f'   TO (ανατιθέμενος):    {case["user_to"]}')
    print(f'   FROM (προωθητής):     {case["user_from"]}')
    print()

print('='*80)
