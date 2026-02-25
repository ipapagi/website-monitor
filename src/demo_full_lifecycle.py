"""
Demo: Full Case Lifecycle Tracking
Ενσωμάτωση όλων των 3 συσχετίσεων για πλήρη παρακολούθηση
"""
import os
from dotenv import load_dotenv

from session import PKMSession
from config import INCOMING_DEFAULT_PARAMS, SETTLED_CASES_DEFAULT_PARAMS
from settled_cases import (
    fetch_settled_cases,
    filter_out_settled_from_incoming,
    get_settled_for_incoming,
    simplify_settled_records
)
from ots_assignments import (
    fetch_ots_assignments,
    add_assignment_info,
    get_assignment_info,
    filter_assigned,
    filter_unassigned,
    get_assignment_statistics,
    format_assignment_for_display,
    simplify_ots_record
)
from api import sanitize_party_name

load_dotenv()
USERNAME = os.getenv('PKM_USERNAME', '')
PASSWORD = os.getenv('PKM_PASSWORD', '')


def get_full_case_status(portal_record, settled_by_code, ots_by_pkm):
    """
    Λαμβάνει πλήρη κατάσταση της υπόθεσης
    
    Returns: dict with status, details, next_action
    """
    pkm = str(portal_record.get('W007_P_FLD21', '')).strip()
    party = portal_record.get('W007_P_FLD13', '')
    
    # Check 1: Is it settled?
    settled = get_settled_for_incoming(portal_record, settled_by_code)
    if settled:
        return {
            'pkm': pkm,
            'case_id': settled.get('W001_P_FLD2', ''),
            'status': '✅ COMPLETED',
            'party': sanitize_party_name(party),
            'settled_date': settled.get('W001_P_FLD3', ''),
            'final_status': settled.get('W001_P_FLD12', ''),
            'color': '🟢'
        }
    
    # Check 2: Is it assigned to department?
    assignment = get_assignment_info(portal_record, ots_by_pkm)
    if assignment:
        return {
            'pkm': pkm,
            'status': '⏳ IN PROGRESS',
            'party': sanitize_party_name(party),
            'department': assignment['department_short'],
            'assigned_date': assignment['date_assigned_formatted'],
            'assignment_status': assignment['status'],
            'assigned_by': assignment['assigned_by'],
            'color': '🟡'
        }
    
    # Check 3: Pending assignment
    return {
        'pkm': pkm,
        'status': '⏳ PENDING',
        'party': sanitize_party_name(party),
        'message': 'Awaiting department assignment',
        'submitted': portal_record.get('W007_P_FLD3', ''),
        'color': '🔵'
    }


