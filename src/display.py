"""Εμφάνιση αποτελεσμάτων"""

def _print_field_changes(field_changes, max_len=50):
    """Βοηθητική για εμφάνιση αλλαγών πεδίων"""
    for field, vals in field_changes.items():
        if field not in ['docid', '_raw']:
            old_val = str(vals['old'])[:max_len] + '...' if len(str(vals['old'])) > max_len else (vals['old'] or '(κενό)')
            new_val = str(vals['new'])[:max_len] + '...' if len(str(vals['new'])) > max_len else (vals['new'] or '(κενό)')
            print(f"     └─ {field}: {old_val} → {new_val}")

def print_comparison_results(changes, baseline_data):
    """Εμφανίζει τα αποτελέσματα σύγκρισης ενεργών διαδικασιών"""
    print("\n" + "="*80)
    print("📊 ΣΥΓΚΡΙΣΗ ΜΕ BASELINE".center(80))
    print("="*80)
    print(f"📅 Baseline από: {baseline_data.get('timestamp', 'Άγνωστο')}")
    print(f"📋 Ενεργές στο baseline: {baseline_data.get('count', 0)}")
    print("="*80)
    
    has_changes = False
    for key, label, icon in [('new', 'ΝΕΕΣ ΕΝΕΡΓΕΣ ΔΙΑΔΙΚΑΣΙΕΣ', '🆕'), 
                              ('activated', 'ΕΝΕΡΓΟΠΟΙΗΘΗΚΑΝ', '🔓'),
                              ('deactivated', 'ΑΠΕΝΕΡΓΟΠΟΙΗΘΗΚΑΝ', '🔒'),
                              ('removed', 'ΑΦΑΙΡΕΘΗΚΑΝ', '🗑️'),
                              ('modified', 'ΤΡΟΠΟΠΟΙΗΘΗΚΑΝ', '🔄')]:
        if changes.get(key):
            has_changes = True
            print(f"\n{icon} {label} ({len(changes[key])})")
            print("─" * 80)
            for idx, item in enumerate(changes[key], 1):
                proc = item.get('new', item) if isinstance(item, dict) and 'new' in item else item
                status = "✅" if key in ['new', 'activated'] else "❌" if key == 'deactivated' else "⚠️" if key == 'removed' else "📝"
                print(f"{idx:3}. {status} [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
                if key in ['activated', 'deactivated']:
                    print(f"     └─ Ενεργή: {'ΟΧΙ → ΝΑΙ' if key == 'activated' else 'ΝΑΙ → ΟΧΙ'}")
                elif key == 'modified' and 'field_changes' in item:
                    _print_field_changes(item['field_changes'])
    
    if not has_changes:
        print("\n✅ Καμία αλλαγή από το baseline!")
    print("\n" + "="*80)

def print_all_procedures_comparison(changes, baseline_data):
    """Εμφανίζει τα αποτελέσματα σύγκρισης όλων των διαδικασιών"""
    print("\n" + "="*80)
    print("📊 ΣΥΓΚΡΙΣΗ ΟΛΩΝ ΤΩΝ ΔΙΑΔΙΚΑΣΙΩΝ ΜΕ BASELINE".center(80))
    print("="*80)
    print(f"📅 Baseline από: {baseline_data.get('timestamp', 'Άγνωστο')}")
    print(f"📋 Διαδικασίες στο baseline: {baseline_data.get('count', 0)}")
    print("="*80)
    
    has_changes = False
    for key, label, icon in [('new', 'ΝΕΕΣ ΔΙΑΔΙΚΑΣΙΕΣ', '🆕'),
                              ('activated', 'ΕΝΕΡΓΟΠΟΙΗΘΗΚΑΝ', '🔓'),
                              ('deactivated', 'ΑΠΕΝΕΡΓΟΠΟΙΗΘΗΚΑΝ', '🔒'),
                              ('removed', 'ΑΦΑΙΡΕΘΗΚΑΝ', '🗑️'),
                              ('modified', 'ΤΡΟΠΟΠΟΙΗΘΗΚΑΝ', '🔄')]:
        if changes.get(key):
            has_changes = True
            print(f"\n{icon} {label} ({len(changes[key])})")
            print("─" * 80)
            for idx, item in enumerate(changes[key], 1):
                proc = item.get('new', item) if isinstance(item, dict) and 'new' in item else item
                status = "✅" if proc.get('ενεργή') == 'ΝΑΙ' else "❌"
                print(f"{idx:3}. {status} [{proc.get('κωδικός')}] {proc.get('τίτλος', '')}")
                if key in ['activated', 'deactivated']:
                    print(f"     └─ Ενεργή: {'ΟΧΙ → ΝΑΙ' if key == 'activated' else 'ΝΑΙ → ΟΧΙ'}")
                elif key == 'modified' and 'field_changes' in item:
                    _print_field_changes(item['field_changes'], 40)
    
    if not has_changes:
        print("\n✅ Καμία αλλαγή στις διαδικασίες!")
    print("\n" + "="*80)

def print_incoming_changes(changes, has_reference_snapshot, date_str, reference_date_str=None, show_test_separately=True):
    """Εμφανίζει αλλαγές εισερχόμενων αιτήσεων"""
    from test_users import classify_records, get_record_stats
    
    print("\n" + "="*80)
    print(f"📥 ΕΙΣΕΡΧΟΜΕΝΕΣ ΑΙΤΗΣΕΙΣ ({date_str})".center(80))
    print("="*80)
    
    if not has_reference_snapshot:
        print("ℹ️  Δεν βρέθηκε προηγούμενο snapshot. Δημιουργήθηκε baseline.")
        print("\n" + "="*80)
        return
    
    print(f"🔁 Σύγκριση με snapshot {reference_date_str}")
    
    if not any(changes.values()):
        print("✅ Καμία αλλαγή σε σχέση με το αποθηκευμένο snapshot.")
        print("\n" + "="*80)
        return
    
    # Διαχωρισμός νέων αιτήσεων
    if changes.get('new'):
        real_new, test_new = classify_records(changes['new'])
        
        # Πραγματικές αιτήσεις
        if real_new:
            print(f"\n🆕 Νέες ΠΡΑΓΜΑΤΙΚΕΣ αιτήσεις ({len(real_new)})")
            print("─"*100)
            for idx, rec in enumerate(real_new, 1):
                _print_incoming_record_line(idx, rec)
        
        # Δοκιμαστικές αιτήσεις
        if test_new and show_test_separately:
            print(f"\n🧪 Νέες ΔΟΚΙΜΑΣΤΙΚΕΣ αιτήσεις ({len(test_new)})")
            print("─"*100)
            for idx, rec in enumerate(test_new, 1):
                reason = rec.get('test_reason', '')
                reason_icon = {'internal_user': '👤', 'test_user': '🧑‍💻', 'test_company': '🏢', 'invalid_case_id': '⚠️'}.get(reason, '🧪')
                _print_incoming_record_line(idx, rec, prefix=reason_icon)
        
        # Σύνοψη
        print(f"\n📊 Σύνοψη νέων: {len(real_new)} πραγματικές, {len(test_new)} δοκιμαστικές")
    
    if changes.get('removed'):
        print(f"\n🗑️  Αφαιρέθηκαν ({len(changes['removed'])})")
        print("─"*80)
        for idx, rec in enumerate(changes['removed'], 1):
            party = f" – {rec.get('party')}" if rec.get('party') else ''
            print(f"{idx:3}. [-] Υπόθεση {rec.get('case_id', 'N/A')} – {rec.get('submitted_at', 'N/A')}{party}")
    
    if changes.get('modified'):
        print(f"\n🔄 Τροποποιήθηκαν ({len(changes['modified'])})")
        print("─"*80)
        for idx, pair in enumerate(changes['modified'], 1):
            party = pair['new'].get('party') or pair['old'].get('party') or ''
            print(f"{idx:3}. [~] Υπόθεση {pair['new'].get('case_id', 'N/A')}{' – ' + party if party else ''}")
            print(f"     └─ Παλαιό: {pair['old'].get('submitted_at', '(κενό)')}")
            print(f"     └─ Νέο : {pair['new'].get('submitted_at', '(κενό)')}")
    
    print("\n" + "="*80)

def _print_incoming_record_line(idx, rec, prefix=''):
    """Βοηθητική για εμφάνιση γραμμής εισερχόμενης"""
    case_id = rec.get('case_id', 'N/A')
    protocol = f"({rec.get('protocol_number')})" if rec.get('protocol_number') else ''
    submitted = rec.get('submitted_at', 'N/A')[:16]
    prefix_str = f"{prefix} " if prefix else "[+] "
    print(f"{idx:>3}. {prefix_str}Υπόθεση {case_id}{protocol:<18} │ {submitted}")
    if rec.get('procedure'):
        print(f"         📋 Διαδικασία: {rec['procedure']}")
    if rec.get('directory'):
        print(f"         🏢 Δ/νση: {rec['directory']}")
    print(f"         👤 Συναλλασσόμενος: {rec.get('party') or '—'}")

def print_test_analysis(records, date_str):
    """Εμφανίζει ανάλυση δοκιμαστικών/πραγματικών αιτήσεων"""
    from test_users import classify_records, get_record_stats
    
    real, test = classify_records(records)
    stats = get_record_stats(records)
    
    print("\n" + "="*80)
    print(f"🔬 ΑΝΑΛΥΣΗ ΑΙΤΗΣΕΩΝ ({date_str})".center(80))
    print("="*80)
    
    print(f"\n📊 ΣΥΝΟΨΗ")
    print("─"*40)
    print(f"  Σύνολο αιτήσεων:     {stats['total']:>5}")
    print(f"  ✅ Πραγματικές:       {stats['real']:>5} ({100*stats['real']/stats['total']:.1f}%)" if stats['total'] > 0 else "")
    print(f"  🧪 Δοκιμαστικές:      {stats['test']:>5} ({100*stats['test']/stats['total']:.1f}%)" if stats['total'] > 0 else "")
    
    if stats['test_breakdown']:
        print(f"\n🧪 ΑΝΑΛΥΣΗ ΔΟΚΙΜΑΣΤΙΚΩΝ")
        print("─"*40)
        reason_labels = {
            'internal_user': '👤 Εσωτερικοί χρήστες',
            'test_user': '🧑‍💻 Δοκιμαστικοί χρήστες',
            'test_company': '🏢 Εταιρείες υποστήριξης',
            'invalid_case_id': '⚠️  Άκυρα Case IDs'
        }
        for reason, count in stats['test_breakdown'].items():
            label = reason_labels.get(reason, reason)
            print(f"  {label}: {count}")
    
    if real:
        print(f"\n✅ ΠΡΑΓΜΑΤΙΚΕΣ ΑΙΤΗΣΕΙΣ ({len(real)})")
        print("─"*80)
        for idx, rec in enumerate(real, 1):
            _print_analysis_record(idx, rec, '✅')
    
    if test:
        print(f"\n🧪 ΔΟΚΙΜΑΣΤΙΚΕΣ ΑΙΤΗΣΕΙΣ ({len(test)})")
        print("─"*80)
        for idx, rec in enumerate(test, 1):
            reason = rec.get('test_reason', '')
            icon = {'internal_user': '👤', 'test_user': '🧑‍💻', 'test_company': '🏢', 'invalid_case_id': '⚠️'}.get(reason, '🧪')
            _print_analysis_record(idx, rec, icon)
    
    print("\n" + "="*80)

def _print_analysis_record(idx, rec, icon):
    """Βοηθητική για εμφάνιση εγγραφής στην ανάλυση"""
    case_id = rec.get('case_id', 'N/A')
    submitted = rec.get('submitted_at', 'N/A')[:16]
    party = rec.get('party', '—')
    procedure = rec.get('procedure', '')
    print(f"{idx:>3}. {icon} [{case_id}] {submitted} - {party}")
    if procedure:
        print(f"         📋 {procedure[:60]}{'...' if len(procedure) > 60 else ''}")
