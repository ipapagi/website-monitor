# OTS Incoming Exploration - Detail Endpoint Issue & Solution

## The Problem

Όταν εκτελείται το `explore_ots_incoming.py`, εμφανίζεται σφάλμα:

```
❌ Αποτυχία (Status: 500)
Response: {"success":false,"processMessage":"JWT strings must contain exactly 2 period characters. Found: 0","total":0}
```

### Why Does This Happen?

**JWT Format Error**: Ένα JWT token έχει αυστηρή δομή `header.payload.signature` (3 μέρη με 2 periods)

Το σφάλμα σημαίνει:
- Ο API server περιμένει JWT token στην Authorization header
- Αλλά λαμβάνει κάτι που δεν έχει σωστή μορφή (0 periods, όχι 2)

**Root Cause**: 
1. Το **list endpoint** (`getSearchDataByQueryId` με queryId=2) χρησιμοποιεί standard session authentication
2. Το **detail endpoint** (`/services/DataServices/fetchDataTableRecord/2/{DOCID}`) έχει διαφορετικές απαιτήσεις
3. Το script προσπαθούσε να χρησιμοποιήσει το session για το detail endpoint χωρίς proper setup

---

## The Solution

### Why We Don't Need the Detail Endpoint

Το **list endpoint ήδη παρέχει όλες τις πληροφορίες**:

```python
# List endpoint columns available:
✅ USER_GROUP_ID_TO           (Department assigned to)
✅ USER_GROUP_ID_TO_ID        (Department ID)
✅ USER_ID_FROM               (Assigned by)
✅ USER_ID_FROM_ID            (User ID)
✅ USER_ID_LOCKED             (Locked by user)
✅ USER_ID_LOCKED_ID          (Locked by user ID)
✅ USER_ID_FINISHD            (Finished by user)
✅ USER_ID_FINISHD_ID         (Finished by user ID)
✅ DATE_START_ISO             (Assignment date)
✅ DATE_START                 (Formatted date)
✅ DATE_END_ISO               (End date)
✅ ACTIONS                    (Current status)
✅ XR_ACTIONS                 (Action type)
```

**Αποτέλεσμα**: Δεν χρειάζεται το detail endpoint. Ήδη έχουμε τα δεδομένα χρέωσης!

---

## What the List Endpoint Provides

### OTS Incoming Structure (50 records example)

```
Statistics from First 50 OTS Records:
───────────────────────────────────────────
✅ Total OTS records:           50
✅ With department assignment:  50 (100.0%)
✅ With assigned_by info:       50 (100.0%)
✅ With locked_user:            0 (0.0%)
✅ With finished_user:          0 (0.0%)
✅ Unique departments:          16
✅ Status types:                2

Statuses Found:
  • "Προς Χρέωση"        (Pending charging - awaiting processing)
  • "Ανάγνωση εγγράφου"  (Reading document - being processed)
```

### Example Record

```json
{
  "DOCID": 44102,
  "USER_GROUP_ID_TO": "ΤΜΗΜΑ ΧΟΡΗΓΗΣΗΣ ΑΔΕΙΩΝ ΒΙΟΜΗΧΑΝΙΑΣ, ΕΝΕΡΓΕΙΑΣ...",
  "USER_GROUP_ID_TO_ID": 100734,
  "USER_ID_FROM": "Administrator",
  "USER_ID_FROM_ID": 1001863,
  "DATE_START_ISO": "2026-02-10 23:43:13.511019",
  "DATE_START": "10-02-2026 23:43:13",
  "ACTIONS": "Προς Χρέωση",
  "XR_ACTIONS": "Κανονική",
  "STEPID": 1,
  "PTYPE_ID": 2
}
```

---

## How to Use Instead

### Option 1: Use the List Endpoint (Recommended ✅)

```python
from explored_ots_incoming import explore_ots_incoming

# Run the updated script - NO JWT errors!
result = explore_ots_incoming()

records = result['records']        # All records
columns = result['columns']        # All available fields
stats = result['stats']            # Statistics
```

### Option 2: Direct Module Usage

```python
from ots_assignments import fetch_ots_assignments, add_assignment_info
from session import PKMSession

session = PKMSession(...)
session.authenticate()

# Get OTS data (uses list endpoint internally)
ots_records, ots_by_pkm = fetch_ots_assignments(session)

# All data already there!
for rec in ots_records:
    dept = rec.get('USER_GROUP_ID_TO')       # Full department name
    date = rec.get('DATE_START_ISO')         # Assignment date
    status = rec.get('ACTIONS')              # Current status
    assigned_by = rec.get('USER_ID_FROM')    # Who assigned
```

