"""
Test script: Lookup OTS assignments by opening each OTS case (detail endpoint).
Uses /services/DataServices/fetchDataTableRecord/2/{doc_id}.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root
from charges import fetch_charges, get_employee_from_ots_detail


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Lookup OTS assignments via detail endpoint")
    parser.add_argument('--ids', required=True, help='Comma list or range, e.g. 105139,105673 or 105100-105110')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay in seconds between detail requests')
    args = parser.parse_args()

    targets = _parse_ids(args.ids)
    if not targets:
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
    print("📋 Fetching OTS records (queryId=2)...")
    ots_records, ots_by_pkm = fetch_charges(monitor)
    print(f"✅ Found {len(ots_records)} OTS records\n")

    for idx, target in enumerate(targets, 1):
        if idx > 1:
            time.sleep(args.delay)

        print("=" * 70)
        print(f"[{idx}/{len(targets)}] Case ID: {target}")

        ots_rec = ots_by_pkm.get(target)
        if not ots_rec:
            print("- OTS list match: NO")
            continue

        doc_id = str(ots_rec.get('DOCID', '')).strip()
        print(f"- OTS list match: YES (DOCID: {doc_id})")

        if not doc_id:
            print("- Detail lookup: SKIP (missing doc_id)")
            continue

        employee = get_employee_from_ots_detail(monitor, doc_id)
        if employee:
            print(f"- Detail assignment (W001_P_FLD10): {employee}")
        else:
            print("- Detail assignment (W001_P_FLD10): NOT FOUND")

    print("=" * 70)
    print("✅ Done")


if __name__ == '__main__':
    main()
