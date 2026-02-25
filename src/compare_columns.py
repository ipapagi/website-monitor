"""Σύγκριση πεδίων (columns) μεταξύ των δύο endpoints."""
import json
import os
from datetime import datetime

from session import PKMSession
from config import INCOMING_DEFAULT_PARAMS, SETTLED_CASES_DEFAULT_PARAMS

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'data', 'tmp'))
os.makedirs(OUT_DIR, exist_ok=True)

load_dotenv()
USERNAME = os.getenv('PKM_USERNAME', '')
PASSWORD = os.getenv('PKM_PASSWORD', '')


def _column_key(col):
    if isinstance(col, dict):
        return col.get('dataIndex') or col.get('name') or col.get('id')
    return str(col)


def _column_label(col):
    if isinstance(col, dict):
        return col.get('header') or col.get('text') or col.get('label') or ''
    return ''


def _column_type(col):
    if isinstance(col, dict):
        return col.get('type') or col.get('xtype') or ''
    return ''


def _write_json(filename, payload):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def _print_columns(columns):
    print("\n📋 Ονομασίες πεδίων (columns):")
    print("-" * 40)
    for i, col in enumerate(columns, 1):
        if i == 1 and isinstance(col, dict):
            print(f"   (keys: {', '.join(col.keys())})")
        field_name = _column_key(col) or 'N/A'
        field_label = _column_label(col)
        field_type = _column_type(col)
        print(f"{i:2}. {field_name:30} | Label: {field_label:20} | Type: {field_type}")


def _fetch_and_dump(session, label, params, prefix):
    print(f"\n{label}")
    print("-" * 80)

    data = session.fetch_data(params)
    if not data or not data.get('success'):
        print("❌ Αποτυχία")
        if data:
            _write_json(f"{prefix}_raw.json", data)
        return []

    metadata = data.get('metaData', {})
    columns = metadata.get('columns', [])
    total = data.get('total', 0)

    print(f"✅ Success: Σύνολο εγγραφών: {total}")
    print(f"📊 Αριθμός στηλών: {len(columns)}")

    if not columns:
        print("\n⚠️ Δεν υπάρχουν columns. metaData keys:")
        for key in metadata.keys():
            print(f"   • {key}")
        _write_json(f"{prefix}_metadata.json", metadata)
        if data.get('data'):
            _write_json(f"{prefix}_sample.json", data['data'][0])
        _write_json(f"{prefix}_raw.json", data)
        print(f"\n✅ Αποθηκεύθηκαν σε {OUT_DIR}\\{prefix}_metadata.json και {OUT_DIR}\\{prefix}_sample.json")
        return []

    _print_columns(columns)

    _write_json(f"{prefix}_columns.json", {
        'endpoint': label,
        'columns': columns,
        'fetched_at': datetime.now().isoformat()
    })
    print(f"\n✅ Αποθηκεύθηκαν σε {OUT_DIR}\\{prefix}_columns.json")
    return columns


def get_columns_comparison():
    print("\n" + "=" * 80)
    print("🔍 ΣΥΓΚΡΙΣΗ ΠΕΔΙΩΝ: Εισερχόμενες vs Διεκπεραιωμένες")
    print("=" * 80)

    session = PKMSession(
        base_url="https://shde.pkm.gov.gr",
        urls={
            'login_page': '/login.jsp',
            'login_api': '/services/LoginServices/loginWeb',
            'main_page': '/ext_main.jsp?locale=el',
            'data_api': '/services/SearchServices/getSearchDataByQueryId'
        },
        login_params={
            'application': '2',
            'otp': ''
        },
        username=USERNAME,
        password=PASSWORD
    )

    params_incoming = INCOMING_DEFAULT_PARAMS.copy()
    params_incoming['limit'] = 5
    incoming_columns = _fetch_and_dump(
        session,
        "📥 ΕΙΣΕΡΧΟΜΕΝΕΣ ΑΙΤΗΣΕΙΣ (queryId=6)",
        params_incoming,
        'incoming'
    )

    params_settled = SETTLED_CASES_DEFAULT_PARAMS.copy()
    params_settled['limit'] = 5
    settled_columns = _fetch_and_dump(
        session,
        "📋 ΔΙΕΚΠΕΡΑΙΩΜΕΝΕΣ ΥΠΟΘΕΣΕΙΣ (queryId=19)",
        params_settled,
        'settled'
    )

    # Δημιουργία mapping label -> field name
    incoming_labels = {}
    for col in incoming_columns:
        label = _column_label(col)
        key = _column_key(col)
        if label and key:
            incoming_labels[label] = key
    
    settled_labels = {}
    for col in settled_columns:
        label = _column_label(col)
        key = _column_key(col)
        if label and key:
            settled_labels[label] = key

    print("\n\n" + "=" * 80)
    print("🔄 ΣΥΓΚΡΙΣΗ ΠΕΔΙΩΝ (με βάση Label/Λειτουργικότητα)")
    print("=" * 80)

    incoming_label_set = set(incoming_labels.keys())
    settled_label_set = set(settled_labels.keys())
    
    common = incoming_label_set & settled_label_set
    only_incoming = incoming_label_set - settled_label_set
    only_settled = settled_label_set - incoming_label_set

    print(f"\n✅ Κοινά πεδία ({len(common)}):")
    for label in sorted(common):
        inc_field = incoming_labels[label]
        set_field = settled_labels[label]
        print(f"   • {label:30} | Εισερχ: {inc_field:15} | Διεκπερ: {set_field}")

    print(f"\n📥 Μόνο σε Εισερχόμενες ({len(only_incoming)}):")
    for label in sorted(only_incoming):
        field = incoming_labels[label]
        print(f"   • {label:30} | {field}")

    print(f"\n📋 Μόνο σε Διεκπεραιωμένες ({len(only_settled)}):")
    for label in sorted(only_settled):
        field = settled_labels[label]
        print(f"   • {label:30} | {field}")


if __name__ == '__main__':
    get_columns_comparison()
