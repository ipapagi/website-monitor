# 📊 Excel Αρχεία & Χρεώσεις - Πλήρης Οδηγός

## 🎯 Περίληψη: Ποια Excel Αρχεία Ενημερώνονται

### 📋 Όνομα Αρχείων

| Όνομα Αρχείου | Δημιουργείται | Ενημερώνεται | Περιεχόμενο |
|--------------|--------|---------|-----------|
| `incoming_new_YYYY-MM-DD.xlsx` | **ΝΑΙ** (νέο κάθε μέρα) | ΔΕΝ ενημερώνεται (διασταύρωση) | Μόνο **νέες** αιτήσεις σήμερα (τα τελευταία 24ώρα) |
| `incoming_all_YYYY-MM-DD.xlsx` | **ΝΑΙ** (νέο κάθε μέρα) | ΔΕΝ ενημερώνεται (διασταύρωση) | **ΌΛΕ** οι αιτήσεις από το snapshot |
| `Διαδικασίες - εισερχόμενες αιτήσεις.xlsx` | **ΝΑΙ** (μία φορά) | **ΝΑΙ** (κάθε εξαγωγή) | ΌΛΕ οι αιτήσεις (αθροιστικό) |

---

## 🕐 ΧΡΟΝΟΛΟΓΙΟΣ: Πότε Δημιουργούνται/Ενημερώνονται

### 1️⃣ ΚΑΘΗΜΕΡΙΝΗ ΡΟΧΑ (αυτόματη, όχι manual)

```
ΩΡΟΛΟΓΙΟ ΜΗΧΑΝΙΣΜΟ: cron job ή scheduler
         ↓
    14:00 π.μ. (κατά προσέγγιση)
         ↓
    src/main.py --check-incoming-portal
         ↓
    ✅ Ανάκτηση εισερχόμενων από API
    ✅ Φόρτωση snapshot προηγούμενης μέρας
    ✅ Σύγκριση → νέες/αφαιρεμένες/τροποποιημένες
    ✅ ΑΝΑΚΤΗΣΗ ΧΡΕΩΣΕΩΝ (fetch_charges)
    ✅ Enrichment με _charge data
    ✅ Αποθήκευση JSON snapshot: data/incoming_requests/YYYY-MM-DD.json
         ↓
    ✅ Email αποστολή με σύνοψη
```

**Αποτέλεσμα**: JSON snapshot περιέχει `_charge` field για κάθε record.

---

### 2️⃣ MANUAL EXPORT - νέες αιτήσεις

```
MANUAL COMMAND:
    python -m src.main --export-incoming-xls
         ↓
    Ανάβασμα digest από memory ή από load_digest()
         ↓
    Ανάγνωση: incoming.real_new[], incoming.test_new[]
         ↓
    Processing με xls_export.build_requests_xls()
         ↓
    Δημιουργία αρχείου:
    📁 data/incoming_new_2026-02-16.xlsx
         ↓
    ✅ 5 στήλες (με "Ανάθεση σε" column E)
    ✅ Τα _charge δεδομένα μεταφέρονται στο Excel
```

**Φάκελος**: `data/` (ή custom path)  
**Όνομα Pattern**: `incoming_new_YYYY-MM-DD.xlsx`  
**Περιεχόμενο**: Μόνο σημερινές νέες αιτήσεις (real & test)  
**Σύνολο Rows**: ~5-20 αιτήσεις (τυπικά)

---

### 3️⃣ MANUAL EXPORT - όλες οι αιτήσεις

```
MANUAL COMMAND:
    python -m src.main --export-incoming-xls-all
         ↓
    Ανάβασμα digest από memory ή από load_digest()
         ↓
    Ανάγνωση: incoming.records[] (ΌΛΑ τα records από snapshot)
         ↓
    Ταξινόμηση με classify_records() → real vs test
         ↓
    Processing με xls_export.build_requests_xls(scope='all')
         ↓
    Δημιουργία αρχείου:
    📁 data/incoming_all_2026-02-16.xlsx
         ↓
    ✅ 5 στήλες (με "Ανάθεση σε" column E)
    ✅ Τα _charge δεδομένα μεταφέρονται στο Excel
```

**Φάκελος**: `data/` (ή custom path)  
**Όνομα Pattern**: `incoming_all_YYYY-MM-DD.xlsx`  
**Περιεχόμενο**: ΌΛΕ οι αιτήσεις από σήμερα (real & test)  
**Σύνολο Rows**: ~177 αιτήσεις (σύμφωνα με όσα είδαμε)

---

### 4️⃣ ΑΘΡΟΙΣΤΙΚΟ EXPORT - Fixed Filename

