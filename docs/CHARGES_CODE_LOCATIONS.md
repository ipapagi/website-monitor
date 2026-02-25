# ΧΡΕΩΣΕΙΣ - ΑΚΡΙΒΕΣ ΚΩΔΙΚΑ ΑΝΑ ΑΡΧΕΙΟ

## 📁 ΑΡΧΕΙΟ 1: `src/charges.py` (ΝΕΟ - 235 γραμμές)

**ΑΡΧΕΙΑΚΗ ΚΑΤΑΣΤΑΣΗσ: ΝΕΟ ΑΡΧΕΙΟ**

### Ποια Δεδομένα Εισέρχονται:
- API Response από queryId=19 (55 records)
- DESCRIPTION field με κείμενο όπως: `"Αίτημα 2026/106653 ΚΗΠΟΣ..."`
- W001_P_FLD10 με όνομα υπαλλήλου

### Ποια Δεδομένα Εξέρχονται:
- `charges_by_pkm`: Dict με PKM → charge_record mapping
- Κάθε record εμπλουτίζεται με `_charge` field

### Κρίσιμες Συναρτήσεις:

```python
# ΓΡΑΜΜΉ 28-49: fetch_charges()
def fetch_charges(session) -> Tuple[List[dict], Dict[str, dict]]:
    charges_data = session.fetch_data(CHARGES_PARAMS)
    charges_records = charges_data.get('data', []) if charges_data and charges_data.get('success') else []
    
    # Δημιουργία mapping από PKM
    charges_by_pkm = {}
    for rec in charges_records:
        # Δοκιμή 1: Από W007_P_FLD21
        pkm = str(rec.get('W007_P_FLD21', '')).strip()
        
        # Δοκιμή 2: Εξαγωγή από DESCRIPTION
        if not pkm:
            pkm = _extract_pkm_from_description(rec.get('DESCRIPTION', ''))
        
        if pkm:
            charges_by_pkm[pkm] = rec  # ← ΑΠΟΘΗΚΕΥΣΗ ΣΤΟ DICT
    
    return charges_records, charges_by_pkm
```

---

## 📁 ΑΡΧΕΙΟ 2: `src/daily_report.py`

**ΓΡΑΜΜΕΣ 45-67: ΣΥΝΑΡΤΗΣΗ `def _prepare_incoming()`**

### ΠΡΟΣΘΕΤΟΣ ΚΩΔΙΚΑΣ (Γραμμές 110-123):

```python
# ← Πριν αυτό ήταν το enrich_record_details
    # Εμπλουτισμός εγγραφών που λείπουν πληροφορίες
    to_enrich = [r for r in records if not r.get('procedure') or not r.get('directory')]
    if to_enrich:
        enrich_record_details(monitor, to_enrich)

    # 🔴 ΝΕΑ ΓΡΑΜΜΗ: Ανάκτηση χρεώσεων και εμπλουτισμός records
    try:
        from charges import fetch_charges, add_charge_info
        print("📋 Ανάκτηση χρεώσεων υπαλλήλων...")
        charges_records, charges_by_pkm = fetch_charges(monitor)
        print(f"   Βρέθηκαν {len(charges_records)} χρεώσεις")
        records = add_charge_info(records, charges_by_pkm)
        print(f"   ✅ Εμπλουτισμός με χρεώσεις ολοκληρώθηκε")
    except Exception as exc:
        print(f"   ⚠️  Αποτυχία ανάκτησης χρεώσεων: {exc}")
        # Συνεχίζουμε χωρίς χρεώσεις

    changes = compare_incoming_records(records, prev_snap)
```

### Ροή Εκτέλεσης:
1. `fetch_charges(monitor)` → Καλει src/charges.py
2. `add_charge_info(records, charges_by_pkm)` → Εμπλουτίζει κάθε record
3. Το `records` list τώρα έχει `_charge` field σε κάθε element

---

## 📁 ΑΡΧΕΙΟ 3: `src/xls_export.py`

