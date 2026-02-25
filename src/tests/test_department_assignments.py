#!/usr/bin/env python3
"""Check if department assignments are from completed cases (queryId=19)"""

import sys
import os
import re
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root, INCOMING_DEFAULT_PARAMS
from incoming import fetch_incoming_records, simplify_incoming_records
from charges import fetch_charges_combined, add_charge_info_from_combined

def is_department(employee_name: str) -> bool:
    """Check if employee_name is a department (ΤΜΗΜΑ...) instead of a person."""
    if not employee_name:
        return False
    
    # Department indicators
    dept_keywords = [
        'ΤΜΗΜΑ',
        'ΔΙΕΥΘΥΝΣΗ',
        'Προϊστάμενοι',
        'Γενική Διεύθυνση',
        'Το Γραφείο',
        'άπαν'  # "Άπαν..." for delegated/unanimous decisions
    ]
    
    name_upper = str(employee_name).upper()
    return any(keyword in name_upper for keyword in dept_keywords)


def fetch_completed_cases(monitor) -> dict:
    """Fetch queryId=19 (Διεκπεραιωμένες) to check if these are completed."""
    params = {
        'queryId': '19',
        'queryOwner': '19',
        'isCase': 'false',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': '100',
        'isPoll': 'true'
    }
    
    data = monitor.fetch_data(params)
    if not data or not data.get('success'):
        return {}
    
    # Extract PKM numbers from DESCRIPTION
    completed_pkms = {}
    for rec in data.get('data', []):
        description = rec.get('DESCRIPTION', '')
        # Try to extract PKM from description
        match = re.search(r'Αίτημα\s+\d+/(\d+)', description)
        if match:
            pkm = match.group(1)
            completed_pkms[pkm] = rec
    
    return completed_pkms


def main():
    # Load config
    root = get_project_root()
    cfg_path = os.path.join(root, 'config', 'config.yaml')
    config = load_config(cfg_path)
    
    # Create monitor
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
        print("❌ Login failed")
        return
    
    print("\n" + "="*80)
    print("ANALYSIS: Department-assigned cases - Are they completed?")
    print("="*80)
    
    # Fetch incoming records with combined charges
    print("\n📥 Fetching incoming records with combined charges...")
    incoming_data = monitor.fetch_data(INCOMING_DEFAULT_PARAMS)
    incoming_records = incoming_data.get('data', []) if incoming_data else []
    records = simplify_incoming_records(incoming_records)
    
    charges_records, charges_by_pkm = fetch_charges_combined(monitor)
    records = add_charge_info_from_combined(records, charges_by_pkm)
    print(f"✅ Fetched {len(records)} incoming records")
    
    # Fetch completed cases (queryId=19)
    print("\n📥 Fetching completed cases (queryId=19)...")
    completed_cases = fetch_completed_cases(monitor)
    print(f"✅ Fetched {len(completed_cases)} completed cases")
    
    # Separate by person vs department
    print("\n" + "="*80)
    print("ANALYSIS: Personal vs Department Assignments")
    print("="*80)
    
    charged_records = [r for r in records if r.get('_charge', {}).get('charged')]
    personal_assignments = []
    department_assignments = []
    
    for rec in charged_records:
        employee = rec.get('_charge', {}).get('employee', '')
        if is_department(employee):
            department_assignments.append(rec)
        else:
            personal_assignments.append(rec)
    
    print(f"\n📊 Assignment Type Distribution:")
    print(f"   Personal (individual): {len(personal_assignments)} cases")
    print(f"   Department assignments: {len(department_assignments)} cases")
    print(f"   Total charged: {len(charged_records)}")
    
    if department_assignments:
        print(f"\n⚠️  Department-assigned cases (potential completed):")
        print(f"   Total: {len(department_assignments)}")
        
        # Check if these are in completed cases
        dept_in_completed = 0
        dept_not_in_completed = 0
        
        print(f"\n   Sample (first 10):")
        for i, rec in enumerate(department_assignments[:10], 1):
            case_id = rec.get('case_id', '')
            employee = rec.get('_charge', {}).get('employee', '')
            
            if case_id in completed_cases:
                status = "✅ FOUND in queryId=19 (Completed)"
                dept_in_completed += 1
            else:
                status = "❌ NOT in queryId=19"
                dept_not_in_completed += 1
            
            # Truncate long names
            emp_short = employee[:60] + "..." if len(employee) > 60 else employee
            print(f"   {i:2}. PKM {case_id:6} → {emp_short}")
            print(f"       {status}")
        
        # Count all
        for rec in department_assignments:
            case_id = rec.get('case_id', '')
            if case_id in completed_cases:
                dept_in_completed += 1
            else:
                dept_not_in_completed += 1
        
        print(f"\n📊 SUMMARY of Department Assignments:")
        print(f"   Found in queryId=19 (Completed): {dept_in_completed}/{len(department_assignments)} ({dept_in_completed/len(department_assignments)*100:.1f}%)")
        print(f"   NOT found in queryId=19: {dept_not_in_completed}/{len(department_assignments)} ({dept_not_in_completed/len(department_assignments)*100:.1f}%)")
        
        if dept_in_completed / len(department_assignments) > 0.8:
            print(f"\n✅ CONCLUSION: Department assignments ARE primarily completed cases!")
        else:
            print(f"\n⚠️  CONCLUSION: Department assignments are MIXED (some completed, some not)")
    else:
        print("\n✅ No department assignments found - all are personal!")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