```
MANUAL COMMAND:
    python -m src.main --export-incoming-xls-all
    
    [Αν δεν υπάρχει date στο digest, χρησιμοποιεί σήμερα]
         ↓
    Special Case: Όνομα αρχείου FIXED (χωρίς ημερομηνία)
         ↓
    Δημιουργία/Ενημέρωση αρχείου:
    📁 data/Διαδικασίες - εισερχόμενες αιτήσεις.xlsx
         ↓
    ✅ 5 στήλες (με "Ανάθεση σε" column E)
    ✅ Ενημερώνεται κάθε φορά που τρέχει η εντολή
```

**Φάκελος**: `data/`  
**Όνομα**: `Διαδικασίες - εισερχόμενες αιτήσεις.xlsx` (FIXED)  
**Περιεχόμενο**: ΌΛΕ οι αιτήσεις από σήμερα (real & test)  
**Ενημέρωση**: Κάθε φορά που καλείται αυτή η εντολή

---

## 📍 ΚΩΔΙΚΑ ΘΕΣΕΙΣ

### Που Δημιουργούνται τα Αρχεία

**Αρχείο**: [src/main.py](src/main.py)  
**Γραμμές**: 216-235

```python
if args.export_incoming_xls or args.export_incoming_xls_all:
    from services.report_service import load_digest
    from xls_export import build_requests_xls
    
    digest = load_digest()
    date_str = (digest.get('incoming', {}) or {}).get('date') or datetime.now().strftime('%Y-%m-%d')
    out_dir = os.path.join(get_project_root(), 'data')
    os.makedirs(out_dir, exist_ok=True)
    
    scope = 'all' if args.export_incoming_xls_all else 'new'
    
    if scope == 'all':
        out_path = os.path.join(out_dir, "Διαδικασίες - εισερχόμενες αιτήσεις.xlsx")
    else:
        out_path = os.path.join(out_dir, f"incoming_{scope}_{date_str}.xlsx")
    
    build_requests_xls(digest, scope=scope, file_path=out_path)
```

### Που Ενημερώνονται με Χρεώσεις

**Αρχείο**: [src/xls_export.py](src/xls_export.py)  
**Γραμμές**: 58-97 (_write_sheet function)

```python
def _write_sheet(ws, rows: List[Dict], title: str):
    # ... setup code ...
    
    for rec in rows_sorted:
        col_vals[0].append(rec.get("directory", ""))
        col_vals[1].append(_format_protocol(rec))
        col_vals[2].append(rec.get("procedure", ""))
        col_vals[3].append(rec.get("party", ""))
        
        # ✅ ΧΡΕΩΣΕΩΝ ΕΝΗΜΕΡΩΣΗ
        charge_info = rec.get("_charge", {})
        employee = charge_info.get("employee", "") if charge_info.get("charged") else ""
        col_vals[4].append(employee)  # ← ΣΤΗΛΗ E: "Ανάθεση σε"
```

**Αρχείο**: [src/xls_export.py](src/xls_export.py)  
**Γραμμές**: 39 (header setup)

```python
def _write_sheet(ws, rows: List[Dict], title: str):
    headers = [
        "Δ/νση", 
        "Αρ. Πρωτοκόλλου", 
        "Διαδικασία", 
        "Συναλλασσόμενος", 
        "Ανάθεση σε"  # ← 5η στήλη (Column E)
    ]
```

---

## 🔄 ΔΕΔΟΜΕΝΑ ΡΟΧΑ → EXCEL

### Από JSON Snapshot → Excel

```
ΣΤΟΧΟΣ: Πώς περνούν τα _charge δεδομένα στο Excel
            ↓
    1. daily_report._prepare_incoming()
       └─→ load_previous_snapshot() [ΕΑΝ υπάρχει]
       └─→ merge_with_previous_snapshot()
       └─→ fetch_charges() [ΝΕΩΝ χρεώσεων]
       └─→ add_charge_info() [Προσθήκη _charge field]
       └─→ save_incoming_snapshot(today, records) ← ΑΠΟΘΗΚΕΥΣΗ
            ↓
    2. JSON snapshot αποθηκεύεται με _charge:
       📁 data/incoming_requests/2026-02-16.json
       └─→ Κάθε record έχει:
           {
               "case_id": "2026/106653",
               "procedure": "...",
               "_charge": {
                   "charged": true,
                   "employee": "ΓΑΛΟΥΠΗ ΕΥΑΓΓΕΛΙΑ",
                   "pkm": "106653"
               }
           }
            ↓
    3. Manual export command:
       python -m src.main --export-incoming-xls
            ↓
    4. build_requests_xls() ανάγνωση του digest:
       └─→ Διαβάζει incoming.real_new[] (objects με _charge)
       └─→ Διαβάζει όλα τα records από snapshot
            ↓
    5. xls_export._write_sheet() επεξεργασία:
       └─→ Για κάθε record:
           - rec.get("_charge", {})
           - employee = charge_info.get("employee", "")
           - col_vals[4].append(employee)  ← Column E
            ↓
    6. Excel αρχείο δημιουργία:
       📁 data/incoming_new_2026-02-16.xlsx
       ├─ Φύλλο 1: "Δοκιμαστικές"
       │  └─ 5 στήλες (E = employee names)
       └─ Φύλλο 2: "Πραγματικές"
           └─ 5 στήλες (E = employee names)
```

