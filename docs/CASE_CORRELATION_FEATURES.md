# Case Correlation Features

## Overview

Το σύστημα παρέχει **3 ανεξάρτητες συσχέτιση** για παρακολούθηση της πλήρους κύκλου ζωής υποθέσεων:

```
Incoming (Portal) 
    ↓
Settled Cases (Διεκπεραιωμένες) ← Remove completed ✓
    ↓
Assigned to Department (OTS) ← Track status ✓
    ↓
Pending / Active
```

## Three Correlation Systems

### 1. Settled Cases Correlation
**File**: `src/settled_cases.py` | **Doc**: `docs/SETTLED_INCOMING_CORRELATION.md`

**Purpose**: Filter out settled/completed cases from reports

**Key Function**: `filter_out_settled_from_incoming()`
```python
# Remove settled cases from incoming
active_cases = filter_out_settled_from_incoming(incoming, settled)

# Result: 35 active cases from 50 tested (30% were settled)
```

**Stats**:
- Correlation Field: W007_P_FLD7 (Αφορά Υπόθεση) contains case codes
- Match Key: W001_P_FLD2 (Case code in settled)
- Match Rate: 30% (15/50 incoming are settled)
- Use: Remove completed cases before reporting

---

### 2. OTS Assignments (NEW)
**File**: `src/ots_assignments.py` | **Doc**: `docs/OTS_INCOMING_ASSIGNMENTS.md`

**Purpose**: Track which department has assigned a case and its status

**Key Function**: `add_assignment_info()`
```python
# Enrich incoming with assignment details
enriched = add_assignment_info(incoming, ots_by_pkm)

# Result: _assignment field contains department, date, status
# Example: ✅ ΤΜΗΜΑ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ (2026-02-10) - Προς Χρέωση
```

**Stats**:
- OTS Total: 68 records
- Match Rate: 73.5% (50/68 have Portal matches via PKM)
- Correlation Field: W007_P_FLD21 (PKM) in DESCRIPTION
- Example: "Αίτημα 2026/106653 ΨΥΤΙΛΛΗΣ" contains PKM 106653
- Departments: 10+
- Unassigned Rate: 84% of sample still pending assignment

**Workflow States**:
- `Προς Χρέωση` = Queued for processing
- `Ανάθεση` = Being processed
- `Ολοκληρώση` = Completed (final status)

---

### 3. Directory/Department Lookup
**Files**: `src/directories_manager.py`, `src/directory_emails.py`

**Purpose**: Get employee contact info for assigned departments

**For Integration**:
```python
from directories_manager import get_directory_by_id

dept_id = assignment['department_id']  # e.g. 100734
directory = get_directory_by_id(dept_id)

# Result: director, heads, emails, phone available
```

---

## Correlation Chaining (Full Lifecycle)

### Get Complete Status
```python
from settled_cases import get_settled_for_incoming
from ots_assignments import get_assignment_info
from directories_manager import get_directory_by_id

def get_full_case_status(portal_record, settled_by_pkm, ots_by_pkm):
    """Get complete lifecycle of a case"""
    pkm = portal_record.get('W007_P_FLD21')
    
    # Check 1: Is it settled?
    settled = get_settled_for_incoming(portal_record, settled_by_pkm)
    if settled:
        return {
            'status': '✅ COMPLETED',
            'settled_date': settled.get('W001_P_FLD3'),
            'final_status': settled.get('W001_P_FLD12'),
            'case_code': settled.get('W001_P_FLD2')
        }
    
    # Check 2: Is it assigned?
    assignment = get_assignment_info(portal_record, ots_by_pkm)
    if assignment:
        # Get director contact
        directory = get_directory_by_id(assignment['department_id'])
        return {
            'status': '⏳ IN PROGRESS',
            'department': assignment['department_short'],
            'assigned_date': assignment['date_assigned'],
            'director': directory.get('director'),
            'director_email': directory.get('director_email')
        }
    
    # Check 3: Not yet assigned
    return {
        'status': '🔴 PENDING',
        'message': 'Not yet assigned to department'
    }

# Usage
for record in incoming[:10]:
    status = get_full_case_status(record, settled_by_pkm, ots_by_pkm)
    print(f"{record['W007_P_FLD21']}: {status['status']}")
```

---

## Quick Reference by Use Case

### Use Case: Generate Daily Report
Shows only **active** cases with **assignment status**

```python
from settled_cases import filter_out_settled_from_incoming
from ots_assignments import add_assignment_info, format_assignment_for_display

# 1. Remove settled
active = filter_out_settled_from_incoming(incoming, settled)

# 2. Add assignment info
enriched = add_assignment_info(active, ots_by_pkm)

# 3. Display
for rec in enriched:
    print(f"{rec['W007_P_FLD21']} | {rec['W007_P_FLD13'][:30]} | {format_assignment_for_display(rec)}")
```

**Output Example**:
```
106653 | ΚΡΙΝΟΣ ΨΥΤΙΛΛΗΣ (Πολίτης)    | ✅ ΤΜΗΜΑ ΧΟΡΗΓΗΣΗΣ (2026-02-10)
106652 | ΚΡΙΝΟΣ ΨΥΤΙΛΛΗΣ (Πολίτης)    | ✅ ΤΜΗΜΑ ΧΟΡΗΓΗΣΗΣ (2026-02-10)
105782 | ΜΑΡΙΑ ΜΟΥΡΑΤΙΔΟΥ (Εσ. χρήσης) | ⏳ Δεν έχει χρεωθεί
```

