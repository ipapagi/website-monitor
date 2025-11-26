# PKM Website Monitor - Πλήρης Τεκμηρίωση

## Περιεχόμενα
1. [Επισκόπηση](#επισκόπηση)
2. [Εγκατάσταση & Ρύθμιση](#εγκατάσταση--ρύθμιση)
3. [Οδηγίες Χρήσης](#οδηγίες-χρήσης)
4. [Αρχιτεκτονική Συστήματος](#αρχιτεκτονική-συστήματος)
5. [API & Δεδομένα](#api--δεδομένα)
6. [Αντιμετώπιση Προβλημάτων](#αντιμετώπιση-προβλημάτων)

---

## Επισκόπηση

Το PKM Website Monitor είναι μια εφαρμογή Python που παρακολουθεί τις ενεργές διαδικασίες στην πλατφόρμα της Περιφέρειας Κεντρικής Μακεδονίας.

### Κύριες Λειτουργίες
- **Login**: Αυτόματη σύνδεση στην πλατφόρμα.
- **Monitoring**: Συνεχής έλεγχος για αλλαγές στις διαδικασίες.
- **Baseline**: Αποθήκευση της τρέχουσας κατάστασης για μελλοντική σύγκριση.
- **Alerts**: Ειδοποιήσεις για νέες, τροποποιημένες ή διαγραμμένες διαδικασίες.

---

## Εγκατάσταση & Ρύθμιση

### Προαπαιτούμενα
- Python 3.8+
- Git

### Βήματα Εγκατάστασης

1. **Λήψη κώδικα:**
   ```bash
   git clone <repository-url>
   cd website-monitor
   ```

2. **Εγκατάσταση Βιβλιοθηκών:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ρύθμιση Credentials (.env):**
   Δημιουργήστε ένα αρχείο `.env` στον κεντρικό φάκελο:
   ```env
   PKM_USERNAME=το_username_σας
   PKM_PASSWORD=ο_κωδικός_σας
   ```

4. **Ρυθμίσεις (config.yaml):**
   Το αρχείο `config/config.yaml` περιέχει τα URLs και τις παραμέτρους του API.

---

## Οδηγίες Χρήσης

Η εφαρμογή εκτελείται μέσω γραμμής εντολών (CLI).

### 1. Δημιουργία Baseline (Πρώτη φορά)
Αποθηκεύει την τρέχουσα κατάσταση των ενεργών διαδικασιών τοπικά:
```bash
python -m src.main --save-baseline --list-active
```

### 2. Σύγκριση (Χειροκίνητα)
Συγκρίνει την τρέχουσα κατάσταση με το αποθηκευμένο baseline:
```bash
python -m src.main --compare
```

### 3. Συνεχής Παρακολούθηση
Ξεκινάει τον έλεγχο ανά 5 λεπτά (default):
```bash
python -m src.main
```

### 4. Λίστα Ενεργών
Εμφανίζει μόνο τις τρέχουσες ενεργές διαδικασίες:
```bash
python -m src.main --list-active
```

---

## Αρχιτεκτονική Συστήματος

### Δομή Modules
- **src/main.py**: Entry point. Διαχειρίζεται τα arguments και το baseline.
- **src/monitor.py**: Κλάση `PKMMonitor`. Υλοποιεί Login, Fetch, Parse, Compare.
- **src/utils.py**: Φόρτωση ρυθμίσεων (YAML + .env).

### Ροή Δεδομένων (Data Flow)
1. **Init**: Φόρτωση config & credentials.
2. **Auth**: Login -> Λήψη JWT Token.
3. **Fetch**: GET Data API (με JWT).
4. **Process**: Parsing JSON -> Φιλτράρισμα ενεργών (`W003_P_FLD3 == 'ΝΑΙ'`).
5. **Compare**: Σύγκριση με `data/active_procedures_baseline.json`.

---

## API & Δεδομένα

### Endpoints

#### 1. Login
- **URL**: `/services/LoginServices/loginWeb`
- **Method**: `POST`
- **Body**: `username`, `password`, `application=2`
- **Response**: JSON με `jwt` token.

#### 2. Search Data
- **URL**: `/services/SearchServices/getSearchDataByQueryId`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <JWT>`
- **Params**: `queryId=1`, `limit=100`
- **Response**: JSON με λίστα εγγραφών.

### Δομή Δεδομένων (JSON)

#### Διαδικασία (Procedure Object)
```json
{
  "docid": "1386",
  "κωδικός": "ΑΝΑΠ-17",
  "τίτλος": "Χορήγηση άδειας...",
  "ενεργή": "ΝΑΙ",
  "κατάσταση": "Οριστικοποιημένη",
  "αρ_διαδικασίας": "200"
}
```

#### Mapping Πεδίων
| Πεδίο API | Εσωτερικό Όνομα | Περιγραφή |
|-----------|-----------------|-----------|
| `DOCID` | `docid` | Μοναδικό ID |
| `W003_P_FLD6` | `κωδικός` | Κωδικός (π.χ. ΑΝΑΠ-17) |
| `W003_P_FLD4` | `τίτλος` | Τίτλος Διαδικασίας |
| `W003_P_FLD3` | `ενεργή` | Κατάσταση (ΝΑΙ/ΟΧΙ) |

---

## Αντιμετώπιση Προβλημάτων

| Πρόβλημα | Λύση |
|----------|------|
| **ModuleNotFoundError** | `pip install -r requirements.txt` |
| **Login Failed** | Ελέγξτε το `.env` για τυπογραφικά λάθη |
| **No baseline found** | Τρέξτε με `--save-baseline` |
| **SSL Errors** | Αγνοήστε τα warnings (self-signed certs) |

### Debugging Files
Η εφαρμογή δημιουργεί αρχεία για έλεγχο σφαλμάτων:
- `api_response.json`: Η τελευταία απάντηση του API.
- `debug_api_error.txt`: Λεπτομέρειες αν αποτύχει το request.