---

## Technical Explanation

### How the List Endpoint Works

```
Client Request:
├─ POST /services/SearchServices/getSearchDataByQueryId
├─ queryId=2
├─ Session Cookie (from login)
└─ No JWT required (session-based auth)

Server Response:
├─ 200 OK
├─ data: [{DOCID, USER_GROUP_ID_TO, USER_ID_FROM, DATE_START_ISO, ...}, ...]
└─ metaData: {columns: [{dataIndex, header, type}, ...]}
```

### Why Detail Endpoint Would Fail

```
Client Request:
├─ GET /services/DataServices/fetchDataTableRecord/2/{DOCID}
├─ Authorization: ??? (No JWT in session)
└─ Expected: "Authorization: Bearer JWT_TOKEN"

Server Response:
├─ 500 Internal Server Error
└─ "JWT strings must contain exactly 2 period characters. Found: 0"
   (Trying to parse empty/invalid JWT)
```

---

## Historical Context

### What Changed

1. **Original Problem**: Needed detail endpoint to get assignment info
2. **Discovery**: Found that OTS DESCRIPTION contains PKM number
3. **Better Discovery**: List endpoint ALREADY has all assignment fields!
4. **Solution**: Use list endpoint exclusively

### Evolution of Understanding

```
Phase 1: "Need detail endpoint for assignment info"
  └─ ❌ Failed with JWT error

Phase 2: "Extract PKM from DESCRIPTION, match with Portal"
  └─ ✅ Works! (73.5% match rate)

Phase 3: "But why match? List endpoint already has assignment!"
  └─ ✅ All fields present in list data

Phase 4: "Support both - list for assignments, correlation for PKM matching"
  └─ ✅ Optimal solution (current state)
```

---

## Files Updated

```
src/explore_ots_incoming.py
├─ Removed: detail endpoint attempts
├─ Added: field analysis from list data
├─ Added: statistics generation
└─ Result: No JWT errors, better insights

src/ots_assignments.py (unchanged)
├─ Already uses list endpoint exclusively
├─ All functions work perfectly
└─ No dependency on detail endpoint

Data outputs:
├─ data/tmp/ots_incoming_columns.json    (14 columns available)
├─ data/tmp/ots_incoming_sample.json     (50 sample records)
└─ data/tmp/ots_incoming_stats.json      (statistics)
```

---

## Key Takeaway

### ✅ We Don't Need the Detail Endpoint For Assignments!

The list endpoint provides **everything**:
- Department name (USER_GROUP_ID_TO)
- Department ID (USER_GROUP_ID_TO_ID)
- Assignment date (DATE_START_ISO)
- Status (ACTIONS)
- Who assigned (USER_ID_FROM)
- And 9 more relevant fields

**Result**: 
- ✅ No authentication issues
- ✅ Faster performance (no extra API call)
- ✅ Simpler code
- ✅ Full data available

---

## Running the Corrected Script

```bash
# Run exploration (no errors!)
cd src
python explore_ots_incoming.py

# Output files created:
#   ✅ data/tmp/ots_incoming_columns.json
#   ✅ data/tmp/ots_incoming_sample.json
#   ✅ data/tmp/ots_incoming_stats.json
```

**Expected Output**:
```
1️⃣ Ανάκτηση λίστας OTS εισερχόμενων...
   ✅ Success: Σύνολο εγγραφών: 68
2️⃣ Δομή πεδίων (columns):
   ✅ 14 columns listed
3️⃣ Δείγμα εγγραφών:
   ✅ 10 sample records with full assignment info
4️⃣ ΑΝΆΛΥΣΗ ΠΕΔΊΩΝ ΓΙΑ ΧΡΈΩΣΗ & ΑΝΆΘΕΣΗ
   ✅ 11 assignment-related fields found
   ✅ 16 unique departments
   ✅ 2 status types
```

---

## References

- **Fixed Script**: [src/explore_ots_incoming.py](../src/explore_ots_incoming.py)
- **OTS Module**: [src/ots_assignments.py](../src/ots_assignments.py)
- **Full Guide**: [docs/OTS_INCOMING_ASSIGNMENTS.md](../docs/OTS_INCOMING_ASSIGNMENTS.md)
- **Architecture**: [docs/CASE_CORRELATION_ARCHITECTURE.md](../docs/CASE_CORRELATION_ARCHITECTURE.md)
