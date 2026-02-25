# 📂 ΧΡΕΩΣΕΙΣ - ΔΟΜΗ ΑΡΧΕΙΩΝ & ΡΟΧΑ ΔΕΔΟΜΕΝΩΝ

## 🏗️ ΑΡΧΙΤΕΚΤΟΝΙΚΗ

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DAILY WORKFLOW                              │
│              (Εκτέλεση κάθε πρωί με python src/main.py)            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                ┌─────────────────┼─────────────────────┐
                ▼                 ▼                     ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │   LOGIN      │  │ FETCH        │  │ ENRICH       │
          │              │  │ INCOMING     │  │ DETAILS      │
          │ session.py   │  │ incoming.py  │  │ api.py       │
          │ login()      │  │ fetch_rec()  │  │ enrich()     │
          └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                 │                  │                 │
                 └──────────────┬───┴────────────┬────┘
                                ▼
                    ┌────────────────────────────┐
                    │  RAM: 177 records         │
                    │  + procedure              │
                    │  + directory              │
                    └────────────────────────────┘
                                │
            ┌───────────────────┴──────────────────────┐
            │  🔴 NEW STEP: FETCH CHARGES  🔴         │
            │                                          │
            ▼                                          ▼
    ┌──────────────────┐                     ┌──────────────────┐
    │  API queryId=19  │                     │  charges.py      │
    │  (55 records)    │                     │  fetch_charges() │
    └────────┬─────────┘                     └────────┬─────────┘
             │                                        │
             └────────────────┬──────────────────────┘
                              ▼
                    ┌────────────────────────────┐
                    │  Extract PKM from         │
                    │  DESCRIPTION field        │
                    │ "Αίτημα 2026/106653..."   │
                    │ → 106653                  │
                    └────────┬───────────────────┘
                             ▼
                ┌────────────────────────────────────┐
                │  charges_by_pkm dict               │
                │  {'106653': record,                │
                │   '105673': record, ...}           │
                └────────────┬─────────────────────┘
                             │
                             │ 🔴 MATCHING LOGIC
                             ▼
    ┌─────────────────────────────────────────────────┐
    │  For each of 177 incoming records:              │
    │  1. Get case_id (the PKM)                       │
    │  2. Look it up: pkm in charges_by_pkm?          │
    │  3. If YES:                                     │
    │     rec['_charge'] = {                          │
    │       'charged': True,                          │
    │       'employee': charge['W001_P_FLD10']        │
    │     }                                           │
    │  4. If NO:                                      │
    │     rec['_charge'] = {                          │
    │       'charged': False,                         │
    │       'employee': None                          │
    │     }                                           │
    └────────────┬──────────────────────────────────┘
                 ▼
    ┌────────────────────────────────────────┐
    │  RAM: 177 records + _charge field   │
    │  Result: 55 charged, 122 uncharged  │
    └────────┬───────────────────────────────┘
             │
     ┌───────┴────────────────────────────┐
     │  Save Snapshot (JSON)              │
     │  + Classify (real/test)            │
     │  + Build Digest                    │
     ▼                                    ▼
┌─────────────────────────────┐  ┌──────────────────────────┐
│ data/incoming_requests/     │  │ digest dict              │
│ 2026-02-16.json             │  │ (RAM, passed to export)  │
│ {                           │  │ {                        │
│   "records": [              │  │   "incoming": {          │
│     {                       │  │     "records": [...]     │
│       ...                   │  │     "real_new": [...]    │
│       "_charge": {          │  │     "test_new": [...]    │
│         "charged": true,    │  │   }                      │
│         "employee": "NAME"  │  │ }                        │
│       }                     │  │                          │
│     }                       │  │                          │
│   ]                         │  │                          │
│ }                           │  │                          │
└─────────────────────────────┘  └──────────────────────────┘
             │                            │
             │                    ┌───────┴─────────────┐
             │                    │  Export Options:   │
             │                    │  - Email Report    │
             │                    │  - Excel Report    │
             │                    │  - Directory Emails│
             │                    └────────┬───────────┘
             │                             ▼
             │                  ┌──────────────────────┐
             │                  │ xls_export.py        │
             │                  │ build_requests_xls() │
             │                  └─────────┬────────────┘
             │                            ▼
             └─────────────┬──────────────────────────┐
                           ▼                          ▼
                  ┌──────────────────┐       ┌────────────────┐
                  │  Excel File      │       │ EMAIL REPORTS  │
                  │  5 columns       │       │ (αν enabled)   │
                  │  (E = ...)       │       │ + _charge info │
                  └──────────────────┘       └────────────────┘