### Παράδειγμα Δεδομένων

**Σε JSON (data/incoming_requests/2026-02-16.json)**:
```json
{
  "date": "2026-02-16",
  "records": [
    {
      "case_id": "2026/106653",
      "protocol_number": "2026/...",
      "directory": "ΑΤΕΔ/ΑΙΟΠ",
      "procedure": "...",
      "party": "...",
      "_charge": {
        "charged": true,
        "employee": "ΓΑΛΟΥΠΗ ΕΥΑΓΓΕΛΙΑ",
        "pkm": "106653"
      }
    }
  ]
}
```

**Σε Excel (data/incoming_new_2026-02-16.xlsx)**:
```
Δ/νση                | Αρ. Πρωτοκόλλου | Διαδικασία | Συναλλασσόμενος | Ανάθεση σε
──────────────────────────────────────────────────────────────────────────────
ΑΤΕΔ/ΑΙΟΠ          | 2026(...)/16-02 | ...        | ...             | ΓΑΛΟΥΠΗ ΕΥΑΓΓΕΛΙΑ
ΕΡΓΟΥΧΙΑ           | ...             | ...        | ...             | (κενό αν δεν χρεώθη)
```

---

## ⏰ ΧΡΟΝΟΣΕΙΡΑ - ΠΟΤΕ ΤΙ ΣΥΜΒΑΙΝΕΙ

### Timeline κατά τη Διάρκεια daily_report.py Execution

```
T+0s:    START: daily_report.build_daily_digest()
         └─→ Signin & load monitor
         
T+3s:    _prepare_incoming()
         └─→ Fetch from API queryId=6 (177 records)
         
T+5s:    Load previous snapshot (αν υπάρχει)
         └─→ data/incoming_requests/2026-02-15.json
         
T+7s:    fetch_charges() ← ΝΕΩΝ ΧΡΕΩΣΕΩΝ
         └─→ Fetch from API queryId=19 (55 charges)
         └─→ Extract PKM from DESCRIPTION
         └─→ Create charges_by_pkm map
         
T+8s:    add_charge_info() ← ENRICHMENT
         └─→ Για κάθε record, lookup case_id in charges_by_pkm
         └─→ Προσθήκη _charge field (55 matched, 122 uncharged)
         
T+9s:    save_incoming_snapshot() ← PERSISTENCE
         └─→ Save: data/incoming_requests/2026-02-16.json
         └─→ WITH _charge field για όλα τα 177 records
         
T+10s:   Email notification (με σύνοψη νέων)
         
T+11s:   END: daily_report complete
```

### Timeline κατά τη Manual Excel Export

```
USER RUNS:
    python -m src.main --export-incoming-xls
         ↓
T+0s:    Load digest (από memory ή load_digest())
    
T+1s:    Load incoming snapshots από disk:
         └─→ data/incoming_requests/2026-02-16.json ← WITH _charge
         
T+2s:    build_requests_xls() called:
         └─→ scope='new' (αν --export-incoming-xls)
         └─→ Diag digest.incoming.real_new[] και .test_new[]
         
T+3s:    _write_sheet() processes each record:
         └─→ Διαβάζει _charge.employee
         └─→ Writes to column E
         
T+4s:    Save Excel file:
         └─→ data/incoming_new_2026-02-16.xlsx
         
T+5s:    Console: ✅ Δημιουργήθηκε XLS (new): data/incoming(...
```

---

## 📊 ΦΥΣΙΚΗ ΤΟΠΟΘΕΣΙΑ ΑΡΧΕΙΩΝ

### Δημιουργημένα Excel Αρχεία

```
project-root/
│
├── data/
│   ├── 📁 incoming_requests/
│   │   ├── 2026-02-14.json       (snapshot προηγούμενης - χωρίς _charge)
│   │   ├── 2026-02-15.json       (snapshot προηγούμενης - χωρίς _charge)
│   │   ├── 2026-02-16.json       (TODAY - WITH _charge field) ✅
│   │   └── ...
│   │
│   ├── 📊 incoming_new_2026-02-16.xlsx         (Manual export - νέες) ✅
│   ├── 📊 incoming_all_2026-02-16.xlsx         (Manual export - όλες) ✅
│   ├── 📊 Διαδικασίες - εισερχόμενες αιτήσεις.xlsx  (Fixed name) ✅
│   │
│   └── outputs/
│       └── reports/
│           └── test_charges_report.xlsx        (Test output)
```

---

