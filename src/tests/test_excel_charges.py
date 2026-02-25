"""Δοκιμή δημιουργίας Excel με χρεώσεις"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from daily_report import build_daily_digest
from xls_export import build_requests_xls
from config import get_project_root

print("\n" + "="*80)
print("📊 ΔΟΚΙΜΗ EXCEL EXPORT ΜΕ ΧΡΕΩΣΕΙΣ".center(80))
print("="*80 + "\n")

# Build digest
print("📋 Δημιουργία digest...")
digest = build_daily_digest()

# Create Excel with all records
output_dir = os.path.join(get_project_root(), 'data', 'outputs', 'reports')
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(output_dir, 'test_charges_report.xlsx')

print(f"📝 Δημιουργία Excel: {output_file}")
build_requests_xls(digest, scope='all', file_path=output_file)

print(f"✅ Το Excel δημιουργήθηκε επιτυχώς!")
print(f"📁 Διαδρομή: {output_file}")

# Statistics
incoming = digest.get('incoming', {})
records = incoming.get('records', [])
charged = [r for r in records if r.get('_charge', {}).get('charged')]
print(f"\n📊 Στατιστικά:")
print(f"   Σύνολο: {len(records)} αιτήσεις")
print(f"   Χρεωμένες: {len(charged)} ({len(charged)/len(records)*100:.1f}%)")
print(f"   Μη χρεωμένες: {len(records) - len(charged)}")

print(f"\n💡 Ανοίξτε το αρχείο για να δείτε τη στήλη 'Ανάθεση σε'")
print("="*80 + "\n")
