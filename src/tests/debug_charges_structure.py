#!/usr/bin/env python3
"""Debug: Check structure of fetch_charges_combined result"""

import sys
import os

# Setup path for imports
from src_setup import *

from monitor import PKMMonitor
from charges import fetch_charges_combined
from utils import load_config
from config import get_project_root
import json

root = get_project_root()
cfg_path = os.path.join(root, 'config', 'config.yaml')
config = load_config(cfg_path)

monitor = PKMMonitor(
    base_url=config.get('base_url', 'https://shde.pkm.gov.gr'),
    urls=config.get('urls', {}),
    api_params=config.get('api_params', {}),
    login_params=config.get('login_params', {}),
    check_interval=config.get('check_interval', 300),
    username=config.get('username'),
    password=config.get('password'),
    session_cookies=config.get('session_cookies')
)

if not monitor.logged_in and not monitor.login():
    print("Login failed")
    sys.exit(1)

result = fetch_charges_combined(monitor)
print("Type of result:", type(result))

if isinstance(result, tuple):
    print("Tuple with %d elements" % len(result))
    records, charges_dict = result
    print("\nFirst element type:", type(records), "len:", len(records) if hasattr(records, '__len__') else 'N/A')
    print("Second element type:", type(charges_dict), "len:", len(charges_dict) if hasattr(charges_dict, '__len__') else 'N/A')
    
    if isinstance(charges_dict, dict) and len(charges_dict) > 0:
        first_key = list(charges_dict.keys())[0]
        print("\nFirst PKM:", first_key)
        first_value = charges_dict[first_key]
        print("Type of charge value:", type(first_value))
        print("Value:", first_value)
        
        if isinstance(first_value, dict):
            print("Keys in charge dict:", list(first_value.keys()))
