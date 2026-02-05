# Διαχείριση Διευθύνσεων, Περιφερειακών Ενοτήτων & Email Routing

## Επισκόπηση

Το σύστημα διαθέτει πλέον **κεντρικοποιημένη διαμόρφωση** για:
- ✅ Διευθύνσεις της Περιφέρειας
- ✅ Περιφερειακές Ενότητες (Π.Ε.)
- ✅ Email αυτών με δυνατότητα συμπλήρωσης

---

## Αρχείο Διαμόρφωσης

### Θέση
```
data/directories_config.json
```

### Δομή

```json
{
  "directories": [
    {
      "id": "dir_001",
      "name": "ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ ΚΑΙ ΚΟΙΝΩΝΙΚΗΣ ΜΕΡΙΜΝΑΣ",
      "short_name": "ΔΗΜΟΣΙΑ ΥΓΕΙΑ",
      "regional_units": [
        {
          "id": "ru_001_1",
          "name": "Π.Ε. ΘΕΣΣΑΛΟΝΙΚΗΣ",
          "email": "health.thessaloniki@rcm.gov.gr",
          "phone": "+30 2310 123456",
          "responsible": ""  // Προαιρετικό: όνομα υπευθύνου
        }
      ]
    }
  ],
  "regional_units_map": {
    "ΘΕΣΣΑΛΟΝΙΚΗΣ": {
      "id": "ru_regional_1",
      "name": "Π.Ε. ΘΕΣΣΑΛΟΝΙΚΗΣ",
      "email": "perifereia.thessaloniki@rcm.gov.gr",
      "phone": "+30 2310 999999"
    }
  }
}
```

### Πεδία

| Πεδίο | Περιγραφή | Υποχρεωτικό |
|-------|-----------|-----------|
| `id` | Μοναδικό αναγνωριστικό | ✅ |
| `name` | Πλήρες όνομα Διεύθυνσης/Π.Ε. | ✅ |
| `short_name` | Σύντομη μορφή | ❌ |
| `email` | Email διεύθυνσης | ⚠️ (χρειάζεται συμπλήρωση) |
| `phone` | Τηλέφωνο | ❌ |
| `responsible` | Όνομα υπευθύνου | ❌ |

---

## Utility Script: manage_directories.py

### Εντολές

#### 1. Εμφάνιση όλων
```bash
python manage_directories.py
# ή
python manage_directories.py --list-directories
```

#### 2. Αναζήτηση Email
```bash
# Όλες οι Διευθύνσεις
python manage_directories.py --find-email

# Συγκεκριμένη Διεύθυνση
python manage_directories.py --find-email "ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ"

# Διεύθυνση + Π.Ε.
python manage_directories.py --find-email "ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ" "Π.Ε. ΘΕΣΣΑΛΟΝΙΚΗΣ"
```

#### 3. Εξαγωγή σε CSV
```bash
python manage_directories.py --export-csv
# Δημιουργεί: data/directories_export.csv
```

#### 4. Εξαγωγή σε JSON
```bash
python manage_directories.py --export-json
# Δημιουργεί: data/directories_export.json
```

#### 5. Εμφάνιση Π.Ε.
```bash
python manage_directories.py --list-regional-units
```

#### 6. Επαλήθευση Διαμόρφωσης
```bash
python manage_directories.py --validate
```
Ελέγχει για:
- Missing emails
- Invalid email formats
- Missing required fields
- Duplicate entries

---

## Python API: DirectoriesManager

### Χρήση

```python
from src.directories_manager import DirectoriesManager

manager = DirectoriesManager()

# Αναζήτηση Διεύθυνσης
dir_info = manager.get_directory_by_name("ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ")

# Αναζήτηση Π.Ε.
rus = manager.get_regional_units_for_directory("ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ")

# Email για συγκεκριμένη Διεύθυνση + Π.Ε.
email = manager.get_email_for_directory_and_regional_unit(
    "ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ",
    "Π.Ε. ΘΕΣΣΑΛΟΝΙΚΗΣ"
)

# Εύρεση καλύτερου email για αίτηση
record = {
    'directory': 'ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ ΚΑΙ ΚΟΙΝΩΝΙΚΗΣ ΜΕΡΙΜΝΑΣ Μ.Ε. ΘΕΣΣΑΛΟΝΙΚΗΣ',
    'case_id': '911678'
}
email_tuple = manager.find_best_email_for_record(record)  # Returns (email, source)
```

### Κύριες Μέθοδοι

| Μέθοδος | Περιγραφή |
|--------|-----------|
| `get_directory_by_name(name)` | Αναζήτηση Διεύθυνσης με όνομα |
| `get_directory_by_short_name(short_name)` | Αναζήτηση με σύντομο όνομα |
| `get_email_for_directory_and_regional_unit(dir, ru)` | Email για Διεύθυνση+Π.Ε. |
| `get_regional_unit_email(ru_name)` | Email Π.Ε. |
| `get_regional_units_for_directory(dir_name)` | Όλες οι Π.Ε. μιας Διεύθυνσης |
| `find_best_email_for_record(record)` | Καλύτερο email για αίτηση |
| `export_for_excel()` | Export σε format Excel |

---

## Ενσωμάτωση με directory_emails.py

