"""
Comprehensive test suite for all email notification types
"""
import os
import sys
from datetime import datetime

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from email_notifier import EmailNotifier

def test_configuration():
    """Test 1: Configuration"""
    print("\n" + "=" * 60)
    print("TEST 1: EMAIL CONFIGURATION")
    print("=" * 60)
    
    notifier = EmailNotifier()
    
    print(f"✓ Email Address: {notifier.email_address}")
    print(f"✓ SMTP Server: {notifier.smtp_server}:{notifier.smtp_port}")
    print(f"✓ Notifications Enabled: {notifier.is_enabled()}")
    
    admins = notifier.load_admins()
    print(f"✓ Admins Loaded: {len(admins)}")
    
    if notifier.is_enabled() and admins:
        print("✅ PASS: Configuration is valid!")
        return True
    else:
        print("❌ FAIL: Configuration is invalid!")
        return False

def test_error_notification():
    """Test 2: Error Notification"""
    print("\n" + "=" * 60)
    print("TEST 2: ERROR EMAIL NOTIFICATION")
    print("=" * 60)
    
    notifier = EmailNotifier()
    
    if not notifier.is_enabled():
        print("❌ SKIP: Email notifications disabled")
        return False
    
    print("Sending test error email...")
    notifier.notify_error(
        website_name="TEST - PKM Portal",
        error_message="Test error: Connection timeout - Unable to reach server",
        url="https://pkm.rcm.gov.gr",
        timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )
    
    print("✅ PASS: Error email sent!")
    return True

def test_recovery_notification():
    """Test 3: Recovery Notification"""
    print("\n" + "=" * 60)
    print("TEST 3: RECOVERY EMAIL NOTIFICATION")
    print("=" * 60)
    
    notifier = EmailNotifier()
    
    if not notifier.is_enabled():
        print("❌ SKIP: Email notifications disabled")
        return False
    
    print("Sending test recovery email...")
    notifier.notify_recovery(
        website_name="TEST - PKM Portal",
        url="https://pkm.rcm.gov.gr",
        downtime_duration="5λ 30δ",
        timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )
    
    print("✅ PASS: Recovery email sent!")
    return True

def test_daily_report():
    """Test 4: Daily Report"""
    print("\n" + "=" * 60)
    print("TEST 4: DAILY REPORT EMAIL")
    print("=" * 60)
    
    notifier = EmailNotifier()
    
    if not notifier.is_enabled():
        print("❌ SKIP: Email notifications disabled")
        return False
    
    websites_status = {
        "TEST - PKM Portal": True,
        "TEST - PKM Login": True,
        "TEST - Politis System": False
    }
    
    print("Sending test daily report...")
    notifier.send_daily_report(
        checks_performed=288,
        errors_count=2,
        websites_status=websites_status
    )
    
    print("✅ PASS: Daily report email sent!")
    return True

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + "EMAIL NOTIFICATION COMPREHENSIVE TEST SUITE".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = {
        "Configuration": test_configuration(),
        "Error Notification": test_error_notification(),
        "Recovery Notification": test_recovery_notification(),
        "Daily Report": test_daily_report()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

if __name__ == "__main__":
    main()