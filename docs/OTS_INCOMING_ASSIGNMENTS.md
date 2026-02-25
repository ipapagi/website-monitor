# OTS INCOMING ASSIGNMENTS - Complete Integration Guide

## Overview

OTS Incoming (Πρωτόκολλο) είναι ένα σύστημα που παρακολουθεί την ανάθεση υποθέσεων σε τμήματα. Αυτή το documentation
εξηγεί πώς να ενσωματώσετε το OTS με τα incoming Portal records για να βλέπετε ποιος έχει αναλάβει κάθε υπόθεση.

## Quick Facts

- **OTS Total Records**: 68
- **Portal Incoming**: 175+ 
- **Match Rate**: 73.5% (μέσω ΠΚΜ στο DESCRIPTION field)
- **Correlation Key**: `W007_P_FLD21` (Portal PKM) ↔ OTS `DESCRIPTION` field

## Data Structure

### Portal Incoming Fields (queryId=6)
```
W007_P_FLD21  = Αριθμός ΠΚΜ (π.χ. "106653")
W007_P_FLD13  = Συναλλασσόμενος (Party name)
W007_P_FLD3   = Ημερομηνία υποβολής
W007_P_FLD8   = Διαδικασία
W007_P_FLD53  = Αριθμός ΚΣΗΔΕ (alternative ID)
DOCID         = Portal document ID
```

### OTS Incoming Fields (queryId=2)
```
DOCID             = OTS document ID
DESCRIPTION       = Contains PKM: "Αίτημα 2026/106653 ΨΥΤΙΛΛΗΣ-136290675"
USER_GROUP_ID_TO  = Assignment department (full name)
USER_GROUP_ID_TO_ID = Department ID
DATE_START_ISO    = Assignment date
DATE_START        = Formatted date (DD-MM-YYYY HH:MM:SS)
ACTIONS           = Status (π.χ. "Προς Χρέωση")
USER_ID_FROM      = Who assigned (usually "Administrator")
USER_ID_FROM_ID   = User ID
INSTANCEID        = Workflow instance ID
ROUTID            = Route ID
```

## Usage Examples

### Basic Workflows

#### 1. Fetch and Setup
```python
from session import PKMSession
from ots_assignments import fetch_ots_assignments, add_assignment_info
from config import INCOMING_DEFAULT_PARAMS

session = PKMSession(...)
session.authenticate()

# Step 1: Get OTS
ots_records, ots_by_pkm = fetch_ots_assignments(session)

# Step 2: Get Portal incoming
portal_params = INCOMING_DEFAULT_PARAMS.copy()
portal_data = session.fetch_data(portal_params)
portal_records = portal_data.get('data', [])

# Step 3: Enrich Portal records with OTS data
enriched = add_assignment_info(portal_records, ots_by_pkm)
```

#### 2. Get Assignment for Specific Record
```python
from ots_assignments import get_assignment_info

incoming_record = portal_records[0]
assignment = get_assignment_info(incoming_record, ots_by_pkm)

if assignment:
    print(f"Department: {assignment['department_short']}")
    print(f"Assigned at: {assignment['date_assigned_formatted']}")
else:
    print("Not yet assigned")
```

#### 3. Filter by Assignment Status
```python
from ots_assignments import filter_assigned, filter_unassigned

assigned = filter_assigned(enriched)
unassigned = filter_unassigned(enriched)

print(f"Assigned: {len(assigned)}")
print(f"Pending assignment: {len(unassigned)}")
```

#### 4. Get Statistics
```python
from ots_assignments import get_assignment_statistics

stats = get_assignment_statistics(enriched)

print(f"Total: {stats['total']}")
print(f"Assigned: {stats['assigned']} ({stats['assigned_percentage']:.1f}%)")
print(f"Departments: {stats['unique_departments']}")

# By department breakdown
for dept, count in stats['by_department'].items():
    print(f"  {count:3} | {dept}")
```

