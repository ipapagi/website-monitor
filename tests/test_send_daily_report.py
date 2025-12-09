import os
import sys

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from email_notifier import EmailNotifier

print("=" * 60)
print("TESTING DAILY REPORT EMAIL")
print("=" * 60)

notifier = EmailNotifier()

if not notifier.is_enabled():
    print("❌ Email notifications are disabled!")
    exit(1)

print("\n📧 Sending test daily report email...")
print("-" * 60)

# Mock data for testing
websites_status = {
    "PKM Portal": True,
    "PKM Login": True,
    "Politis System": False
}

notifier.send_daily_report(
    checks_performed=288,  # 288 checks in 24 hours (every 5 minutes)
    errors_count=2,
    websites_status=websites_status
)

print("-" * 60)
print("✅ Daily report email sent successfully!")
print("\nCheck your email inbox for the report.")