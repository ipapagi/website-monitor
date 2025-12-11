"""Εμφάνιση ημερήσιας αναφοράς στο terminal"""
from datetime import datetime
from formatters import format_incoming_record_text


def print_digest_header(digest: dict):
    """Εμφανίζει τα headers της αναφοράς"""
    print("\n" + "=" * 100)
    print("ΗΜΕΡΗΣΙΑ ΑΝΑΦΟΡΑ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ".center(100))
    print("=" * 100)
    print(f"📅 Δημιουργία: {digest.get('generated_at', '')}")
    print(f"🌐 URL: {digest.get('base_url', '')}")
    print("=" * 100 + "\n")


def print_summary(digest: dict):
    """Εμφανίζει τη σύνοψη με κάρτες"""
    active_data = digest.get('active', {})
    all_data = digest.get('all', {})
    incoming_data = digest.get('incoming', {})
    
    active_changes = active_data.get('changes') or {}
    all_changes = all_data.get('changes') or {}
    incoming_changes = incoming_data.get('changes') or {}

    def count_changes(changes, key):
        return len(changes.get(key, [])) if changes else 0

    print("📊 ΣΥΝΟΨΗ")
    print("-" * 100)
    print(f"  Ενεργές διαδικασίες: {active_data.get('total', 0):4d}  │  "
          f"Σύνολο: {all_data.get('total', 0):4d}  │  "
          f"Αιτήσεις: {incoming_data.get('stats', {}).get('total', 0):4d}")
    print(f"  Νέες ενεργές: {count_changes(active_changes, 'new'):4d}  │  "
          f"Νέες σύνολο: {count_changes(all_changes, 'new'):4d}  │  "
          f"Πραγματικές/Δοκιμ.: {incoming_data.get('stats', {}).get('real', 0)}/{incoming_data.get('stats', {}).get('test', 0)}")
    print()


def print_active_changes(digest: dict):
    """Εμφανίζει αλλαγές ενεργών διαδικασιών"""
    active_data = digest.get('active', {})
    active_changes = active_data.get('changes')
    
    if not active_changes:
        return

    print("\n" + "=" * 100)
    print("✅ ΑΛΛΑΓΕΣ ΕΝΕΡΓΩΝ ΔΙΑΔΙΚΑΣΙΩΝ".center(100))
    print("=" * 100)
    print(f"Baseline: {active_data.get('baseline_timestamp', '—')}\n")

    has_changes = False
    for change_type, label, icon in [
        ('new', 'Νέες Ενεργές', '🆕'),
        ('activated', 'Ενεργοποιήθηκαν', '🔓'),
        ('deactivated', 'Απενεργοποιήθηκαν', '🔒'),
        ('removed', 'Αφαιρέθηκαν', '🗑️'),
        ('modified', 'Τροποποιήθηκαν', '📝'),
    ]:
        items = active_changes.get(change_type, [])
        if items:
            has_changes = True
            print(f"{icon} {label} ({len(items)})")
            print("-" * 100)
            for idx, item in enumerate(items, 1):
                proc = item.get('new', item) if isinstance(item, dict) and 'new' in item else item
                code = proc.get('κωδικός', '')[:15]
                title = proc.get('τίτλος', '')[:60]
                status = proc.get('ενεργή', '')
                print(f"  {idx:2d}. [{code:15s}] {title:60s} │ {status}")
            print()

    if not has_changes:
        print("✓ Καμία αλλαγή\n")