Το `directory_emails.py` χρησιμοποιεί αυτόματα τη διαμόρφωση:

### Σειρά Αναζήτησης Email

1. **Αναζήτηση σε directories_config.json** (Διεύθυνση + Π.Ε.)
   - Εξάγει τη Π.Ε. από το όνομα αίτησης
   - Ψάχνει το αντίστοιχο email

2. **Fallback σε περιβάλλον μεταβλητές** (`.env`)
   - Ψάχνει `DIRECTORY_EMAIL_{directory_name}`

3. **Γενική αναζήτηση**
   - Χρησιμοποιεί το πρώτο email της Διεύθυνσης

### Παράδειγμα Output

```
📧 Δημιουργία email για Διεύθυνση: ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ
   Αιτήσεις: 2
   ℹ️  Email βρέθηκε από directory_ru
   ✅ Email εστάλη στο health.thessaloniki@rcm.gov.gr
```

---

## Συμπλήρωση Emails

### Βήμα 1: Ανοίξτε το αρχείο
```
data/directories_config.json
```

### Βήμα 2: Συμπληρώστε τα κενά emails
Αναζητήστε τα πεδία `"email": ""` και συμπληρώστε τα.

Παράδειγμα:
```json
{
  "name": "Π.Ε. ΘΕΣΣΑΛΟΝΙΚΗΣ",
  "email": "",  // ← Συμπληρώστε εδώ
  "phone": "+30 2310 123456"
}
```

### Βήμα 3: Επαλήθευση
```bash
python manage_directories.py --validate
```

Αυτό θα εμφανίσει προειδοποιήσεις για κενά emails.

---

## Αυτόματη Συμπλήρωση (Μελλοντικά)

Πιθανοί τρόποι αυτόματης εύρεσης:

### Επιλογή 1: Αναζήτηση στο Active Directory (AD)
```python
# Ψάχνουν χρήστες σύμφωνα με τη Διεύθυνση
email = find_in_active_directory(directory_name)
```

### Επιλογή 2: Web Scraping από Περιφερειακό Δικτυακό Τόπο
```python
# Crawling της ιστοσελίδας της Περιφέρειας για emails
emails = scrape_region_website()
```

### Επιλογή 3: REST API Αναζήτησης
```python
# Query σε κεντρικό σύστημα
email = query_central_directory_api(directory_id)
```

**Προς το παρόν:** Χειροκίνητη συμπλήρωση στο `directories_config.json`

---

## Δομή Αρχείων

```
website-monitor/
├── data/
│   ├── directories_config.json     ← ΚΕΝΤΡΙΚΗ ΔΙΑΜΟΡΙΩΣΗ
│   ├── directories_export.csv      ← (δημιουργείται)
│   └── directories_export.json     ← (δημιουργείται)
├── src/
│   ├── directories_manager.py      ← NEW
│   ├── directory_emails.py         ← ΤΡΟΠΟΠΟΙΗΜΕΝΟ
│   └── ...
└── manage_directories.py           ← NEW (utility script)
```

---

## Παράδειγμα Workflow

### 1. Δείτε τα υπάρχοντα δεδομένα
```bash
python manage_directories.py
```

### 2. Εξαγάγετε σε Excel
```bash
python manage_directories.py --export-csv
# Ανοίξτε: data/directories_export.csv με Excel/Calc
```

### 3. Συμπληρώστε τα emails
Ενημερώστε το αρχείο με τα σωστά emails

### 4. Αντιγράψτε ενημερωμένα δεδομένα
Αντιγράψτε τα δεδομένα από Excel πίσω στο `directories_config.json`

### 5. Επαληθεύστε
```bash
python manage_directories.py --validate
```

### 6. Δοκιμάστε την αποστολή
```bash
python src/main.py --send-directory-emails
```

---

## Troubleshooting

### ❌ "Δεν βρέθηκε email"
**Λύση:** Συμπληρώστε το email στο `directories_config.json` ή ορίστε `DIRECTORY_EMAIL_*` περιβάλλον μεταβλητή

### ❌ Invalid email format
**Λύση:** Ελέγξτε ότι το email είναι σε σωστό format (xxx@yyy.zzz)

### ❌ Π.Ε. δεν αναγνωρίζεται
**Λύση:** Ελέγξτε ότι το όνομα Π.Ε. στο αρχείο ταιριάζει ακριβώς με το όνομα στο `directory` field

---

## SQL Query για Εξαγωγή (Μελλοντικά)

Αν αναπτυχθεί backend database:
```sql
SELECT 
  d.name as directory,
  ru.name as regional_unit,
  ru.email
FROM directories d
JOIN regional_units ru ON d.id = ru.directory_id
ORDER BY d.name, ru.name;
```

---

## Σημειώσεις

✅ Το αρχείο είναι JSON, εύκολα επεξεργάσιμο με Python/JavaScript/Any text editor  
✅ Υποστηρίζει ελληνικά χαρακτήρες (UTF-8)  
✅ Partial matching για ευέλικτες αναζητήσεις  
✅ Fallback σε περιβάλλον μεταβλητές για backward compatibility  
⚠️ Ενημερώστε το αρχείο μόλις αλλάξουν emails ή Διευθύνσεις