```

---

## 📋 ΑΡΧΕΙΑ ΚΑΤΑ ΑΛΦΑΒΗΤΑ

### 🔵 ΕΙ΅ΕΛΤ

```
src/
├── session.py
│   └── login() ........................ Σύνδεση
│
├── incoming.py
│   ├── fetch_incoming_records() ...... API queryId=6 (177 records)
│   ├── simplify_incoming_records() ... Εξαγωγή case_id, submitted_at, etc
│   ├── save_incoming_snapshot() ....... Αποθήκευση στο 2026-02-16.json
│   └── compare_incoming_records() .... Διαφορές με προηγ. snapshot
│
├── charges.py 🔴 ΝΕΟ ΑΡΧΕΙΟ
│   ├── fetch_charges() ............... API queryId=19 (55 records)
│   ├── _extract_pkm_from_description() Εξαγωγή PKM από DESCRIPTION
│   ├── add_charge_info() ............. 🔴 ΕΜΠΛΟΥΤΙΣΜΕΝΑ RECORDS
│   ├── get_employee_from_charge() .... Εξαγωγή ονόματος (W001_P_FLD10)
│   ├── filter_charged() .............. Φιλτράρισμα χρεωμένων
│   ├── filter_uncharged() ............ Φιλτράρισμα μη χρεωμένων
│   ├── get_charge_statistics() ....... Στατιστικά
│   └── print_charge_statistics() ..... Εμφάνιση στατιστικών
│
├── api.py
│   └── enrich_record_details() ....... Προσθήκη procedure/directory
│
├── test_users.py
│   ├── classify_records() ............ Κατάταξη real/test (με _charge)
│   └── get_record_stats() ............ Στατιστικά
│
├── daily_report.py 🔴 ΤΡΟΠΟΠΟΙΗΜΕΝΟ
│   ├── _prepare_incoming() ........... 🔴 Προστέθηκε fetch_charges()
│   ├── build_daily_digest() .......... Δημιουργία digest dict (με _charge)
│   └── send_daily_email() ............ Αποστολή email report
│
└── xls_export.py 🔴 ΤΡΟΠΟΠΟΙΗΜΕΝΟ
    ├── _write_sheet() ................ 🔴 Προσθήκη στήλης "Ανάθεση σε"
    └── build_requests_xls() .......... Δημιουργία Excel (με 5 στήλες)

data/
├── config.yaml
│   ├── incoming_api_params
│   │   ├── queryId: 6
│   │   └── ... other params
│   └── (queryId=19 hardcoded στο charges.py)

├── incoming_requests/
│   └── 2026-02-16.json 🔴 ΠΕΡΙΕΧΕΙ _charge
│       {
│         "records": [
│           { "case_id": "106653", "_charge": {...} },
│           ...
│         ]
│       }

└── outputs/
    └── reports/
        └── test_charges_report.xlsx 🔴 5 στήλες, E=Ανάθεση σε
```

---

## 🔄 ΔΕΔΟΜΕΝΑ ΚΑΤΑ ΣΤΑΔΙΟ

### STAGE 1: Incoming (177 records)
```
Before charges:
  {
    case_id: "106653",
    protocol_number: "",
    submitted_at: "2026-02-10 10:15:30",
    party: "ΚΗΠΟΣ-258403847",
    procedure: "ΔΑΟ-ΦΖΠ-32",
    directory: "ΓΕΝ. ΔΙΕ. ΑΓΡΟΤΙΚΗΣ"
  }
```

### STAGE 2: After add_charge_info()
```
After charges:
  {
    case_id: "106653",
    protocol_number: "",
    submitted_at: "2026-02-10 10:15:30",
    party: "ΚΗΠΟΣ-258403847",
    procedure: "ΔΑΟ-ΦΖΠ-32",
    directory: "ΓΕΝ. ΔΙΕ. ΑΓΡΟΤΙΚΗΣ",
    _charge: {           🔴 ΝΕΟ FIELD
      charged: true,
      employee: "ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ",
      doc_id: "44066",
      case_id: null,
      description: "&Alpha;&#943;&tau;&eta;&mu;&alpha;..."
    }
  }
