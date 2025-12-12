import os
import sys
from datetime import datetime

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from email_notifier import EmailNotifier

print("=" * 60)
print("TESTING RECOVERY EMAIL NOTIFICATION")
print("=" * 60)

notifier = EmailNotifier()

if not notifier.is_enabled():
    print("❌ Email notifications are disabled!")
    exit(1)

print("\n📧 Sending test recovery email...")
print("-" * 60)

notifier.notify_recovery(
    website_name="PKM Portal",
    url="https://pkm.rcm.gov.gr",
    downtime_duration="2λ 45δ",
    timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
)

print("-" * 60)
print("✅ Test recovery email sent successfully!")
print("\nCheck your email inbox for the recovery message.")