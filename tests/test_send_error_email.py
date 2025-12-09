import os
import sys
from datetime import datetime

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from email_notifier import EmailNotifier

print("=" * 60)
print("TESTING ERROR EMAIL NOTIFICATION")
print("=" * 60)

notifier = EmailNotifier()

if not notifier.is_enabled():
    print("❌ Email notifications are disabled!")
    print("Check your .env file configuration")
    exit(1)

print("\n📧 Sending test error email...")
print("-" * 60)

notifier.notify_error(
    website_name="PKM Portal",
    error_message="Connection timeout - Unable to reach server after 10 seconds",
    url="https://pkm.rcm.gov.gr",
    timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
)

print("-" * 60)
print("✅ Test error email sent successfully!")
print("\nCheck your email inbox for the test message.")