# FAQs: Case Correlation & OTS Assignment Tracking

## Q1: Τι είναι τα OTS Incoming?
**A**: OTS (Πρωτόκολλο) είναι ένα σύστημα που παρακολουθεί την ανάθεση υποθέσεων σε τμήματα. Κάθε εισερχόμενη υπόθεση από το Portal εισέρχεται στο OTS για δρομολόγηση και χρέωση σε τμήμα.

---

## Q2: Γιατί το `explore_ots_incoming.py` δεν δουλευε και έδινε JWT error;
**A**: Το script προσπαθούσε να χρησιμοποιήσει το **detail endpoint** (`/fetchDataTableRecord`) το οποίο έχει διαφορετικές απαιτήσεις authentication από το list endpoint.

**Λύση**: Δεν χρειαζόμαστε το detail endpoint! Το list endpoint (queryId=2) παρέχει **όλες** τις πληροφορίες που χρειάζονται:
- USER_GROUP_ID_TO (τμήμα)
- USER_ID_FROM (ποίος ανάθεσε)  
- DATE_START_ISO (ημερομηνία ανάθεσης)
- ACTIONS (κατάσταση)

---

## Q3: Ποιο είναι το σωστό setup για να τρέξω το updated script;
**A**: 
```bash
cd src
python explore_ots_incoming.py
```

Θα δεις:
- ✅ 68 OTS records ανακτημένα
- ✅ 14 πεδία διαθέσιμα
- ✅ 50 δείγμα εγγραφών
- ✅ 16 διαφορετικά τμήματα
- ✅ Στατιστικά αποθηκευμένα

---

## Q4: Ποια δεδομένα χρησιμοποιούμε για τη συσχέτιση Portal ↔ OTS;

**A**: Το κλειδί συσχέτισης είναι το **ΠΚΜ** (Αριθμός Πρωτοκόλλου):

```
Portal Incoming:
├─ W007_P_FLD21 = "106653"  ← PKM

OTS DESCRIPTION:
└─ "Αίτημα 2026/106653 ΨΥΤΙΛΛΗΣ..." ← Περιέχει PKM
```

**Match Rate**: 73.5% (50/68 OTS matches με Portal PKM)

---

## Q5: Πώς ενσωματώνω τα OTS assignments στις αναφορές;

**A**:
```python
from ots_assignments import (
    fetch_ots_assignments,
    add_assignment_info,
    format_assignment_for_display
)

# 1. Ανάκτηση OTS
ots_records, ots_by_pkm = fetch_ots_assignments(session)

# 2. Εμπλουτισμός Portal records
enriched = add_assignment_info(portal_records, ots_by_pkm)

# 3. Εμφάνιση
for rec in enriched:
    status = format_assignment_for_display(rec)
    print(f"{rec['W007_P_FLD21']} | {status}")
```

**Output**:
```
106653 | ✅ ΤΜΗΜΑ ΧΟΡΗΓΗΣΗΣ (2026-02-10) - Προς Χρέωση
105782 | ⏳ Δεν έχει χρεωθεί
```

---

## Q6: Ποιες είναι οι 3 συσχετίσεις που προσφέρουμε;

**A**:

| Layer | System | Purpose | Match |
|-------|--------|---------|-------|
| 1 | Settled Cases | Filter completed cases | 30% |
| 2 | OTS Assignments | Track assigned department | 73.5% |
| 3 | Directories | Get contact info | Always |

**Full Lifecycle**:
```
Portal Incoming
  ↓ (30% matched)
Is Settled? → YES: ✅ COMPLETED
  ↓ NO
  ↓ (73.5% matched)
Is Assigned? → YES: ⏳ IN PROGRESS (show dept)
  ↓ NO
  ↓
🔵 PENDING (await assignment)
```

---

## Q7: Τι πεδία έχει το OTS record;

**A**: 14 πεδία (από list endpoint):

```
1. USER_ID_FROM          Αναθέτων
2. COMMENTS_A            Σχόλια ανάθεσης
3. XR_ACTIONS            Προτεραιότητα
4. ACTIONS               Ενέργειες (κατάσταση)
5. USER_GROUP_ID_TO      Ανατέθηκε σε... (DEPARTMENT)
6. DATE_START            Ημ/νία ανάθεσης
7. DATE_END              Ημ/νία λήξης
8. USER_ID_LOCKED        Χρήστης που δέσμευσε
9. USER_ID_FINISHD       Χρήστης που διεκπεραίωσε
10. DATE_FINISHED        Ημ/νία διεκπεραίωσης
11. FINISHED_STATUS_ID   Τρόπος διεκπεραίωσης
12. COMMENTS_B           Σχόλια δεσμ./διεκπ.
13. P_PROC_MAIN_ID       Διαδικασία
14. P_PROC_STEPS_STEPID  Βήμα
```

---

## Q8: Γιατί κάποιες εγγραφές δεν έχουν USER_ID_LOCKED;

**A**: Διότι δεν έχουν ακόμα φτάσει στο στάδιο "δέσμευσης" από χρήστη. Η κατάσταση "Προς Χρέωση" σημαίνει ότι περιμένει να ανατεθεί σε ένα συγκεκριμένο υπάλληλο.

