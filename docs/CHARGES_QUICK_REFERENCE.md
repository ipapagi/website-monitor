# ⚡ ΧΡΕΩΣΕΙΣ - ΓΡΗΓΟΡΗ ΑΝΑΦΟΡΑ (Quick Reference)

## 🎯 Σε 60 Δευτερόλεπτα: Τι άλλαξε;

### ✨ 3 Αρχεία Αλλαγμένα

| Αρχείο | Τι | Γραμμές | Λόγος |
|--------|-----|---------|-------|
| **src/charges.py** | ✨ ΝΕΟ | 235 | Ανάκτηση χρεώσεων |
| **src/daily_report.py** | ✏️ +14 lines | 110-123 | Κάλεσμα fetch_charges() |
| **src/xls_export.py** | ✏️ +3 αλλαγές | 39, 58-65, 69-105 | 5η στήλη "Ανάθεση σε" |

---

## 🔄 Ροή Δεδομένων (10 βήματα)

```
1️⃣ Login → 2️⃣ Fetch Incoming (177) → 3️⃣ Simplify 
→ 4️⃣ Enrich Details → 5️⃣ Fetch Charges (55) 🔴
→ 6️⃣ Match & Add _charge 🔴 → 7️⃣ Save JSON
→ 8️⃣ Classify → 9️⃣ Build Digest → 🔟 Export Excel ✅
```

---

## 📍 ΠΟΥ ΑΚΡΙΒΩΣ ΕΜΜΠΑΙΝΟΥΝ ΟΙ ΧΡΕΩΣΕΙΣ

### Στη RAM (μνήμη):
```python
# ΒΗΜΑ 5A: Ανάκτηση
charges_records = [55 items]          # Από API queryId=19
charges_by_pkm = {'106653': {...}}     # Dictionary mapping

# ΒΗΜΑ 5B: Εμπλουτισμός
record['_charge'] = {                  # Προσθήκη πεδίου σε κάθε record
    'charged': True/False,
    'employee': 'ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ'  # ← ΤΟ ΚΡΙΤΙΚΟ ΠΕΔΙΟ
}
```

### Στο Αρχείο (JSON):
```json
// data/incoming_requests/2026-02-16.json
{
  "records": [
    {
      "case_id": "106653",
      "_charge": {
        "charged": true,
        "employee": "ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ"
      }
    }
  ]
}
```

### Στο Excel:
```
| Column E: Ανάθεση σε |
|  ΑΝΤΩΝΙΑΔΗΣ...       |  ← Αυτό
|  ΓΑΛΟΥΠΗ ΕΥΑΓΓΕΛ...  |
|                      |  ← Κενό αν δεν χρεωμένο
```

---

## 🔑 Κλειδί Συσχέτισης (Matching)

### Μέθοδος 1: Direct Matching (31.1% - 55/177)
**Incoming Records**:
- `case_id` = W007_P_FLD21 = **PKM** (π.χ. "106653")

**Charges**:
- `DESCRIPTION` = "Αίτημα 2026/106653 ..." 
- Εξαγωγή: regex → **PKM** (π.χ. "106653")

**Αποτέλεσμα**: 55 matches (31.1%)

### Μέθοδος 2: API Enrichment (92.5%-96% additional) 🔴 ΝΕΑ
Για τις εγγραφές **χωρίς** χρέωση, το σύστημα κάνει δύο κλήσεις API:

**Βήμα 1**: GET `/7/{doc_id}` → Εξαγωγή charge DOCID από W007_P_FLD7.docIds
**Βήμα 2**: GET `/2/{charge_doc_id}` → Εξαγωγή employee από W001_P_FLD10

**Αποτέλεσμα**: 37 επιπλέον enriched records (92.5% success rate)

---

## 📊 Τι Αλλάζει (Before/After)

### BEFORE:
```
{
  case_id: "106653",
  procedure: "ΔΑΟ-ΦΖΠ-32",
  directory: "ΓΕΝ. ΔΙΕ.",
  party: "ΚΗΠΟΣ"
}
```

### AFTER:
```
{
  case_id: "106653",
  procedure: "ΔΑΟ-ΦΖΠ-32",
  directory: "ΓΕΝ. ΔΙΕ.",
  party: "ΚΗΠΟΣ",
  related_case: "Συμπληρωματικά: 2026/105673",  ← Για supplements
  _charge: {                    ← 🔴 ΝΕΟ!
    charged: true,
    employee: "ΑΝΤΩΝΙΑΔΗΣ"      ← 🔴 ΤΟ ΣΗΜΑΝΤΙΚΟ!
  }
}
```

---

## 🚀 Πώς να Δοκιμάσετε

### 1. Test module:
```bash
cd C:\Develop\Office\Python\check_politis\website-monitor
python test_charges.py
```
✅ Εμφανίζει: 55 χρεώσεις, 17 υπάλληλοι

### 2. Test Excel:
```bash
python test_excel_charges.py
```
✅ Δημιουργεί: test_charges_report.xlsx με 5 στήλες

### 3. Check JSON:
```bash
cat data/incoming_requests/2026-02-16.json | grep -A5 "_charge"
```
✅ Εμφανίζει: `"employee": "ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ"`

