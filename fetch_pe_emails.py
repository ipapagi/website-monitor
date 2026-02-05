#!/usr/bin/env python3
"""Fetch emails for each regional unit subdirectorate"""
import requests
import re
import json
from bs4 import BeautifulSoup

# Mapping of regional units to subdomain
PE_SUBDOMAINS = {
    'ΘΕΣΣΑΛΟΝΙΚΗΣ': 'thessaloniki',
    'ΧΑΛΚΙΔΙΚΗΣ': 'chalkidiki',
    'ΚΙΛΚΙΣ': 'kilkis',
    'ΠΕΛΛΑΣ': 'pella',
    'ΗΜΑΘΙΑΣ': 'imathia',
}

# URLs for each directorate per PE
base_urls = {
    'ΟΙΚΟΝΟΜΙΚΟ': {
        'ΘΕΣΣΑΛΟΝΙΚΗΣ': 'https://www.pkm.gov.gr/org_chart/dieythinsi-genikis-dieythynsis-dimosias-ygeias-kai-koinonikis-merimnas/dieythynsi-dimosias-ygeias-kai-koinonikis-merimnas-me-thessalonikis/',  # No subdirectorate, use main
        'ΧΑΛΚΙΔΙΚΗΣ': 'https://www.pkm.gov.gr/org_chart/geniki-dieythynsi-esoterikis-organosis-kai-leitoyrgias/dieythynsi-oikonomikoy-pkm/ypodieythynsi-oikonomikoy-anthropinon-poron-pe-chalkidikis/',
        'ΚΙΛΚΙΣ': 'https://www.pkm.gov.gr/org_chart/geniki-dieythynsi-esoterikis-organosis-kai-leitoyrgias/dieythynsi-oikonomikoy-pkm/ypodieythynsi-oikonomikoy-anthropinon-poron-pe-kilkis/',
        'ΠΕΛΛΑΣ': 'https://www.pkm.gov.gr/org_chart/geniki-dieythynsi-esoterikis-organosis-kai-leitoyrgias/dieythynsi-oikonomikoy-pkm/ypodieythynsi-oikonomikoy-anthropinon-poron-pe-pellas/',
        'ΗΜΑΘΙΑΣ': 'https://www.pkm.gov.gr/org_chart/geniki-dieythynsi-esoterikis-organosis-kai-leitoyrgias/dieythynsi-oikonomikoy-pkm/ypodieythynsi-oikonomikoy-anthropinon-poron-pe-imathias/',
    }
}

results = {}

for directorate, pe_urls in base_urls.items():
    results[directorate] = {}
    for pe, url in pe_urls.items():
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text(' ', strip=True)
            
            # Try pattern: "word στο domain.pkm.gov.gr"
            m = re.search(r'([a-z0-9._%+-]+)\s+στο\s+([a-z0-9.-]+\.pkm\.gov\.gr)', text, re.I)
            if m:
                email = f"{m.group(1)}@{m.group(2)}"
            else:
                # Try pattern: "word στο pkm.gov.gr"
                m2 = re.search(r'([a-z0-9._%+-]+)\s+στο\s+pkm\.gov\.gr', text, re.I)
                email = f"{m2.group(1)}@pkm.gov.gr" if m2 else "NOT FOUND"
            
            results[directorate][pe] = email
            print(f"{directorate} / Π.Ε. {pe}: {email}")
        except Exception as e:
            results[directorate][pe] = f"ERROR: {str(e)[:50]}"
            print(f"{directorate} / Π.Ε. {pe}: ERROR - {e}")

print("\n" + "="*60)
print(json.dumps(results, ensure_ascii=False, indent=2))