def demo_full_lifecycle():
    """Δείχνει πλήρη κύκλο ζωής υποθέσεων"""
    
    print("\n" + "=" * 100)
    print("🎯 DEMO: FULL CASE LIFECYCLE TRACKING")
    print("=" * 100)
    
    # ==================== SETUP ====================
    print("\n" + "─" * 100)
    print("STEP 1: Initialize Session & Fetch Data")
    print("─" * 100)
    
    session = PKMSession(
        base_url="https://shde.pkm.gov.gr",
        urls={
            'login_page': '/login.jsp',
            'login_api': '/services/LoginServices/loginWeb',
            'main_page': '/ext_main.jsp?locale=el',
            'data_api': '/services/SearchServices/getSearchDataByQueryId'
        },
        login_params={
            'application': '2',
            'otp': ''
        },
        username=USERNAME,
        password=PASSWORD
    )
    
    # Fetch Portal Incoming
    print("\n📥 Fetching Portal Incoming (queryId=6)...")
    portal_params = INCOMING_DEFAULT_PARAMS.copy()
    portal_params['limit'] = 100
    portal_data = session.fetch_data(portal_params)
    portal_records = portal_data.get('data', []) if portal_data and portal_data.get('success') else []
    print(f"   ✅ {len(portal_records)} incoming cases fetched")
    
    # Fetch Settled Cases
    print("\n🔒 Fetching Settled Cases (queryId=19)...")
    settled_params = SETTLED_CASES_DEFAULT_PARAMS.copy()
    settled_params['limit'] = 100
    settled_data = session.fetch_data(settled_params)
    settled_records = settled_data.get('data', []) if settled_data and settled_data.get('success') else []
    settled_by_code = {}
    if settled_records:
        simplified = simplify_settled_records(settled_records)
        for rec in simplified:
            code = str(rec.get('W001_P_FLD2', '')).strip()
            if code:
                settled_by_code[code] = rec
    print(f"   ✅ {len(settled_records)} settled cases fetched")
    print(f"   ✅ {len(settled_by_code)} can be correlated")
    
    # Fetch OTS Assignments
    print("\n👥 Fetching OTS Assignments (queryId=2)...")
    ots_records, ots_by_pkm = fetch_ots_assignments(session)
    print(f"   ✅ {len(ots_records)} OTS records fetched")
    print(f"   ✅ {len(ots_by_pkm)} can be correlated with PKM")
    
    # ==================== ANALYSIS ====================
    print("\n" + "─" * 100)
    print("STEP 2: Analyze Case Distribution")
    print("─" * 100)
    
    test_sample = portal_records[:50]
    
    # Categorize cases
    settled_count = 0
    assigned_count = 0
    pending_count = 0
    
    for rec in test_sample:
        if get_settled_for_incoming(rec, settled_by_code):
            settled_count += 1
        elif get_assignment_info(rec, ots_by_pkm):
            assigned_count += 1
        else:
            pending_count += 1
    
    print(f"\n📊 Sample Analysis ({len(test_sample)} cases):")
    print(f"   ✅ COMPLETED:     {settled_count:3} ({settled_count/len(test_sample)*100:5.1f}%) - Cases that are settled")
    print(f"   ⏳ IN PROGRESS:    {assigned_count:3} ({assigned_count/len(test_sample)*100:5.1f}%) - Assigned to department")
    print(f"   🔵 PENDING:       {pending_count:3} ({pending_count/len(test_sample)*100:5.1f}%) - Awaiting first assignment")
    
    # ==================== DETAILED DISPLAY ====================
    print("\n" + "─" * 100)
    print("STEP 3: Case Status Details")
    print("─" * 100)
    
    statuses = {'🟢': [], '🟡': [], '🔵': []}
    
    print()
    for i, rec in enumerate(test_sample[:25], 1):
        status_info = get_full_case_status(rec, settled_by_code, ots_by_pkm)
        color = status_info['color']
        status = status_info['status']
        
        statuses[color].append(status_info)
        
        if status == '✅ COMPLETED':
            print(f"{i:2}. {color} {status_info['pkm']} | {status_info['settlement_date']}")
            print(f"    Party: {status_info['party']}")
            print(f"    Final: {status_info['final_status']}")
        
        elif status == '⏳ IN PROGRESS':
            print(f"{i:2}. {color} {status_info['pkm']} | {status_info['assigned_date']}")
            print(f"    Party: {status_info['party']}")
            print(f"    Dept:  {status_info['department']}")
            print(f"    Assigned by: {status_info['assigned_by']}")
        
        else:  # PENDING
            print(f"{i:2}. {color} {status_info['pkm']} | {status_info['submitted']}")
            print(f"    Party: {status_info['party']}")
            print(f"    Status: Awaiting assignment")
    
    if len(test_sample) > 25:
        print(f"\n    ... and {len(test_sample) - 25} more cases")
    
    # ==================== DEPARTMENT WORKLOAD ====================
    print("\n" + "─" * 100)
    print("STEP 4: Department Workload")
    print("─" * 100)
    
    enriched = add_assignment_info(test_sample, ots_by_pkm)
    stats = get_assignment_statistics(enriched)
    
    print(f"\n👥 Workload Distribution:")
    sorted_depts = sorted(stats['by_department'].items(), key=lambda x: x[1], reverse=True)
    
    for dept, count in sorted_depts[:8]:
        bar = "█" * (count // 2 + 1)
        print(f"   {count:2} cases | {bar} | {dept}")
    
    if len(sorted_depts) > 8:
        print(f"   ... and {len(sorted_depts) - 8} more departments")
    
    # ==================== STATISTICS ====================
    print("\n" + "─" * 100)
    print("STEP 5: Overall Statistics")
    print("─" * 100)
    
    print(f"\n📈 System-Wide Metrics (tested on {len(test_sample)} cases):")
    print(f"   Total Portal Incoming:   {len(portal_records)}")
    print(f"   Total Settled Cases:     {len(settled_records)}")
    print(f"   Total OTS Assignments:   {len(ots_records)}")
    print(f"\n   Settled Match Rate:      {(settled_count / len(test_sample) * 100):.1f}%")
    print(f"   Assignment Match Rate:   {(assigned_count / len(test_sample) * 100):.1f}%")
    print(f"   Pending Assignment Rate: {(pending_count / len(test_sample) * 100):.1f}%")
    
    print(f"\n   Departments with Cases: {stats['unique_departments']}")
    print(f"   Average Cases/Dept:     {stats['assigned'] / stats['unique_departments']:.1f}")
    print(f"\n   Assigned Cases:         {stats['assigned']}")
    print(f"   Unassigned Cases:       {stats['unassigned']}")
    
    # ==================== SUMMARY ====================
    print("\n" + "=" * 100)
    print("📋 SUMMARY: Case Tracking Integration")
    print("=" * 100)
    
    print(f"""
✅ INTEGRATION STATUS:
   
   1. Settled Cases Correlation:     ✓ Active (filters completed)
   2. OTS Assignments Tracking:      ✓ Active (shows department)
   3. Department Information:        ✓ Ready (see directories_manager.py)
   
🎯 CAPABILITIES UNLOCKED:

   • Show only ACTIVE cases (exclude settled)
   • Display assigned department with each case
   • Alert for cases > 5 days without assignment
   • Email director of assigned department
   • Track SLA completion times
   • Monitor per-department workload
   
📊 NEXT STEPS:

   1. Integrate into daily_report.py
   2. Add assignment column to Excel export
   3. Set up SLA alerts (> 5 days unassigned)
   4. Connect department emails
   5. Track historical metrics
""")
    
    print("=" * 100)
    print("✅ DEMO COMPLETE")
    print("=" * 100)
    
    return {
        'portal_records': portal_records,
        'settled_records': settled_records,
        'ots_records': ots_records,
        'settled_by_code': settled_by_code,
        'ots_by_pkm': ots_by_pkm
    }


if __name__ == '__main__':
    demo_full_lifecycle()
