"""
Export doc_id <-> case_id mapping from current incoming (queryId=6) to Excel.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from incoming import fetch_incoming_records, simplify_incoming_records


def main() -> None:
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

    params = config.get('incoming_api_params', INCOMING_DEFAULT_PARAMS).copy()
    data = fetch_incoming_records(monitor, params)
    if not data or not data.get('success'):
        print("❌ Failed to fetch incoming records")
        return

    records = simplify_incoming_records(data.get('data', []))
    print(f"✅ Found {len(records)} incoming records")

    try:
        from openpyxl import Workbook
    except Exception as exc:
        print(f"❌ openpyxl not available: {exc}")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "docid_caseid"

    headers = [
        "case_id",
        "doc_id",
        "submitted_at",
        "party",
        "directory",
        "procedure",
    ]
    ws.append(headers)

    for rec in records:
        ws.append([
            rec.get('case_id', ''),
            rec.get('doc_id', ''),
            rec.get('submitted_at', ''),
            rec.get('party', ''),
            rec.get('directory', ''),
            rec.get('procedure', ''),
        ])

    out_dir = os.path.join(root, 'data', 'outputs')
    os.makedirs(out_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    out_path = os.path.join(out_dir, f"docid_caseid_map_{date_str}.xlsx")
    wb.save(out_path)
    print(f"✅ Saved: {out_path}")


if __name__ == '__main__':
    main()
