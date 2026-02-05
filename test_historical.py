#!/usr/bin/env python
# Quick test to ensure --date parameter works without encoding issues
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from directory_emails import send_directory_emails

print("Testing historical date parameter...")
send_directory_emails(test_date="2025-12-02")
print("\n✓ Test completed successfully!")
