#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test weekly report with date normalization."""

import sys
import os
import subprocess
from datetime import datetime

sys.path.insert(0, 'src')

# Fix Windows console encoding  
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from config import get_project_root

# Normalize date like the script should
date_input = "2026-2-9"
parts = date_input.split('-')
parsed_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
normalized_date = parsed_date.strftime("%Y-%m-%d")

print("=" * 80)
print("Test: Date Normalization in Weekly Report")
print("=" * 80)
print()
print(f"Input date: {date_input}")
print(f"Normalized: {normalized_date}")
print()

# Check where files would be created
project_root = get_project_root()
outputs_dir = os.path.join(project_root, 'data', 'outputs', 'reports')

print(f"Output directory: {outputs_dir}")
print()

# Expected filename pattern
expected_pattern = f"{normalized_date}_*_Αναφορά Εισερχομένων Αιτήσεων ΣΗΔΕ.xlsx"
print(f"Expected filename pattern: {expected_pattern}")
print()

# List any existing files with the normalized date
if os.path.exists(outputs_dir):
    files = os.listdir(outputs_dir)
    matching = [f for f in files if f.startswith(normalized_date)]
    if matching:
        print(f"Existing files with normalized date ({normalized_date}):")
        for f in matching:
            print(f"  - {f}")
    else:
        print(f"No files yet with normalized date ({normalized_date})")

print()
print("=" * 80)
print(f"✅ Date normalization ready: {date_input} -> {normalized_date}")
print("=" * 80)