```

### STAGE 3: In JSON Snapshot
```
data/incoming_requests/2026-02-16.json
{
  "date": "2026-02-16",
  "count": 177,
  "records": [
    {
      "case_id": "106653",
      "procedure": "ΔΑΟ-ΦΖΠ-32",
      "directory": "ΓΕΝ. ΔΙΕ. ΑΓΡΟΤΙΚΗΣ",
      "party": "ΚΗΠΟΣ-258403847",
      "_charge": {        🔴 ΑΠΟΘΗΚΕΥΜΕΝΟ
        "charged": true,
        "employee": "ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ"
      }
    },
    ...
  ]
}
```

### STAGE 4: In Excel
```
Excel file with 5 columns:
╔━━━━━━━━━━━━━━━╦━━━━━━━━━━━━━╦━━━━━━━━━━━━╦━━━━━━━━━━━━━╦━━━━━━━━━━━━━╗
║ Δ/νση         ║ Αρ. Πρωτ.   ║ Διαδικασία ║ Συναλλ.    ║ Ανάθεση σε   ║
╠═══════════════╬═════════════╬════════════╬════════════╬══════════════╣
║ ΓΕΝ. ΔΙΕ.    ║ 106653/...  ║ ΔΑΟ-ΦΖΠ-32║ ΚΗΠΟΣ-... ║ ΑΝΤΩΝΙΑΔΗΣ  ║
║ (column A)    ║ (column B)   ║ (column C) ║ (column D) ║ (column E) 🔴║
├───────────────┼─────────────┼────────────┼────────────┼──────────────┤
║ ΓΕΝ. ΔΙΕ.    ║ 105673/...  ║ ΔΑΟ-ΦΠΕ-100║ ΠΑΝΤΩΝΗΣ-..║ ΓΑΛΟΥΠΗ     ║
├───────────────┼─────────────┼────────────┼────────────┼──────────────┤
║ ΓΕΝ. ΔΙΕ.    ║ 106789/...  ║ ΑΝΑΠ-23    ║ ΣΟΚΟΣ-...  ║             ║
│               │             │            │            │ ← κενό       │
│               │             │            │            │  (not charged)
└───────────────┴─────────────┴────────────┴────────────┴──────────────┘
```

---

## 🎯 ΚΡΙΤΙΚΑ ΣΗΜΕΙΑ ΑΛΛΑΓΗΣ

### ✅ Αρχείο 1: src/charges.py
- **Γραμμές**: 235 (ΝΕΟ)
- **Κλειδικές συναρτήσεις**: 
  - `fetch_charges()`: API call
  - `_extract_pkm_from_description()`: Regex extraction
  - `add_charge_info()`: 🔴 ΕΜΠΛΟΥΤΙΣΜΟΣ

### ✅ Αρχείο 2: src/daily_report.py
- **Γραμμές**: 110-123 (ΝΕΟ ΚΩΔΙΚΑΣ)
- **Τι κάνει**: Καλεί `fetch_charges()` και `add_charge_info()`
- **Αποτέλεσμα**: `records` list έχει `_charge` field

### ✅ Αρχείο 3: src/xls_export.py
- **Αλλαγή 1** (Γραμμή 39): Προσθήκη "Ανάθεση σε" στο headers
- **Αλλαγή 2** (Γραμμές 58-65): Εξαγωγή employee
- **Αλλαγή 3** (Γραμμές 69-105): 5 στήλες instead of 4

### ✅ Αρχείο 4: src/incoming.py
- **Χωρίς αλλαγές**: Χρησιμοποιείται ήδη υπάρχων κώδικας
- **Automatic**: Το `_charge` field αποθηκεύεται αυτόματα στο JSON

---

## 📊 ΣΤΑΤΙΣΤΙΚΑ ΑΛΛΑΓΩΝ

| Κατηγορία | Γραμμές | Αρχεία |
|-----------|--------|--------|
| Νέα κώδικα | 235 | 1 (charges.py) |
| Τροποποιημένα | 14 | 2 (daily_report.py, xls_export.py) |
| Χωρίς αλλαγές | - | 8 (session, incoming, api, test_users, κτλ) |
| **Σύνολο** | **249** | **11** |

---

## 🚀 ΕΝΕΡΓΟΠΟΙΗΣΗ

### Αυτόματα (κάθε φορά που τρέχει το daily workflow):
```bash
python src/main.py --build-daily-digest ✅ έχει χρεώσεις
python src/main.py --export-xls ✅ 5 στήλες
python src/daily_report.py ✅ με χρεώσεις στο digest
```

### Manual:
```bash
python test_charges.py ✅ δοκιμή module
python test_excel_charges.py ✅ δοκιμή Excel
```

---

## 🔐 ΣΗΜΕΙΑ ΑΣΦΑΛΕΙΑΣ

1. **Try-Except**: Αν αποτύχει fetch_charges → συνεχίζει χωρίς
2. **Fallback**: Αν δεν ταιριάξει PKM → `charged: False`
3. **HTML Decoding**: Αποφυγή encoding issues
4. **Type Casting**: `str(pkm).strip()` για ασφαλείς συγκρίσεις

---

## 📞 DEBUGGING CHECKLIST

- [ ] 1. Ανακτώνται χρεώσεις; `len(charges_by_pkm) > 0`
- [ ] 2. Έχουν _charge τα records? `'_charge' in records[0]`
- [ ] 3. Έχουν employee? `records[0]['_charge']['employee']`
- [ ] 4. Σώζεται στο JSON? Check 2026-02-16.json
- [ ] 5. Εμφανίζεται στο Excel? Ανοίξτε file και δείτε column E
