#!/usr/bin/env python3
"""
Test script to verify email and PDF generation with new incoming request format
"""
import os
import sys
import json
from datetime import datetime

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from email_notifier import EmailNotifier

print("=" * 80)
print("TESTING NEW EMAIL AND PDF FORMAT WITH INCOMING REQUESTS")
print("=" * 80)

notifier = EmailNotifier()

if not notifier.is_enabled():
    print("⚠️  Email notifications are disabled! Will only generate PDF.")

# Load real sample data
print("\n📋 Loading sample data from incoming_2025-12-03.json...")
incoming_file = os.path.join(os.path.dirname(__file__), 'data', 'incoming_requests', 'incoming_2025-12-03.json')

with open(incoming_file, 'r', encoding='utf-8') as f:
    incoming_snapshot = json.load(f)

# Create sample digest with real data
sample_digest = {
    "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    "base_url": "https://pkm.rcm.gov.gr",
    "active": {
        "total": 3,
        "baseline_timestamp": "2025-12-02",
        "changes": {
            "new": [{"κωδικός": "ΥΓΕΙΑΣ-050", "τίτλος": "Άδεια ασκήσεως επαγγέλματος ψυχολόγου", "ενεργή": "ΝΑΙ"}],
            "activated": [],
            "deactivated": [],
            "removed": [],
            "modified": [],
        },
    },
    "all": {
        "total": 5,
        "baseline_timestamp": "2025-12-02",
        "changes": {
            "new": [],
            "activated": [],
            "deactivated": [],
            "removed": [],
            "modified": [],
        },
    },
    "incoming": {
        "date": "2025-12-03",
        "reference_date": "2025-12-02",
        "changes": {"new": [], "removed": [], "modified": []},
        # Take first 3 real requests
        "real_new": [incoming_snapshot['records'][i] for i in range(min(1, len(incoming_snapshot['records'])))],
        # Take next 3 test requests
        "test_new": [incoming_snapshot['records'][i] for i in range(1, min(4, len(incoming_snapshot['records'])))],
        "stats": {
            "total": len(incoming_snapshot['records']),
            "real": 1,
            "test": 3,
            "test_breakdown": {}
        },
    },
}

print(f"\n✓ Real requests: {len(sample_digest['incoming']['real_new'])}")
print(f"✓ Test requests: {len(sample_digest['incoming']['test_new'])}")

# Test email sending
if notifier.is_enabled():
    print("\n📧 Sending test daily digest email...")
    print("-" * 80)
    notifier.send_daily_digest(sample_digest)
    print("-" * 80)
    print("✅ Daily digest email sent!")
else:
    print("\n⚠️  Skipping email sending (disabled)")

# Test PDF generation
print("\n📄 Generating PDF report...")
print("-" * 80)
pdf_path = notifier.generate_daily_report_pdf(sample_digest)
if pdf_path:
    print(f"✅ PDF generated: {pdf_path}")
    file_size = os.path.getsize(pdf_path)
    print(f"   File size: {file_size:,} bytes")
else:
    print("❌ PDF generation failed!")

print("\n" + "=" * 80)
print("TEST COMPLETED")
print("=" * 80)
