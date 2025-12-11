"""Δημιουργία και αποστολή ημερήσιου email αναφοράς"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from baseline import (
    load_baseline,
    load_all_procedures_baseline,
    compare_with_baseline,
    compare_all_procedures_with_baseline,
)
from incoming import (
    simplify_incoming_records,
    load_previous_incoming_snapshot,
    load_incoming_snapshot,
    save_incoming_snapshot,
    fetch_incoming_records,
    compare_incoming_records,
    merge_with_previous_snapshot,
)
from test_users import classify_records, get_record_stats
from email_notifier import EmailNotifier
from report_display import print_full_digest

load_dotenv()


def _ensure_logged_in(monitor: PKMMonitor):
    """Κάνει login και φορτώνει αρχική σελίδα αν χρειάζεται"""
    if not monitor.logged_in and not monitor.login():
        raise RuntimeError("Αποτυχία login")
    if not monitor.main_page_loaded:
        monitor.load_main_page()


def _fetch_procedures(monitor: PKMMonitor):
    """Επιστρέφει all/active procedures από το API"""
    data = monitor.fetch_page()
    if not data or not data.get("success"):
        raise RuntimeError("Αποτυχία ανάκτησης δεδομένων διαδικασιών")
    all_procs = monitor.parse_table_data(data)
    active_procs = [p for p in all_procs if p.get("ενεργή") == "ΝΑΙ"]
    return all_procs, active_procs


def _prepare_incoming(monitor: PKMMonitor, config: dict):
    """Φέρνει εισερχόμενες αιτήσεις, συγκρίνει με προηγούμενο snapshot και αποθηκεύει το σημερινό."""
    incoming_params = config.get("incoming_api_params", INCOMING_DEFAULT_PARAMS).copy()
    data = fetch_incoming_records(monitor, incoming_params)
    if not data or not data.get("success"):
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reference_date": None,
            "records": [],
            "changes": {"new": [], "removed": [], "modified": []},
            "real_new": [],
            "test_new": [],
            "stats": {"total": 0, "real": 0, "test": 0, "test_breakdown": {}},
        }

    records = simplify_incoming_records(data.get("data", []))
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Έλεγχος αν υπάρχει forced baseline ημερομηνία στο .env
    force_baseline_date = os.getenv("INCOMING_FORCE_BASELINE_DATE")
    if force_baseline_date:
        print(f"ℹ️  Χρήση αναγκαστικής ημερομηνίας baseline: {force_baseline_date}")
        forced_snap = load_incoming_snapshot(force_baseline_date)
        if forced_snap:
            prev_date, prev_snap = force_baseline_date, forced_snap
            has_prev = True
        else:
            print(f"⚠️  Δεν βρέθηκε snapshot για {force_baseline_date}")
            prev_date, prev_snap = None, None
            has_prev = False
    else:
        # Κανονική ροή: ψάχνουμε προηγούμενο snapshot
        prev_date, prev_snap = load_previous_incoming_snapshot(today)
        has_prev = prev_snap is not None

        # Αν δεν υπάρχει προηγούμενο snapshot, ψάχνουμε fallback ημερομηνία από .env
        if not has_prev:
            fallback_date = os.getenv("INCOMING_BASELINE_DATE")
            if fallback_date:
                fallback_snap = load_incoming_snapshot(fallback_date)
                if fallback_snap:
                    prev_date, prev_snap = fallback_date, fallback_snap
                    has_prev = True

    if has_prev:
        records = merge_with_previous_snapshot(records, prev_snap)
    else:
        # Αν δεν υπάρχει προηγούμενο, μήνυμα baseline: θα θεωρηθεί baseline χωρίς αλλαγές
        prev_snap = {"records": []}

    changes = compare_incoming_records(records, prev_snap)
    real_new, test_new = classify_records(changes.get("new", []))
    stats = get_record_stats(records)

    # Αποθήκευση snapshot για το επόμενο run
    save_incoming_snapshot(today, records)

    return {
        "date": today,
        "reference_date": prev_date,
        "records": records,
        "changes": changes,
        "real_new": real_new,
        "test_new": test_new,
        "stats": stats,
    }


def build_daily_digest(config_path: str | None = None) -> dict:
    """Συγκεντρώνει όλα τα δεδομένα για την ημερήσια αναφορά."""
    root = get_project_root()
    cfg_path = config_path or os.path.join(root, "config", "config.yaml")
    config = load_config(cfg_path)

    monitor = PKMMonitor(
        base_url=config.get("base_url", "https://shde.pkm.gov.gr"),
        urls=config.get("urls", {}),
        api_params=config.get("api_params", {}),
        login_params=config.get("login_params", {}),
        check_interval=config.get("check_interval", 300),
        username=config.get("username"),
        password=config.get("password"),
        session_cookies=config.get("session_cookies"),
    )

    _ensure_logged_in(monitor)
    all_procs, active_procs = _fetch_procedures(monitor)

    active_bl = load_baseline()
    all_bl = load_all_procedures_baseline()

    active_changes = compare_with_baseline(all_procs, active_bl) if active_bl else None
    all_changes = compare_all_procedures_with_baseline(all_procs, all_bl) if all_bl else None

    incoming_data = _prepare_incoming(monitor, config)

    digest = {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "base_url": monitor.base_url,
        "active": {
            "total": len(active_procs),
            "baseline_timestamp": active_bl.get("timestamp") if active_bl else None,
            "changes": active_changes,
        },
        "all": {
            "total": len(all_procs),
            "baseline_timestamp": all_bl.get("timestamp") if all_bl else None,
            "changes": all_changes,
        },
        "incoming": incoming_data,
    }
    return digest


def send_daily_email(config_path: str | None = None) -> bool:
    """Δημιουργεί και στέλνει το ημερήσιο email."""
    digest = build_daily_digest(config_path)
    
    # Εμφάνιση στο terminal
    print_full_digest(digest)
    
    # Αποστολή email
    notifier = EmailNotifier()
    if not notifier.is_enabled():
        raise RuntimeError("Email notifications are disabled")
    notifier.send_daily_digest(digest)
    return True


if __name__ == "__main__":
    try:
        send_daily_email()
        print("✅ Ημερήσιο email εστάλη επιτυχώς")
    except Exception as exc:  # pragma: no cover - manual run helper
        print(f"❌ Αποτυχία αποστολής ημερήσιου email: {exc}")
        sys.exit(1)