## 🎯 SYNOPSIS: Ποία Αρχεία, Πότε

| Σημείο Ενημέρωσης | Αρχείο | Τύπος | Πότε | Ποιος |
|---------------|--------|-------|------|-------|
| **JSON Snapshot** | `data/incoming_requests/2026-02-16.json` | Δεδομένα | κάθε μέρα (14:00) | daily_report |
| **Excel (νέες)** | `data/incoming_new_YYYY-MM-DD.xlsx` | Εξαγωγή | manual command | user |
| **Excel (όλες)** | `data/incoming_all_YYYY-MM-DD.xlsx` | Εξαγωγή | manual command | user |
| **Excel (fixed)** | `data/Διαδικασίες - εισερχόμενες αιτήσεις.xlsx` | Εξαγωγή | manual command | user |

---

## ✅ ΕΛΕΓΧΟΣ: Πού Είναι τα _charge δεδομένα

### 1. Ελέγχος στο JSON Snapshot

```bash
# Λέγση αρχείου
cat data/incoming_requests/2026-02-16.json | grep -o '"_charge"' | wc -l
# Αποτέλεσμα: 177 (όλα τα records έχουν _charge field)

# Δείτε ένα παράδειγμα
python -c "
import json
snap = json.load(open('data/incoming_requests/2026-02-16.json'))
print(snap['records'][0].get('_charge', {}))
"
```

### 2. Ελέγχος στο Excel Αρχείο

```python
from openpyxl import load_workbook

wb = load_workbook('data/incoming_new_2026-02-16.xlsx')
ws = wb['Πραγματικές']

# Διαβάστε column E (Ανάθεση σε)
for row in range(3, 20):
    cell_value = ws[f'E{row}'].value
    print(f"Row {row}: {cell_value}")
```

---

## 🔧 DEBUGGING

### Q: Δεν βλέπω employee names στο Excel

**A: Ελέγξτε:**

1. ✅ Χρεώσεις ανακτήθηκαν:
   ```python
   from charges import fetch_charges
   records, by_pkm = fetch_charges(monitor)
   print(f"Έχουνν ανακτηθεί {len(records)} χρεώσεις")
   ```

2. ✅ PKM matching δουλεύει:
   ```python
   from charges import fetch_charges, add_charge_info
   records, by_pkm = fetch_charges(monitor)
   incoming = load_incoming_snapshot('2026-02-16')
   enriched = add_charge_info(incoming['records'], by_pkm)
   charged = [r for r in enriched if r.get('_charge', {}).get('charged')]
   print(f"Ταιριάστηκαν {len(charged)} records")
   ```

3. ✅ JSON snapshot περιέχει _charge:
   ```bash
   python -c "import json; s=json.load(open('data/incoming_requests/2026-02-16.json')); print(s['records'][0].get('_charge'))"
   ```

4. ✅ Excel build δεν έχει σφάλμα:
   ```bash
   python -m src.main --export-incoming-xls
   ```

---

## 📞 COMMAND REFERENCE

### Δημιουργία Excel - κάθε εντολή

```bash
# ΝΕΩΝ αιτήσεων (σήμερα)
python -m src.main --export-incoming-xls
# → data/incoming_new_2026-02-16.xlsx

# ΟΛΩΝ αιτήσεων (σndef snapshot)
python -m src.main --export-incoming-xls-all
# → data/incoming_all_2026-02-16.xlsx
# → data/Διαδικασίες - εισερχόμενες αιτήσεις.xlsx (FIXED)

# Daily automation (triggers both internally)
python -m src.main --check-incoming-portal
# → data/incoming_requests/2026-02-16.json (WITH _charge)
# → Email notification
```

---

## 🎓 ΣΥΝΟΨΗ

**Τι Ενημερώνεται:**
- ✅ JSON snapshot: `data/incoming_requests/YYYY-MM-DD.json` (αυτόματο, κάθε μέρα)
- ✅ Excel (νέες): `data/incoming_new_YYYY-MM-DD.xlsx` (manual export)
- ✅ Excel (όλες): `data/incoming_all_YYYY-MM-DD.xlsx` (manual export)  
- ✅ Excel (fixed): `data/Διαδικασίες - εισερχόμενες αιτήσεις.xlsx` (manual export)

**Πότε:**
- JSON: Αυτόματο κάθε μέρα (~14:00) κατά τη daily_report execution
- Excel: Manual με `--export-incoming-xls` flags

**Column E "Ανάθεση σε":**
- Συμπληρώνεται από `_charge.employee` field
- Κενό αν δεν υπάρχει χρέωση (55/177 = 31.1%)
- Σώνει από JSON snapshot που περιέχει _charge metadata

---

**📅 Δημιουργία:** 16 Φεβρουαρίου 2026  
**⏰ Ώρα ενημέρωσης:** Κάθε εξαγωγή
