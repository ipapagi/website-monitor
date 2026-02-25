#!/usr/bin/env python3
"""Test script to investigate queryId=3 as alternative charge source."""

import sys
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add src to path
sys.path.insert(0, 'src')

from monitor import PKMMonitor
from utils import load_config
from config import get_project_root


def extract_pkm_from_description(description: str) -> Optional[str]:
    """Extract case ID from description field.
    
    Expected patterns:
    - "Αίτημα 2026/105139"
    - "Αίτημα 105139"
    - "2026/105139"
    - "105139"
    """
    if not description:
        return None
    
    # Try pattern: "Αίτημα YYYY/XXXXXX" or "Αίτημα XXXXXX"
    match = re.search(r'Αίτημα\s+(?:\d{4}/)?(\d+)', description)
    if match:
        return match.group(1)
    
    # Try pattern: "YYYY/XXXXXX"
    match = re.search(r'(\d{4})/(\d+)', description)
    if match:
        return match.group(2)
    
    # Try pattern: just digits (at least 5)
    match = re.search(r'(\d{5,})', description)
    if match:
        return match.group(1)
    
    return None


def fetch_queryid3_records(monitor, limit: int = 100) -> List[Dict]:
    """Fetch records from queryId=3."""
    params = {
        'queryId': '3',
        'queryOwner': '3',
        'isCase': 'false',
        'stateId': 'welcomeGrid-45_dashboard0',
        'page': '1',
        'start': '0',
        'limit': str(limit),
        'isPoll': 'true'
    }
    
    data = monitor.fetch_data(params)
    
    if not data or not data.get('success'):
        print(f"❌ Error fetching queryId=3: {data}")
        return []
    
    records = data.get('data', [])
    print(f"✅ Fetched {len(records)} records from queryId=3")
    return records


def analyze_user_fields(records: List[Dict]) -> Dict:
    """Analyze USER_GROUP_ID_TO vs USER_ID_FROM fields."""
    
    analysis = {
        'total_records': len(records),
        'records_with_both_fields': 0,
        'same_user_count': 0,
        'different_user_count': 0,
        'missing_description': 0,
        'pkm_extraction_success': 0,
        'samples_same': [],
        'samples_different': [],
        'user_comparison_details': []
    }
    
    for i, record in enumerate(records):
        user_to = record.get('USER_GROUP_ID_TO')
        user_from = record.get('USER_ID_FROM')
        description = record.get('DESCRIPTION', '')
        pkm = extract_pkm_from_description(description)
        
        if not pkm:
            analysis['missing_description'] += 1
            continue
        
        analysis['pkm_extraction_success'] += 1
        
        if user_to and user_from:
            analysis['records_with_both_fields'] += 1
            
            # Compare values
            are_same = user_to == user_from
            
            detail = {
                'pkm': pkm,
                'user_to': user_to,
                'user_from': user_from,
                'are_same': are_same,
                'description': description[:80]
            }
            analysis['user_comparison_details'].append(detail)
            
            if are_same:
                analysis['same_user_count'] += 1
                if len(analysis['samples_same']) < 5:
                    analysis['samples_same'].append(detail)
            else:
                analysis['different_user_count'] += 1
                if len(analysis['samples_different']) < 5:
                    analysis['samples_different'].append(detail)
    
    return analysis


def print_analysis(analysis: Dict) -> None:
    """Print analysis results."""
    print("\n" + "="*80)
    print("QueryId=3 USER_GROUP_ID_TO vs USER_ID_FROM Analysis")
    print("="*80)
    
    print(f"\n📊 Statistics:")
    print(f"   Total records fetched: {analysis['total_records']}")
    print(f"   PKM extraction successful: {analysis['pkm_extraction_success']}")
    print(f"   Records missing DESCRIPTION: {analysis['missing_description']}")
    print(f"   Records with both USER fields: {analysis['records_with_both_fields']}")
    
    if analysis['records_with_both_fields'] > 0:
        same_pct = (analysis['same_user_count'] / analysis['records_with_both_fields']) * 100
        diff_pct = (analysis['different_user_count'] / analysis['records_with_both_fields']) * 100
        
        print(f"\n👥 User Comparison Results:")
        print(f"   Same user (USER_GROUP_ID_TO == USER_ID_FROM): {analysis['same_user_count']} ({same_pct:.1f}%)")
        print(f"   Different users: {analysis['different_user_count']} ({diff_pct:.1f}%)")
        
        print(f"\n✅ Sample cases where users are SAME:")
        for sample in analysis['samples_same'][:3]:
            print(f"   PKM: {sample['pkm']}")
            print(f"      TO: {sample['user_to']}")
            print(f"      FROM: {sample['user_from']}")
            print()
        
        if analysis['samples_different']:
            print(f"⚠️  Sample cases where users are DIFFERENT:")
            for sample in analysis['samples_different'][:3]:
                print(f"   PKM: {sample['pkm']}")
                print(f"      TO: {sample['user_to']}")
                print(f"      FROM: {sample['user_from']}")
                print()
        else:
            print("   (No cases found with different users)")
    
    print("\n" + "="*80)
    
    # Conclusion
    if analysis['different_user_count'] == 0 and analysis['records_with_both_fields'] > 0:
        print("\n✅ CONCLUSION: USER_GROUP_ID_TO and USER_ID_FROM are ALWAYS the same person")
        print("   → queryId=3 can be used as authoritative source for charges")
    elif analysis['different_user_count'] > 0:
        print("\n⚠️  CONCLUSION: USER_GROUP_ID_TO and USER_ID_FROM are NOT always the same")
        print("   → Need to determine which field represents the charge/assignment")
    else:
        print("\n❓ CONCLUSION: Insufficient data to determine relationship")
    
    return analysis


def export_comparison_table(analysis: Dict, filename: str = None) -> None:
    """Export comparison details to JSON for reference."""
    if not filename:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"data/outputs/queryid3_user_comparison_{timestamp}.json"
    
    import os
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_records': analysis['total_records'],
            'pkm_extraction_success': analysis['pkm_extraction_success'],
            'records_with_both_fields': analysis['records_with_both_fields'],
            'same_user_count': analysis['same_user_count'],
            'different_user_count': analysis['different_user_count'],
        },
        'details': analysis['user_comparison_details']
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Exported comparison details to: {filename}")


def main():
    """Main execution."""
    try:
        # Load config
        root = get_project_root()
        cfg_path = os.path.join(root, 'config', 'config.yaml')
        config = load_config(cfg_path)
        
        print("🔍 Initializing PKM Monitor...")
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
        
        print("🔐 Logging in...")
        if not monitor.logged_in and not monitor.login():
            print("❌ Login failed")
            return
        
        print("✅ Logged in\n")
        
        print("📥 Fetching queryId=3 records...")
        records = fetch_queryid3_records(monitor, limit=100)
        
        if not records:
            print("❌ No records fetched from queryId=3")
            return
        
        print("\n🔬 Analyzing USER_GROUP_ID_TO vs USER_ID_FROM...")
        analysis = analyze_user_fields(records)
        
        # Print results
        print_analysis(analysis)
        
        # Export for reference
        export_comparison_table(analysis)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