#### 5. Display Assignments
```python
from ots_assignments import format_assignment_for_display

for record in assigned:
    pkm = record.get('W007_P_FLD21')
    display = format_assignment_for_display(record)
    print(f"ΠΚΜ {pkm}: {display}")
    # ΠΚΜ 106653: ✅ ΤΜΗΜΑ ΧΟΡΗΓΗΣΗΣ ΑΔΕΙΩΝ... (2026-02-10) - Προς Χρέωση
```

#### 6. Simplify OTS Records
```python
from ots_assignments import simplify_ots_record

for ots_rec in ots_records[:5]:
    simplified = simplify_ots_record(ots_rec)
    print(f"{simplified['pkm']} -> {simplified['department_short']}")
```

## Integration with Reports

### Daily Report Enhancement
```python
from ots_assignments import add_assignment_info, get_assignment_statistics
from daily_report import generate_daily_report

# Get daily data
session = PKMSession(...)
incoming = session.fetch_data(INCOMING_DEFAULT_PARAMS).get('data', [])
ots_records, ots_by_pkm = fetch_ots_assignments(session)

# Enrich
enriched = add_assignment_info(incoming, ots_by_pkm)

# Generate report with assignment column
report = generate_daily_report(enriched)
# Now includes: ✅ or ⏳ status in assignment column
```

### Weekly Report with Department Breakdown
```python
from ots_assignments import get_assignment_statistics

enriched = add_assignment_info(weekly_incoming, ots_by_pkm)
stats = get_assignment_statistics(enriched)

# Report header
print(f"Weekly Summary")
print(f"Assigned: {stats['assigned']} / {stats['total']} ({stats['assigned_percentage']:.1f}%)")
print(f"\nWorkload by Department:")

for dept, count in sorted(stats['by_department'].items(), key=lambda x: x[1], reverse=True):
    print(f"  {count:3} cases | {dept}")
```

### SLA Tracking
```python
from datetime import datetime, timedelta

# Requirements:
# - SLA = 5 days to assign
# - SLA = 30 days to complete

unassigned = filter_unassigned(enriched)
assigned = filter_assigned(enriched)

# SLA 1: Not assigned yet but submitted > 5 days ago
overdue_assign = []
cutoff = datetime.now() - timedelta(days=5)

for rec in unassigned:
    submitted = rec.get('W007_P_FLD3')  # "DD-MM-YYYY ..."
    # Parse and compare...
    overdue_assign.append(rec)

# SLA 2: Assigned but not completed > 30 days
overdue_complete = []
cutoff_complete = datetime.now() - timedelta(days=30)

for rec in assigned:
    assigned_date = rec['_assignment']['date_assigned']
    # Parse and compare...
```

## Data Flow

```
Portal Incoming Records (queryId=6)
        ↓
   W007_P_FLD21 (PKM: "106653")
        ↓
[OTS Mapping: PKM → assign details]
        ↓
   OTS DESCRIPTION contains "Αίτημα 2026/106653"
        ↓
   add_assignment_info()
        ↓
   _assignment field added to Portal record
        ↓
   Reports, filtering, statistics ready
```

## Key Functions Reference

| Function | Purpose | Returns |
|----------|---------|---------|
| `fetch_ots_assignments(session)` | Get OTS data | `(ots_records, ots_by_pkm)` |
| `add_assignment_info(records, ots_by_pkm)` | Enrich records | Records with `_assignment` field |
| `get_assignment_info(record, ots_by_pkm)` | Get assignment for one | Assignment dict or None |
| `filter_assigned(enriched)` | Get assigned only | List of assigned records |
| `filter_unassigned(enriched)` | Get unassigned only | List of unassigned records |
| `get_assignment_statistics(enriched)` | Calculate stats | Stats dict |
| `format_assignment_for_display(record)` | Format for UI | "✅ DEPT (DATE) - STATUS" |
| `simplify_ots_record(ots)` | Clean OTS record | Readable dict |

## Assignment Flow States

1. **New Portal Incoming** → `W007_P_FLD21` created
2. **Not Yet in OTS** → `_assignment.assigned = False` 
3. **Assigned to Department** → `_assignment.assigned = True`, department set
4. **Status: Προς Χρέωση** → Waiting in department queue
5. **Status: Ανάθεση** → Actually processing
6. **Status: Ολοκληρώση** → Completed (if in OTS)