**ΑΛΛΑΓΗ 1 - ΓΡΑΜΜΗ 39: Προσθήκη στήλης**

```python
def _write_sheet(ws, rows: List[Dict], title: str):
    # ← ΤΡΟΠΟΠΟΙΗΜΕΝΗ ΓΡΑΜΜΗ
    headers = ["Δ/νση", "Αρ. Πρωτοκόλλου", "Διαδικασία", "Συναλλασσόμενος", "Ανάθεση σε"]
    # ↑ Προστέθηκε "Ανάθεση σε" στο τέλος
```

**ΑΛΛΑΓΗ 2 - ΓΡΑΜΜΕΣ 58-65: Εξαγωγή employee από _charge**

```python
    col_vals = [[], [], [], [], []]  # ← 5 columns instead of 4
    for rec in rows_sorted:
        col_vals[0].append(rec.get("directory", ""))
        col_vals[1].append(_format_protocol(rec))
        col_vals[2].append(rec.get("procedure", ""))
        col_vals[3].append(rec.get("party", ""))
        # 🔴 ΝΕΑΣ ΓΡΑΜΜΕΣ:
        charge_info = rec.get("_charge", {})
        employee = charge_info.get("employee", "") if charge_info.get("charged") else ""
        col_vals[4].append(employee)  # ← 5η στήλη
```

**ΑΛΛΑΓΗ 3 - ΓΡΑΜΜΕΣ 69-75: Loop για 5 στήλες**

```python
    for idx in range(5):  # ← Changed from 4 to 5
        max_len = max([len(str(v)) for v in (col_vals[idx] + [headers[idx]])], default=len(headers[idx]))
        max_width = [100, 40, 120, 60, 50][idx]  # ← Added 50 for new column
        width_chars = min(max_len + 2, max_width)
        col_letter = chr(ord("A") + idx)
        ws.column_dimensions[col_letter].width = width_chars

    r = 3
    for i in range(len(rows_sorted)):
        ws.cell(row=r, column=1, value=col_vals[0][i])
        ws.cell(row=r, column=2, value=col_vals[1][i])
        ws.cell(row=r, column=3, value=col_vals[2][i])
        ws.cell(row=r, column=4, value=col_vals[3][i])
        ws.cell(row=r, column=5, value=col_vals[4][i])  # ← 🔴 ΝΕΑ ΓΡΑΜΜΗ
        r += 1
```

---

## 📁 ΑΡΧΕΙΟ 4: `src/incoming.py` (Χωρίς αλλαγές)

**Σ Χρησιμοποιούνται ήδη υπάρχοντες συναρτήσεις:**

- `save_incoming_snapshot()`: Αποθηκεύει τα records στο JSON file
  - **Αυτόματα** αποθηκεύει και τα `_charge` fields!
  - Γίνεται στη γραμμή: `json.dump(payload, f, ensure_ascii=False, indent=2)`

```python
def save_incoming_snapshot(date_str, records):
    """Αποθηκεύει snapshot"""
    payload = {'date': date_str, 'count': len(records), 'records': records}
    # ↑ records = 177 items με _charge field το καθένα
    with open(get_incoming_snapshot_path(date_str), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    # ↑ Αποθήκευση στο JSON (data/incoming_requests/2026-02-16.json)
```

---

## 📊 ΠΙΝΑΚΑΣ ΣΥΝΟΨΗΣ - ΠΟΥ ΜΠΑΙΝΟΥΝ ΟΙ ΧΡΕΩΣΕΙΣ