---

### Use Case: Track Department Workload

```python
from ots_assignments import add_assignment_info, get_assignment_statistics, filter_assigned

enriched = add_assignment_info(incoming, ots_by_pkm)
stats = get_assignment_statistics(enriched)

print("Department Workload")
print("-" * 50)

for dept, count in sorted(stats['by_department'].items(), key=lambda x: x[1], reverse=True):
    print(f"{count:3} cases: {dept}")

print(f"\nSummary:")
print(f"Total assigned: {stats['assigned']}/{stats['total']} ({stats['assigned_percentage']:.1f}%)")
print(f"Pending assignment: {stats['unassigned']} ({stats['unassigned_percentage']:.1f}%)")
```

---

### Use Case: SLA Monitoring

```python
from datetime import datetime, timedelta
from ots_assignments import add_assignment_info, filter_unassigned

enriched = add_assignment_info(incoming, ots_by_pkm)
unassigned = filter_unassigned(enriched)

# SLA: Must assign within 5 days
sla_days = 5
overdue = []

for rec in unassigned:
    submitted = datetime.strptime(rec['W007_P_FLD3'], '%d-%m-%Y %H:%M:%S')
    if (datetime.now() - submitted).days > sla_days:
        overdue.append(rec)

print(f"📊 SLA Report: Assignment within {sla_days} days")
print(f"Overdue: {len(overdue)} cases")
for rec in overdue[:5]:
    submitted = rec['W007_P_FLD3']
    print(f"  {rec['W007_P_FLD21']} | Submitted {submitted}")
```

---

### Use Case: Export to Excel with Full Status

```python
import pandas as pd
from settled_cases import filter_out_settled_from_incoming, get_settled_for_incoming
from ots_assignments import add_assignment_info, format_assignment_for_display

# Prepare data
enriched = add_assignment_info(
    filter_out_settled_from_incoming(incoming, settled),
    ots_by_pkm
)

# Build export
export_data = []
for rec in enriched:
    export_data.append({
        'ΠΚΜ': rec.get('W007_P_FLD21'),
        'Συναλλασσόμενος': rec.get('W007_P_FLD13'),
        'Ημ/νία Υποβολής': rec.get('W007_P_FLD3'),
        'Διαδικασία': rec.get('W007_P_FLD8'),
        'Ανάθεση': format_assignment_for_display(rec)
    })

df = pd.DataFrame(export_data)
df.to_excel('cases_status.xlsx', index=False)
```

---

## Integration Checklist

- [ ] `settled_cases.py` - Filter settled cases
  - [ ] Load settled data (queryId=19)
  - [ ] Add to daily_report.py
  - [ ] Test with 50 sample cases

- [ ] `ots_assignments.py` - Track assignments
  - [ ] Load OTS data (queryId=2)
  - [ ] Enrich incoming records
  - [ ] Add to report display
  - [ ] Test statistics

- [ ] `directories_manager.py` - Get contact info
  - [ ] Link assignment department_id
  - [ ] Get director contact
  - [ ] Add to email distribution

- [ ] Reports Integration
  - [ ] Daily report shows assignment status
  - [ ] Weekly report shows SLA metrics
  - [ ] Excel export includes all fields

- [ ] Notifications
  - [ ] Alert for unassigned (> 5 days pending)
  - [ ] Alert for overdue completion (> 30 days)
  - [ ] Email director if assigned to department

---

## Performance Notes

**Current Match Rates**:
- Settled correlation: **30%** (cases stay active ~70%)
- OTS assignment: **73.5%** (most have department tracked)
- Overall active cases: ~60% (30% settled + 10% lost overlap)

**Data Sizes**:
- Incoming: 175+ records
- Settled: 55 records
- OTS: 68 records
- Daily incoming: ~50-100 new cases

**Query Speed**:
- fetch_ots_assignments(): ~1-2 seconds
- add_assignment_info(100 records): ~10ms
- get_assignment_statistics(): ~5ms

---

## Files Reference

```
docs/
  ├── OTS_INCOMING_ASSIGNMENTS.md    ← Detailed OTS guide
  ├── SETTLED_INCOMING_CORRELATION.md ← Detailed settlement guide
  ├── CASE_CORRELATION_FEATURES.md   ← This file
  └── ...

src/
  ├── ots_assignments.py              ← OTS module (NEW)
  ├── settled_cases.py                ← Settled cases module
  ├── correlate_ots_portal.py         ← Correlation script (debug)
  ├── directories_manager.py          ← Department lookups
  ├── daily_report.py                 ← Integration point
  └── ...

data/tmp/
  ├── ots_portal_correlation.json     ← 50 matched records
  ├── ots_incoming_columns.json       ← OTS structure
  └── ...
```

---

## Next Steps

1. **Integrate OTS into daily_report.py**: Add assignment column
2. **Add SLA monitoring**: Track unassigned > 5 days, completed > 30 days
3. **Department notifications**: Email directors of assigned cases
4. **User interface**: Dashboard showing department workload
5. **Historical analysis**: Track average assignment time per department