## Common Patterns

### Find all unassigned
```python
unassigned = filter_unassigned(enriched)
for rec in unassigned:
    print(rec['W007_P_FLD21'], rec['W007_P_FLD13'])
```

### Find by department
```python
target_dept = "ΤΜΗΜΑ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ"
dept_records = [r for r in assigned 
               if target_dept in r['_assignment'].get('department', '')]
```

### Find recently assigned (< 5 days)
```python
from datetime import datetime, timedelta

recent = []
cutoff = datetime.now() - timedelta(days=5)

for rec in assigned:
    assigned_date = datetime.fromisoformat(
        rec['_assignment']['date_assigned']
    )
    if assigned_date > cutoff:
        recent.append(rec)
```

### Export for Excel
```python
import pandas as pd
from ots_assignments import format_assignment_for_display

df_data = []
for rec in enriched:
    df_data.append({
        'PKM': rec.get('W007_P_FLD21'),
        'Party': rec.get('W007_P_FLD13'),
        'Procedure': rec.get('W007_P_FLD8'),
        'Submitted': rec.get('W007_P_FLD3'),
        'Assignment': format_assignment_for_display(rec)
    })

df = pd.DataFrame(df_data)
df.to_excel('assignments.xlsx', index=False)
```

## Troubleshooting

### No matches found
**Issue**: All `_assignment.assigned = False`

**Check**:
1. Verify PKM format in Portal: should be numeric like "106653"
2. Verify OTS DESCRIPTION contains "Αίτημα 2026/NNNNNN"
3. Check dates are current (OTS might be filtered by date range)
4. Verify session has access to both queryIds (6 and 2)

**Solution**:
```python
# Debug: Show what we're looking for
for ots in ots_records[:3]:
    desc = ots['DESCRIPTION']
    import re
    match = re.search(r'Αίτημα\s+\d+/(\d+)', desc)
    print(f"OTS: {desc} → PKM: {match.group(1) if match else 'NO MATCH'}")

for portal in portal_records[:3]:
    print(f"Portal: {portal['W007_P_FLD21']}")
```

### Assignment info is None
**Issue**: `get_assignment_info()` returns None

**Cause**: Record PKM not in `ots_by_pkm` dictionary

**Solution**:
```python
# Check if PKM exists in mapping
pkm = record.get('W007_P_FLD21')
if pkm in ots_by_pkm:
    print("Found in OTS")
else:
    print(f"PKM {pkm} not in OTS mapping")
    # Check if it's in full OTS records
    for ots in ots_records:
        if pkm in ots.get('DESCRIPTION', ''):
            print(f"Found but extraction failed!")
```

### Department name truncated
**Issue**: `_assignment.department_short` is "Άγνωστο"

**Cause**: Missing USER_GROUP_ID_TO in OTS record

**Check**:
```python
for ots in ots_records:
    if not ots.get('USER_GROUP_ID_TO'):
        print(f"Missing department for DOCID {ots.get('DOCID')}")
```

## Statistics from Test Run

```
OTS Total:                  68 records
Portal Incoming:            100+ records tested
Successfully Matched:       50 (73.5% of OTS)
Unassigned (sample 50):     42 (84%)
Assigned (sample 50):       8 (16%)
Unique Departments:         10+
OTS without Portal match:   2 (3%)
```

## Related Documentation

- [SETTLED_INCOMING_CORRELATION.md](SETTLED_INCOMING_CORRELATION.md) - Filter out settled cases
- [DIRECTORIES_MANAGEMENT.md](DIRECTORIES_MANAGEMENT.md) - Department/directory API
- [DIRECTORY_EMAILS.md](DIRECTORY_EMAILS.md) - Send emails to assigned departments
- [API_COMPLETE_GUIDE.md](API_COMPLETE_GUIDE.md) - All API endpoints

## See Also

- `src/ots_assignments.py` - Core OTS module
- `src/correlate_ots_portal.py` - Correlation script
- `src/test_ots_assignments.py` - Integration test