def print_all_changes(digest: dict):
    """Εμφανίζει αλλαγές όλων των διαδικασιών"""
    all_data = digest.get('all', {})
    all_changes = all_data.get('changes')
    
    if not all_changes:
        return

    print("=" * 100)
    print("📋 ΑΛΛΑΓΕΣ ΣΥΝΟΛΟΥ ΔΙΑΔΙΚΑΣΙΩΝ".center(100))
    print("=" * 100)
    print(f"Baseline: {all_data.get('baseline_timestamp', '—')}\n")

    has_changes = False
    for change_type, label, icon in [
        ('new', 'Νέες Διαδικασίες', '🆕'),
        ('activated', 'Ενεργοποιήθηκαν', '🔓'),
        ('deactivated', 'Απενεργοποιήθηκαν', '🔒'),
        ('removed', 'Αφαιρέθηκαν', '🗑️'),
        ('modified', 'Τροποποιήθηκαν', '📝'),
    ]:
        items = all_changes.get(change_type, [])
        if items:
            has_changes = True
            print(f"{icon} {label} ({len(items)})")
            print("-" * 100)
            for idx, item in enumerate(items, 1):
                proc = item.get('new', item) if isinstance(item, dict) and 'new' in item else item
                code = proc.get('κωδικός', '')[:15]
                title = proc.get('τίτλος', '')[:60]
                status = proc.get('ενεργή', '')
                print(f"  {idx:2d}. [{code:15s}] {title:60s} │ {status}")
            print()

    if not has_changes:
        print("✓ Καμία αλλαγή\n")


def print_incoming_changes(digest: dict):
    """Εμφανίζει αλλαγές εισερχόμενων αιτήσεων"""
    incoming_data = digest.get('incoming', {})
    incoming_changes = incoming_data.get('changes', {})
    
    print("=" * 100)
    print("📥 ΕΙΣΕΡΧΟΜΕΝΕΣ ΑΙΤΗΣΕΙΣ".center(100))
    print("=" * 100)
    print(f"Σημερινή ημερομηνία: {incoming_data.get('date', '')}")
    print(f"Σύγκριση με: {incoming_data.get('reference_date', 'πρώτη καταγραφή')}")
    print(f"Σύνολο: {incoming_data.get('stats', {}).get('total', 0)} "
          f"(✅ Πραγματικές: {incoming_data.get('stats', {}).get('real', 0)}, "
          f"🧪 Δοκιμαστικές: {incoming_data.get('stats', {}).get('test', 0)})\n")

    # Νέες Πραγματικές
    real_new = incoming_data.get('real_new', [])
    if real_new:
        print(f"✅ Νέες ΠΡΑΓΜΑΤΙΚΕΣ ({len(real_new)})")
        print("-" * 100)
        for idx, rec in enumerate(real_new, 1):
            print(f"  {idx}. {format_incoming_record_text(rec)}")
        print()

    # Νέες Δοκιμαστικές
    test_new = incoming_data.get('test_new', [])
    if test_new:
        print(f"🧪 Νέες ΔΟΚΙΜΑΣΤΙΚΕΣ ({len(test_new)})")
        print("-" * 100)
        for idx, rec in enumerate(test_new, 1):
            print(f"  {idx}. {format_incoming_record_text(rec)}")
        print()

    # Αφαιρεθείσες
    removed = incoming_changes.get('removed', [])
    if removed:
        print(f"🗑️  Αφαιρέθηκαν ({len(removed)})")
        print("-" * 100)
        for idx, rec in enumerate(removed, 1):
            case_id = rec.get('case_id', '')[:15]
            date = rec.get('submitted_at', '')[:10]
            print(f"  {idx}. [{case_id:15s}] {date}")
        print()

    # Τροποποιηθείσες
    modified = incoming_changes.get('modified', [])
    if modified:
        print(f"🔄 Τροποποιήθηκαν ({len(modified)})")
        print("-" * 100)
        for idx, pair in enumerate(modified, 1):
            case_id = pair.get('new', {}).get('case_id', '')[:15]
            old_date = pair.get('old', {}).get('submitted_at', '')[:10]
            new_date = pair.get('new', {}).get('submitted_at', '')[:10]
            print(f"  {idx}. [{case_id:15s}] {old_date} → {new_date}")
        print()

    if not any([real_new, test_new, removed, modified]):
        print("✓ Καμία αλλαγή\n")


def print_full_digest(digest: dict):
    """Εμφανίζει την πλήρη αναφορά στο terminal"""
    print_digest_header(digest)
    print_summary(digest)
    print_active_changes(digest)
    print_all_changes(digest)
    print_incoming_changes(digest)
    print("=" * 100)
    print("✅ Αναφορά δημιουργήθηκε. Αποστολή email...".center(100))
    print("=" * 100 + "\n")
