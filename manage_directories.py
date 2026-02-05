#!/usr/bin/env python3
"""Utility για διαχείριση της διαμόρφωσης Διευθύνσεων και Π.Ε.
Παράδειγμα χρήσης:
  python manage_directories.py --export-csv
  python manage_directories.py --export-excel
  python manage_directories.py --find-email "ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ" "Π.Ε. ΘΕΣΣΑΛΟΝΙΚΗΣ"
"""
import sys
import os
import csv
import argparse
import json
import re
import unicodedata
import time
from urllib.parse import urljoin
from datetime import datetime

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from directories_manager import DirectoriesManager


def export_csv(manager: DirectoriesManager, output_file: str = None):
    """Εξαγωγή σε CSV"""
    if output_file is None:
        output_file = os.path.join(os.path.dirname(__file__), 'data', 'directories_export.csv')
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    rows = manager.export_for_excel()
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Διεύθυνση', 'Σύντομο Όνομα', 'Περιφερειακή Ενότητα', 
            'Email', 'Τηλέφωνο', 'Υπεύθυνος'
        ])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Εξαγωγή σε CSV: {output_file}")
    print(f"   Σύνολο σειρών: {len(rows)}")


def export_json_pretty(manager: DirectoriesManager, output_file: str = None):
    """Εξαγωγή σε formatted JSON"""
    if output_file is None:
        output_file = os.path.join(os.path.dirname(__file__), 'data', 'directories_export.json')
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(manager.config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Εξαγωγή σε JSON: {output_file}")


def _normalize_text(text: str) -> str:
    """Κανονικοποίηση κειμένου (αφαιρεί τόνους, lower)"""
    if not text:
        return ''
    normalized = unicodedata.normalize('NFD', text)
    normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return normalized.lower().strip()


def _extract_email_from_text(text: str) -> str | None:
    """Εξαγωγή email από κείμενο τύπου 'ddiaf στο pkm.gov.gr' ή 'srokanas στο halkidiki.gov.gr'"""
    if not text:
        return None

    patterns = [
        r'([a-z0-9._%+-]+)\s+στο\s+([a-z0-9.-]+\.gov\.gr)',
        r'([a-z0-9._%+-]+)@([a-z0-9.-]+\.gov\.gr)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return f"{match.group(1)}@{match.group(2)}".lower()

    return None


def _normalize_ru_name(ru_name: str) -> str:
    """Κανονικοποίηση ονόματος Π.Ε. (π.χ. 'Π.Ε. ΧΑΛΚΙΔΙΚΗΣ' -> 'χαλκιδικης')."""
    base = ru_name.replace('Π.Ε.', '').replace('ΠΕ', '').strip()
    return _normalize_text(base)


def _get_directory_keywords(directory_name: str) -> list[str]:
    """Επιστρέφει πιο αυστηρές φράσεις για αντιστοίχιση."""
    normalized = _normalize_text(directory_name)
    if 'οικονομικου' in normalized:
        return ['διευθυνση οικονομικου', 'υποδιευθυνση οικονομικου']
    if 'αναπτυξης' in normalized or 'περιβαλλοντος' in normalized:
        return ['διευθυνση αναπτυξης', 'αναπτυξης και περιβαλλοντος']
    if 'δημοσιας' in normalized or 'υγειας' in normalized:
        return ['διευθυνση δημοσιας υγειας', 'υγειας και κοινωνικης μεριμνας']
    if 'ανθρωπινου δυναμικου' in normalized or 'ποιοτητας' in normalized:
        return ['διευθυνση ανθρωπινου δυναμικου', 'διαχειρισης ποιοτητας', 'διοικητικης υποστηριξης']
    if 'πολιτικης προστασιας' in normalized:
        return ['διευθυνση πολιτικης προστασιας', 'τμημα πολιτικης προστασιας']
    return [token for token in normalized.split() if len(token) > 4]


def _page_matches_directory_and_ru(
    page_text: str,
    keywords: list[str],
    ru_key: str,
    ru_required: bool = True
) -> bool:
    """Έλεγχος αν το κείμενο ταιριάζει με Διεύθυνση και Π.Ε."""
    normalized = _normalize_text(page_text)
    if ru_required and ru_key and ru_key not in normalized:
        return False
    return any(keyword in normalized for keyword in keywords)


def _get_org_chart_links(base_url: str) -> list[tuple[str, str]]:
    """Φέρνει links από το οργανόγραμμα"""
    resp = requests.get(base_url, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/org_chart/' not in href:
            continue
        text = a.get_text(' ', strip=True)
        if not text:
            continue
        url = urljoin(base_url, href)
        links.append((text, url))

    # Deduplicate by url while preserving order
    seen = set()
    unique = []
    for text, url in links:
        if url in seen:
            continue
        seen.add(url)
        unique.append((text, url))
    return unique


def _find_best_link(directory_name: str, links: list[tuple[str, str]]) -> str | None:
    """Βρίσκει το καλύτερο link από το οργανόγραμμα για τη Διεύθυνση"""
    norm_dir = _normalize_text(directory_name)
    best_url = None
    best_score = 0

    for text, url in links:
        norm_text = _normalize_text(text)
        if not norm_text:
            continue
        if norm_dir in norm_text or norm_text in norm_dir:
            score = len(norm_text)
            if score > best_score:
                best_score = score
                best_url = url

    return best_url


def _fetch_email_from_org_chart(url: str) -> str | None:
    """Εξάγει email από σελίδα οργανωγράμματος"""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')
    text = soup.get_text(' ', strip=True)
    return _extract_email_from_text(text)


def _save_config(config: dict, config_file: str) -> None:
    """Αποθηκεύει το config στο αρχείο"""
    config['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def auto_fill_emails_from_org_chart(
    manager: DirectoriesManager,
    base_url: str,
    dry_run: bool = False,
    overwrite: bool = False
):
    """Αυτόματη συμπλήρωση emails από το οργανόγραμμα"""
    links = _get_org_chart_links(base_url)
    updated = 0

    for directory in manager.get_all_directories():
        dir_name = (directory.get('name') or '').strip()
        if not dir_name:
            continue

        org_chart_url = (directory.get('org_chart_url') or '').strip()
        if not org_chart_url:
            org_chart_url = _find_best_link(dir_name, links)
            if org_chart_url:
                directory['org_chart_url'] = org_chart_url
                print(f"🔗 Βρέθηκε link για {dir_name}: {org_chart_url}")
            else:
                print(f"⚠️  Δεν βρέθηκε link για {dir_name}")
                continue

        email = _fetch_email_from_org_chart(org_chart_url)
        if not email:
            print(f"⚠️  Δεν βρέθηκε email στη σελίδα: {org_chart_url}")
            continue

        filled = 0
        for ru in directory.get('regional_units', []):
            existing = (ru.get('email') or '').strip()
            if existing and not overwrite:
                continue
            ru['email'] = email
            filled += 1

        if filled > 0:
            updated += filled
            print(f"✅ {dir_name}: {email} (συμπληρώθηκαν {filled})")

    if dry_run:
        print("ℹ️  Dry run: δεν έγινε αποθήκευση.")
        return updated

    if updated > 0:
        _save_config(manager.config, manager.config_file)
        print(f"💾 Αποθηκεύτηκε: {manager.config_file}")
    else:
        print("ℹ️  Δεν έγιναν αλλαγές.")

    return updated


def auto_fill_emails_from_org_chart_deep(
    manager: DirectoriesManager,
    base_url: str,
    dry_run: bool = False,
    overwrite: bool = False,
    max_pages: int | None = None,
    clear_before: bool = False
):
    """Αυτόματη συμπλήρωση emails με deep crawl ανά Π.Ε. και Διεύθυνση."""
    links = _get_org_chart_links(base_url)
    urls = [url for _, url in links]
    if max_pages:
        urls = urls[:max_pages]

    updated = 0

    if overwrite and clear_before:
        for directory in manager.get_all_directories():
            for ru in directory.get('regional_units', []):
                ru['email'] = ''

    for directory in manager.get_all_directories():
        dir_name = (directory.get('name') or '').strip()
        if not dir_name:
            continue

        keywords = _get_directory_keywords(dir_name)

        for ru in directory.get('regional_units', []):
            ru_name = (ru.get('name') or '').strip()
            ru_key = _normalize_ru_name(ru_name)
            ru_required = ru_key != 'θεσσαλονικης'

            if not ru_name:
                continue

            existing = (ru.get('email') or '').strip()
            if existing and not overwrite:
                continue

            candidate_urls = []
            for text, url in links:
                norm_text = _normalize_text(text)
                if not ru_key or ru_key not in norm_text:
                    continue
                if any(keyword in norm_text for keyword in keywords):
                    candidate_urls.append(url)

            if not candidate_urls:
                org_chart_url = (directory.get('org_chart_url') or '').strip()
                if not ru_required and org_chart_url:
                    candidate_urls = [org_chart_url]
                else:
                    candidate_urls = urls

            found_email = None
            for url in candidate_urls:
                try:
                    resp = requests.get(url, timeout=30)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    page_text = soup.get_text(' ', strip=True)

                    if not _page_matches_directory_and_ru(page_text, keywords, ru_key, ru_required=ru_required):
                        continue

                    email = _extract_email_from_text(page_text)
                    if email:
                        found_email = email
                        break
                except Exception:
                    continue
                finally:
                    time.sleep(0.2)

            if found_email:
                ru['email'] = found_email
                updated += 1
                print(f"✅ {dir_name} / {ru_name}: {found_email}")
            else:
                print(f"⚠️  Δεν βρέθηκε email για {dir_name} / {ru_name}")

    if dry_run:
        print("ℹ️  Dry run: δεν έγινε αποθήκευση.")
        return updated

    if updated > 0:
        _save_config(manager.config, manager.config_file)
        print(f"💾 Αποθηκεύτηκε: {manager.config_file}")
    else:
        print("ℹ️  Δεν έγιναν αλλαγές.")

    return updated


def find_email(manager: DirectoriesManager, directory: str = None, regional_unit: str = None):
    """Αναζήτηση email"""
    if directory and regional_unit:
        email = manager.get_email_for_directory_and_regional_unit(directory, regional_unit)
        if email:
            print(f"✅ Email βρέθηκε:")
            print(f"   Διεύθυνση: {directory}")
            print(f"   Π.Ε.: {regional_unit}")
            print(f"   Email: {email}")
        else:
            print(f"❌ Δεν βρέθηκε email για {directory} / {regional_unit}")
    elif directory:
        dir_info = manager.get_directory_info_by_name(directory)
        if dir_info:
            print(f"✅ Πληροφορίες Διεύθυνσης: {directory}")
            for ru in dir_info.get('regional_units', []):
                print(f"   - {ru.get('name')}: {ru.get('email')}")
        else:
            print(f"❌ Δεν βρέθηκε Διεύθυνση: {directory}")
    else:
        # Εμφάνιση όλων
        print("📋 Όλες οι Διευθύνσεις:\n")
        for directory in manager.get_all_directories():
            dir_name = directory.get('name', '')
            print(f"🏢 {dir_name}")
            for ru in directory.get('regional_units', []):
                print(f"   ├─ {ru.get('name')}: {ru.get('email')}")
            print()


def list_regional_units(manager: DirectoriesManager):
    """Εμφάνιση όλων των Π.Ε."""
    print("📍 Περιφερειακές Ενότητες:\n")
    for ru_name, ru_data in manager.get_all_regional_units().items():
        print(f"  {ru_name}")
        print(f"    Email: {ru_data.get('email')}")
        print(f"    Τηλέφωνο: {ru_data.get('phone')}")
        print()


def validate_config(manager: DirectoriesManager):
    """Επαλήθευση διαμόρφωσης"""
    print("🔍 Επαλήθευση διαμόρφωσης...\n")
    
    errors = []
    warnings = []
    
    # Έλεγχος Διευθύνσεων
    directories = manager.get_all_directories()
    print(f"📊 Σύνολο Διευθύνσεων: {len(directories)}")
    
    for directory in directories:
        dir_name = directory.get('name', '')
        if not dir_name:
            errors.append("Διεύθυνση χωρίς όνομα")
        
        rus = directory.get('regional_units', [])
        print(f"  - {dir_name}: {len(rus)} Π.Ε.")
        
        for ru in rus:
            ru_name = ru.get('name', '')
            email = ru.get('email', '').strip()
            
            if not ru_name:
                errors.append(f"Π.Ε. χωρίς όνομα σε {dir_name}")
            
            if not email:
                warnings.append(f"Π.Ε. '{ru_name}' χωρίς email σε {dir_name}")
            elif '@' not in email:
                errors.append(f"Π.Ε. '{ru_name}': Invalid email format '{email}'")
    
    # Έλεγχος Π.Ε.
    rus_map = manager.get_all_regional_units()
    print(f"\n📍 Σύνολο Π.Ε. (map): {len(rus_map)}")
    
    for ru_name, ru_data in rus_map.items():
        email = ru_data.get('email', '').strip()
        if not email:
            warnings.append(f"Π.Ε. '{ru_name}' στο map χωρίς email")
    
    # Αποτελέσματα
    print("\n" + "="*60)
    if errors:
        print(f"❌ Σφάλματα: {len(errors)}")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Δεν βρέθηκαν σφάλματα")
    
    if warnings:
        print(f"\n⚠️  Προειδοποιήσεις: {len(warnings)}")
        for warning in warnings:
            print(f"   - {warning}")
    else:
        print("\n✅ Δεν βρέθηκαν προειδοποιήσεις")
    
    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(
        description='Διαχείριση Διευθύνσεων και Περιφερειακών Ενοτήτων'
    )
    parser.add_argument('--export-csv', action='store_true', help='Εξαγωγή σε CSV')
    parser.add_argument('--export-json', action='store_true', help='Εξαγωγή σε JSON')
    parser.add_argument('--list-directories', action='store_true', help='Εμφάνιση όλων των Διευθύνσεων')
    parser.add_argument('--list-regional-units', action='store_true', help='Εμφάνιση όλων των Π.Ε.')
    parser.add_argument('--find-email', nargs='*', help='Αναζήτηση email [Διεύθυνση] [Π.Ε.]')
    parser.add_argument('--validate', action='store_true', help='Επαλήθευση διαμόρφωσης')
    parser.add_argument('--auto-fill-emails-from-org-chart', action='store_true',
                        help='Αυτόματη συμπλήρωση emails από το οργανόγραμμα')
    parser.add_argument('--auto-fill-emails-from-org-chart-deep', action='store_true',
                        help='Deep crawl ανά Π.Ε. για εύρεση email')
    parser.add_argument('--org-chart-base', default='https://www.pkm.gov.gr/org_chart/',
                        help='Βασικό URL οργανωγράμματος')
    parser.add_argument('--dry-run', action='store_true',
                        help='Εκτέλεση χωρίς αποθήκευση αλλαγών')
    parser.add_argument('--overwrite', action='store_true',
                        help='Αντικατάσταση υπαρχόντων emails')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='Μέγιστος αριθμός σελίδων για deep crawl')
    parser.add_argument('--clear-before', action='store_true',
                        help='Καθαρισμός emails πριν το deep crawl')
    parser.add_argument('--config', default=None, help='Διαδρομή config file')
    
    args = parser.parse_args()
    
    manager = DirectoriesManager(args.config)
    
    if args.export_csv:
        export_csv(manager)
    elif args.export_json:
        export_json_pretty(manager)
    elif args.list_directories or args.list_regional_units:
        if args.list_directories or not any([args.list_regional_units, args.find_email]):
            find_email(manager)
        if args.list_regional_units:
            list_regional_units(manager)
    elif args.find_email is not None:
        if len(args.find_email) == 0:
            find_email(manager)
        elif len(args.find_email) == 1:
            find_email(manager, directory=args.find_email[0])
        else:
            find_email(manager, directory=args.find_email[0], regional_unit=args.find_email[1])
    elif args.validate:
        validate_config(manager)
    elif args.auto_fill_emails_from_org_chart:
        auto_fill_emails_from_org_chart(
            manager,
            base_url=args.org_chart_base,
            dry_run=args.dry_run,
            overwrite=args.overwrite
        )
    elif args.auto_fill_emails_from_org_chart_deep:
        auto_fill_emails_from_org_chart_deep(
            manager,
            base_url=args.org_chart_base,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
            max_pages=args.max_pages,
            clear_before=args.clear_before
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