| Βήμα | Αρχείο | Συνάρτηση | Ενέργεια | Αποτέλεσμα |
|------|--------|-----------|---------|-----------|
| 1 | session.py | login() | Σύνδεση | Session |
| 2 | incoming.py | fetch_incoming_records() | API call queryId=6 | 177 records |
| 3 | incoming.py | simplify_incoming_records() | Εξαγωγή πεδίων | Simplified records |
| 4 | api.py | enrich_record_details() | Προσθήκη procedure/directory | Enriched records |
| **5A** | **charges.py** | **fetch_charges()** | **API call queryId=19** | **55 charges, charges_by_pkm dict** |
| **5B** | **charges.py** | **add_charge_info()** | **Ταίριασμα & _charge field** | **177 records + _charge** |
| 6 | test_users.py | classify_records() | Κατάταξη | real_new, test_new |
| 7 | incoming.py | save_incoming_snapshot() | Αποθήκευση JSON | 2026-02-16.json + _charge |
| 8 | daily_report.py | build_daily_digest() | Δημιουργία digest dict | digest με _charge |
| 9 | xls_export.py | build_requests_xls() | Εγγραφή Excel | 5 στήλες, η 5η = "Ανάθεση σε" |

---

## 🔍 ΛΕΠΤΟΜΕΡΗ ΜΕΤΑΤΟΠΙΣΗ ΔΕΔΟΜΕΝΩΝ

### Moment 1: Φόρτωση Χρεώσεων (5A)
```
RAM: charges_records = [55 items]
     charges_by_pkm = {'106653': {...}, '105673': {...}, ...}
```

### Moment 2: Ταίριασμα (5B)
```
RAM: records[0] = {
       'case_id': '106653',
       'procedure': 'ΔΑΟ-ΦΖΠ-32',
       'directory': 'ΓΕΝ. ΔΙΕ. ΑΓΡΟΤΙΚΗΣ',
       'party': 'ΚΗΠΟΣ-258403847',
+      '_charge': {
+        'charged': True,
+        'employee': 'ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ'
+      }
     }
```

### Moment 3: Αποθήκευση (7)
```
FILE: data/incoming_requests/2026-02-16.json
{
  "records": [
    {
      "case_id": "106653",
      "procedure": "...",
      "directory": "...",
      "party": "...",
      "_charge": {
        "charged": true,
        "employee": "ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ"
      }
    }
  ]
}
```

### Moment 4: Excel (9)
```
CELL E1: "Ανάθεση σε"
CELL E2: "ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ"
CELL E3: ""  (άλλο record)
CELL E4: "ΓΑΛΟΥΠΗ ΕΥΑΓΓΕΛΙΑ"
...
```

---

## 🎯 ΚΛΕΙΔΙΚΑ ΣΗΜΕΙΑ

1. **PKM Matching**: 
   - Incoming: `case_id` (από W007_P_FLD21)
   - Charges: Εξαγόμενο από DESCRIPTION
   - Αναζήτηση: `if pkm in charges_by_pkm`

2. **Employee Field**:
   - Πηγή: `W001_P_FLD10` από τη χρέωση
   - Εξαγωγή: `get_employee_from_charge(charge)`
   - Αποθήκευση: `_charge['employee']`

3. **Persistence**:
   - JSON: `data/incoming_requests/2026-02-16.json` (με _charge)
   - Excel: 5η στήλη "Ανάθεση σε"

4. **Fallback**:
   - Αν δεν βρεθεί χρέωση: `charged: False`, `employee: None`
   - Excel: κενό πεδίο

---

## � NEW FEATURE: API Enrichment Functions (Lines 485-604)

These functions implement the two-step API enrichment for missing charges:

```python
# Line 485-510: fetch_case_detail_payload(monitor, doc_id)
def fetch_case_detail_payload(monitor, doc_id):
    """Fetch case details from /7/{doc_id} endpoint"""
    endpoint = f"/services/DataServices/fetchDataTableRecord/7/{doc_id}"
    # Returns: {success: true, data: [{W007_P_FLD7: {...}, ...}]}

# Line 512-570: get_doc_id_from_w007_p_fld7(payload)
def get_doc_id_from_w007_p_fld7(payload):
    """Extract charge DOCID from W007_P_FLD7.docIds array"""
    # KEY FIX (Line 538-549): Handle both dict and list response formats
    data = payload.get('data')
    if isinstance(data, list):  # Response is LIST, not dict!
        if not data or len(data) == 0:
            return None
        data = data[0]  # Extract first item
    # Continue with dict operations on data
    w007_p_fld7 = data.get('W007_P_FLD7')
    doc_ids = w007_p_fld7.get('docIds', [])
    return doc_ids[0] if doc_ids else None

# Line 572-604: enrich_charge_with_employee(monitor, doc_id)
def enrich_charge_with_employee(monitor, doc_id):
    """Two-step API call to find employee assignment"""
    # Step 1: Fetch from /7 endpoint
    payload = fetch_case_detail_payload(monitor, doc_id)
    charge_doc_id = get_doc_id_from_w007_p_fld7(payload)
    
    if not charge_doc_id:
        return None
    
    # Step 2: Fetch from /2 endpoint
    employee = get_employee_from_ots_detail(monitor, charge_doc_id)
    return employee

# Success Rate: 92.5% (37/40 test records enriched)
```

**Modifications to Existing Functions (Line 428 - CRITICAL FIX 🔴):**

```python
# CHANGED: Use ONLY W001_P_FLD10 (employee), NOT USER_GROUP_ID_TO (department)
def add_charge_info_from_combined(records, charges_by_pkm, monitor=None, enrich_missing=True):
    # Line 428: Department filter fix
    employee = get_employee_from_charge(charge)  # ONLY this
    # REMOVED: get_employee_from_queryid3_charge(charge) which returned departments
    
    # Line 430-445: API enrichment for missing charges
    if enrich_missing and not charge and monitor:
        employee = enrich_charge_with_employee(monitor, doc_id)
```

**Integration Points:**
- daily_report.py line 152: `add_charge_info(records, charges_by_pkm, monitor=monitor, enrich_missing=True)`
- sede_report.py line 123: `add_charge_info_from_combined(records, charges_by_pkm, monitor=monitor, enrich_missing=True)`
- weekly_report_generator.py line 522: `add_charge_info_from_combined(records, charges_by_pkm, monitor=monitor, enrich_missing=True)`

---

## 🔴 NEW FEATURE: Supplement Case Display

### src/incoming.py (Lines 135-148)

Added `related_case` field extraction for supplement cases:

```python
# Line 137: Extract related case from W007_P_FLD7 (text field)
record['related_case'] = record.get('W007_P_FLD7')  # e.g., "Αίτημα 2026/105673 ΜΟΥΡΑΤΙΔΟΥ-128272645"
```

### src/xls_export.py (Lines 137-148)

Format related case in ΤΥΠΟΣ column:

```python
# For supplements: Extract year/number with regex
if record.get('related_case'):
    match = re.search(r'(\d{4}/\d+)', record['related_case'])
    if match:
        case_code = match.group(1)  # e.g., "2026/105673"
        tipo = f"Συμπληρωματικά Αιτήματος: {case_code}"
```

**Result**: 5 supplements correctly labeled in ΤΥΠΟΣ column

---

## �💻 DEBUGGING - ΕΝΤΟΠΙΣΜΟΣ ΣΦΑΛΜΑΤΩΝ

Αν κάτι δεν δουλεύει:

```python
# Έλεγχος 1: Ανακτήθηκαν χρεώσεις;
from src.charges import fetch_charges
charges_records, charges_by_pkm = fetch_charges(monitor)
assert len(charges_by_pkm) > 0, "Δεν υπάρχουν χρεώσεις!"

# Έλεγχος 2: Έχουν _charge;
assert any('_charge' in r for r in records), "Όχι _charge fields!"

# Έλεγχος 3: Έχουν employee;
employees = [r['_charge']['employee'] for r in records if r['_charge']['charged']]
assert len(employees) > 0, "Δεν υπάρχουν χρεωμένες αιτήσεις!"

# Έλεγχος 4: Excel;
import openpyxl
wb = openpyxl.load_workbook('test_charges_report.xlsx')
ws = wb['Πραγματικές']
assert ws['E1'].value == 'Ανάθεση σε', "Στήλη E δεν είναι σωστή!"
```