**Statuses Found**:
- **"Προς Χρέωση"** = Περιμένει επεξεργασία από τμήμα
- **"Ανάγνωση εγγράφου"** = Κάποιος υπάλληλος το διαβάζει

---

## Q9: Πώς παίρνω το όνομα του υπαλλήλου που έχει τη υπόθεση;

**A**: Δύο τρόποι:

**Option 1: USER_ID_FROM (ποίος ανάθεσε)**
```python
assigned_by = rec.get('USER_ID_FROM')  # "Administrator"
```

**Option 2: USER_ID_LOCKED (ποίος δεσμεύτηκε - αν υπάρχει)**
```python
locked_by = rec.get('USER_ID_LOCKED')  # Συνήθως κενό ("") αν στάδιο Προς Χρέωση
```

**Limitation**: Τα user IDs στο OTS είναι usernames, όχι full names. Για πρώτο και τελευταίο όνομα, χρειάζεται extra API call σε directory service.

---

## Q10: Ποια είναι η κατάσταση των FILES που δημιουργούνται;

**A**:

| File | Purpose | Status |
|------|---------|--------|
| `src/ots_assignments.py` | Core module | ✅ Production ready |
| `src/explore_ots_incoming.py` | Debug/analysis | ✅ Fixed (no JWT errors) |
| `src/demo_full_lifecycle.py` | Integration demo | ✅ Working |
| `src/test_ots_assignments.py` | Unit tests | ✅ Passing |
| `src/correlate_ots_portal.py` | Find matches | ✅ Shows 50/68 matches |
| `docs/OTS_INCOMING_ASSIGNMENTS.md` | User guide | ✅ Complete |
| `docs/CASE_CORRELATION_FEATURES.md` | Feature overview | ✅ Complete |
| `docs/OTS_JWT_DETAIL_ENDPOINT_EXPLANATION.md` | Issue explanation | ✅ Complete |
| `docs/IMPLEMENTATION_SUMMARY.md` | Executive summary | ✅ Complete |

---

## Q11: Πώς κάνω SLA monitoring (track if unassigned > 5 days);

**A**:
```python
from datetime import datetime, timedelta
from ots_assignments import filter_unassigned

unassigned = filter_unassigned(enriched)
threshold = datetime.now() - timedelta(days=5)

overdue = []
for rec in unassigned:
    submitted = datetime.strptime(
        rec['W007_P_FLD3'], '%d-%m-%Y %H:%M:%S'
    )
    if submitted < threshold:
        overdue.append(rec)

print(f"Cases unassigned > 5 days: {len(overdue)}")
```

---

## Q12: Τι είναι το Field `_assignment` που προσθέτουμε;

**A**: Δεν είναι πραγματικό field του API. Το προσθέτουμε εμείς κατά τον enrichment:

```python
record['_assignment'] = {
    'assigned': True/False,
    'department': 'ΤΜΗΜΑ ΧΟΡΗΓΗΣΗΣ...',
    'department_id': 100734,
    'date_assigned': '2026-02-10 23:43:13...',
    'status': 'Προς Χρέωση',
    'assigned_by': 'Administrator',
    'ots_docid': 44102
}
```

Αυτό κάνει εύκολη την πρόσβαση και τη filtering.

---

## Q13: Ποια είναι η επόμενη τάξη εργασιών;

**A**: **Priority Order**:

1. **Integrate into daily_report.py** (2-3 hours)
   - Add _assignment field
   - Display assignment status
   - Include in Excel export

2. **SLA Monitoring** (2-3 hours)
   - Alert: unassigned > 5 days
   - Alert: in progress > 30 days
   - Track by department

3. **Email Notifications** (2 hours)
   - Send when assigned
   - Email director
   - Include case details

4. **Dashboard/UI** (4+ hours)
   - Department workload view
   - SLA metrics
   - Case status color-coding

---

## Q14: Ποια APIs χρησιμοποιούμε;

**A**:

| Endpoint | Query ID | Purpose | Auth |
|----------|----------|---------|------|
| `getSearchDataByQueryId` | 6 | Portal Incoming | Session |
| `getSearchDataByQueryId` | 19 | Settled Cases | Session |
| `getSearchDataByQueryId` | 2 | OTS Assignments | Session |
| `getDirectory` | N/A | Department info | Session |
| `/fetchDataTableRecord` | - | Details | ⚠️ JWT (don't use) |

---

## Q15: Πώς monitor κατάσταση workflow;

**A**: Δες τα **ACTIONS** field:

```
Possible States:
├─ "Προς Χρέωση"         = Waiting for department processing
├─ "Ανάγνωση εγγράφου"   = Someone is reading it
└─ (Others as system evolves)

Check via:
action_status = record.get('ACTIONS')
xr_action = record.get('XR_ACTIONS')  # Priority level
```

---

## References

- **[OTS_INCOMING_ASSIGNMENTS.md](docs/OTS_INCOMING_ASSIGNMENTS.md)** - Complete guide
- **[OTS_JWT_DETAIL_ENDPOINT_EXPLANATION.md](docs/OTS_JWT_DETAIL_ENDPOINT_EXPLANATION.md)** - Technical details
- **[CASE_CORRELATION_FEATURES.md](docs/CASE_CORRELATION_FEATURES.md)** - All 3 correlations
- **[src/ots_assignments.py](src/ots_assignments.py)** - Full module code
