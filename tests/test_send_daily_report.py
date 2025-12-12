import os
import sys
from datetime import datetime

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from email_notifier import EmailNotifier

print("=" * 60)
print("TESTING DAILY DIGEST EMAIL")
print("=" * 60)

notifier = EmailNotifier()

if not notifier.is_enabled():
    print("❌ Email notifications are disabled!")
    exit(1)

print("\n📧 Sending test daily digest email...")
print("-" * 60)

sample_digest = {
    "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    "base_url": "https://example.gov",
    "active": {
        "total": 3,
        "baseline_timestamp": datetime.now().isoformat(),
        "changes": {
            "new": [{"κωδικός": "A1", "τίτλος": "Νέα Διαδικασία", "ενεργή": "ΝΑΙ"}],
            "activated": [],
            "deactivated": [],
            "removed": [],
            "modified": [],
        },
    },
    "all": {
        "total": 5,
        "baseline_timestamp": datetime.now().isoformat(),
        "changes": {
            "new": [],
            "activated": [],
            "deactivated": [],
            "removed": [],
            "modified": [],
        },
    },
    "incoming": {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "reference_date": None,
        "changes": {"new": [], "removed": [], "modified": []},
        "real_new": [
            {"case_id": "123", "submitted_at": "2025-12-11 10:00", "subject": "Αίτηση Α", "party": "Δήμος"}
        ],
        "test_new": [],
        "stats": {"total": 1, "real": 1, "test": 0, "test_breakdown": {}},
    },
}

notifier.send_daily_digest(sample_digest)

print("-" * 60)
print("✅ Daily digest email sent successfully!")
print("\nCheck your email inbox for the report.")