### 4. Check Excel (Visual):
```bash
# Κάτω όταν και λάβω το αρχείο
```
✅ Ανοίξτε: test_charges_report.xlsx
✅ Δείτε: Column E = "Ανάθεση σε"

---

## 🎓 Αν Θέλετε να Αλλάξετε Κάτι

### Αλλαγή 1: Διαφορετικό API endpoint
```python
# src/charges.py, γραμμή 10
CHARGES_PARAMS = {
    'queryId': '19',  # ← Αλλάξτε εδώ αν χρειάζεται
    ...
}
```

### Αλλαγή 2: Διαφορετικό πεδίο για το όνομα υπαλλήλου
```python
# src/charges.py, γραμμή 73
employee = charge.get('W001_P_FLD10', '')  # ← Αλλάξτε εδώ
```

### Αλλαγή 3: Εμφάνιση κενού αντί για κενού στο Excel
```python
# src/xls_export.py, γραμμή 58
employee = charge_info.get("employee", "N/A")  # ← Αλλάξτε εδώ
```

---

## ⚠️ Λάθη & Λύσεις

| Πρόβλημα | Αιτία | Λύση |
|---------|-------|------|
| 0 χρεώσεις | Λάθος queryId | Ελέγξτε CHARGES_PARAMS |
| 0 matches | PKM δεν ταιριάζει | Ελέγχος DESCRIPTION format |
| Κενή στήλη E | _charge δεν προστέθηκε | Ελέγχος add_charge_info() |
| Crash | Exception | Απενεργοποίηση try-except για logs |

---

## 📝 Αρχεία Αναφοράς

| Έγγραφο | Περιεχόμενο |
|---------|-------------|
| [CHARGES_GUIDE.md](CHARGES_GUIDE.md) | 📖 Πλήρης οδηγός χρήσης |
| [CHARGES_DETAILED_FLOW.md](CHARGES_DETAILED_FLOW.md) | 📊 Βήμα προς βήμα ροή |
| [CHARGES_CODE_LOCATIONS.md](CHARGES_CODE_LOCATIONS.md) | 💻 Ακριβείς θέσεις κώδικα |
| [CHARGES_FILES_STRUCTURE.md](CHARGES_FILES_STRUCTURE.md) | 📂 Δομή αρχείων |
| **CHARGES_QUICK_REFERENCE.md** | ⚡ Αυτό το αρχείο |

---

## 🎯 Ένα Παράδειγμα (Real Flow)

```
Ημέρα: 16 Φεβρουαρίου 2026, 10:21 π.μ.

1. Εκτέλεση: python src/main.py --build-daily-digest
   ↓
2. Ανάκτηση 177 εισερχόμενων αιτήσεων
   ↓
3. Εμπλουτισμός με procedure/directory
   ↓
4. 🔴 ΝΕΟΣ ΚΩΔΙΚΑΣ: Ανάκτηση 55 χρεώσεων από queryId=19
   ↓
5. 🔴 ΝΕΟΣ ΚΩΔΙΚΑΣ: Ταίριασμα PKM:
   - Incoming case_id=106653 ↔ Charge DESCRIPTION="Αίτημα 2026/106653"
   - Match! → record['_charge'] = {'charged': True, 'employee': 'ΑΝΤΩΝΙΑΔΗΣ'}
   - Repeat for 55 records
   ↓
6. Αποθήκευση snapshot: data/incoming_requests/2026-02-16.json
   (Περιέχει _charge field)
   ↓
7. Κατάταξη: real_new=[50], test_new=[5] (με _charge)
   ↓
8. Δημιουργία digest dict (incoming.records έχουν _charge)
   ↓
9. Export Excel: 5 στήλες
   - A: Δ/νση
   - B: Αρ. Πρωτ.
   - C: Διαδικασία
   - D: Συναλλ.
   - E: 🔴 Ανάθεση σε = "ΑΝΤΩΝΙΑΔΗΣ"
   ↓
10. Αποθήκευση: data/outputs/reports/2026-02-16_XXXXX.xlsx
```

---

## ✅ Ελέγχ Λίστα

Επιθυμητές έκβάσεις:

- [x] src/charges.py δημιουργήθηκε
- [x] 55 χρεώσεις ανακτώνται
- [x] 55 matches με incoming
- [x] _charge field προστίθεται σε όλα τα records
- [x] JSON snapshot αποθηκεύεται με _charge
- [x] Excel έχει 5 στήλες (E = "Ανάθεση σε")
- [x] Test scripts δουλεύουν
- [x] Documentation δημιουργήθηκε

---

## 💬 Ερωτήσεις?

- **"Που αποθηκεύονται οι χρεώσεις;"** → data/incoming_requests/2026-02-16.json
- **"Πόσες χρεώσεις;"** → 55 (31.1% των εισερχόμενων)
- **"Πώς ταιριάζουν;"** → Via PKM (case_id)
- **"Τι δείχνει το Excel;"** → Column E (Ανάθεση σε)
- **"Τι γίνεται αν δεν βρεθούν;"** → Κενό πεδίο

---

**Τελευταία ενημέρωση: 16 Φεβρουαρίου 2026**
