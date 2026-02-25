"""
Test script: Check specific case_id/PKM values against OTS charges (queryId=2)
and incoming records (queryId=6), with delay between checks.
"""
import argparse
import html
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from incoming import fetch_incoming_records, simplify_incoming_records
from charges import get_employee_from_charge


def _parse_ids(raw: str) -> list[str]:
    ids = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            start_str, end_str = part.split('-', 1)
            start = int(start_str.strip())
            end = int(end_str.strip())
            for val in range(start, end + 1):
                ids.append(str(val))
        else:
            ids.append(part)
    return ids


def _parse_query_ids(raw: str) -> list[str]:
    ids = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            start_str, end_str = part.split('-', 1)
            start = int(start_str.strip())
            end = int(end_str.strip())
            for val in range(start, end + 1):
                ids.append(str(val))
        else:
            ids.append(part)
    return ids


def _find_matches(records: list[dict], target: str) -> list[dict]:
    matches = []
    for rec in records:
        description = html.unescape(rec.get('DESCRIPTION', '') or '')
        fields = [
            str(rec.get('W007_P_FLD21', '') or '').strip(),
            str(rec.get('W001_P_FLD1', '') or '').strip(),
            str(rec.get('case_id', '') or '').strip(),
            description,
        ]
        if any(target and target in f for f in fields):
            matches.append(rec)
    return matches


def main() -> None:
    parser = argparse.ArgumentParser(description="Check case_id/PKM values with delay")
    parser.add_argument('--ids', required=True, help='Comma list or range, e.g. 105139,105673 or 105100-105110')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay in seconds between checks')
    parser.add_argument('--query-ids', default='2', help='QueryId list/range, e.g. 2,6,19 or 10-20')
    args = parser.parse_args()

    ids = _parse_ids(args.ids)
    if not ids:
        print("❌ No IDs provided")
        return

    root = get_project_root()
    cfg_path = os.path.join(root, 'config', 'config.yaml')
    config = load_config(cfg_path)

    monitor = PKMMonitor(
        base_url=config.get('base_url', 'https://shde.pkm.gov.gr'),
        urls=config.get('urls', {}),
        api_params=config.get('api_params', {}),
        login_params=config.get('login_params', {}),
        check_interval=config.get('check_interval', 300),
        username=config.get('username'),
        password=config.get('password'),
        session_cookies=config.get('session_cookies')
    )

    print("🔐 Login...")
    if not monitor.logged_in and not monitor.login():
        print("❌ Login failed")
        return

    print("✅ Logged in")
    print("📨 Fetching incoming records (queryId=6)...")
    params = config.get('incoming_api_params', INCOMING_DEFAULT_PARAMS).copy()
    data = fetch_incoming_records(monitor, params)
    incoming_records = simplify_incoming_records(data.get('data', [])) if data and data.get('success') else []
    incoming_set = {str(r.get('case_id', '')).strip() for r in incoming_records}
    print(f"✅ Found {len(incoming_records)} incoming records\n")

    query_ids = _parse_query_ids(args.query_ids)
    if not query_ids:
        print("❌ No queryIds provided")
        return

    for idx, target in enumerate(ids, 1):
        if idx > 1:
            time.sleep(args.delay)

        print("=" * 70)
        print(f"[{idx}/{len(ids)}] Case ID: {target}")

        in_incoming = target in incoming_set
        print(f"- Incoming (queryId=6): {'YES' if in_incoming else 'NO'}")

        for qidx, query_id in enumerate(query_ids, 1):
            if qidx > 1:
                time.sleep(args.delay)

            params = {
                'queryId': query_id,
                'queryOwner': '2',
                'isCase': 'false',
                'stateId': 'welcomeGrid-45_dashboard0',
                'page': '1',
                'start': '0',
                'limit': '100',
                'isPoll': 'true',
            }
            data = monitor.fetch_data(params)
            records = data.get('data', []) if data and data.get('success') else []

            matches = _find_matches(records, target)
            if matches:
                first = matches[0]
                employee = get_employee_from_charge(first) or 'N/A'
                description = html.unescape(first.get('DESCRIPTION', '') or '')
                print(f"- queryId={query_id}: YES ({len(matches)} match(es))")
                print(f"  Employee (W001_P_FLD10): {employee}")
                if description:
                    print(f"  DESCRIPTION: {description[:120]}...")
            else:
                print(f"- queryId={query_id}: NO")

    print("=" * 70)
    print("✅ Done")


if __name__ == '__main__':
    main()
