import os
import sys
from dotenv import load_dotenv

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from email_notifier import EmailNotifier

load_dotenv()

print("=" * 60)
print("EMAIL CONFIGURATION TEST")
print("=" * 60)

notifier = EmailNotifier()

print(f"\n✓ Email Address: {notifier.email_address}")
print(f"✓ SMTP Server: {notifier.smtp_server}:{notifier.smtp_port}")
print(f"✓ Notifications Enabled: {notifier.is_enabled()}")

print("\n" + "=" * 60)
print("ADMINS LOADED")
print("=" * 60)

admins = notifier.load_admins()
if admins:
    for admin in admins:
        print(f"\n• Name: {admin.get('name')}")
        print(f"  Email: {admin.get('email')}")
        print(f"  Notify on Error: {admin.get('notify_on_error')}")
        print(f"  Notify on Recovery: {admin.get('notify_on_recovery')}")
else:
    print("\n⚠️ No admins found in admins.json")

if notifier.is_enabled():
    print("\n✅ Configuration is valid!")
else:
    print("\n❌ Configuration is INVALID - Check .env file")