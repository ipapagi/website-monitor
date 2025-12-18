# PKM Website Monitor - Πλήρης Τεκμηρίωση

## Περιεχόμενα
1. [Επισκόπηση](#επισκόπηση)
2. [Εγκατάσταση & Ρύθμιση](#εγκατάσταση--ρύθμιση)
3. [Οδηγίες Χρήσης](#οδηγίες-χρήσης)
4. [Αρχιτεκτονική Συστήματος](#αρχιτεκτονική-συστήματος)
5. [API & Δεδομένα](#api--δεδομένα)
6. [Αντιμετώπιση Προβλημάτων](#αντιμετώπιση-προβλημάτων)
7. [Ημερήσια Αναφορά & Ιστορική Σύγκριση](#ημερήσια-αναφορά--ιστορική-σύγκριση)

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

### 4. Ημερήσια Αναφορά (email + PDF)
```bash
python -m src.main --send-daily-email
```
- Στέλνει HTML email και PDF (landscape A4) με σύνοψη αλλαγών ενεργών/όλων διαδικασιών και εισερχόμενων αιτήσεων.
- Διαχωρίζει νέες αιτήσεις σε πραγματικές/δοκιμαστικές.
- Εμπλουτίζει εγγραφές με διαδικασία/διεύθυνση όπου λείπουν.

### 5. Ιστορική Σύγκριση Ημερήσιας Αναφοράς
- Ορίζει στο `.env` το `INCOMING_FORCE_BASELINE_DATE=YYYY-MM-DD`.
- Η αναφορά φορτώνει το snapshot αυτής της ημερομηνίας και το συγκρίνει με το αμέσως προηγούμενο διαθέσιμο snapshot.
- Οι τίτλοι σε terminal/email/PDF εμφανίζουν: «ΑΝΑΦΟΡΑ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ - Σύγκριση <ημερομηνία> με <προηγούμενη>».

### 4. Λίστα Ενεργών
Εμφανίζει μόνο τις τρέχουσες ενεργές διαδικασίες:
```bash
python -m src.main --list-active
```

### 6. Εξαγωγή Excel (.xls) νέων αιτήσεων
Δημιουργεί αρχείο `.xls` με δύο φύλλα: **Δοκιμαστικές** και **Πραγματικές**, με στήλες:
Δ/νση, Αρ. Πρωτοκόλλου, Διαδικασία.

```bash
python -m src.main --export-incoming-xls
```
Το αρχείο αποθηκεύεται στον φάκελο `data/` ως `incoming_new_{YYYY-MM-DD}.xls`.

### 7. Εξαγωγή Excel (.xls) ΟΛΩΝ των αιτήσεων
Εξάγει όλες τις αιτήσεις του snapshot (όχι μόνο τις νέες), ταξινομημένες σε δύο φύλλα (Δοκιμαστικές, Πραγματικές):

```bash
python -m src.main --export-incoming-xls-all
```
Το αρχείο αποθηκεύεται ως `incoming_all_{YYYY-MM-DD}.xls`.

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
#### Daily Summary
- **URL**: `/sede/daily`
- **Method**: `GET`
- **Notes**: Flat JSON κατάλληλο για Power Automate. Περιλαμβάνει πρόσθετες λίστες:
  - `incoming_real_new`: νέες πραγματικές αιτήσεις
  - `incoming_test_new`: νέες δοκιμαστικές αιτήσεις
  - `incoming_removed_list`: αφαιρεμένες αιτήσεις

#### Export XLS (Νέες Αιτήσεις)
- **URL**: `/sede/export/xls`
- **Method**: `GET`
- **Response**: `.xls` αρχείο με δύο φύλλα (Δοκιμαστικές, Πραγματικές)
- **Columns**: Δ/νση, Αρ. Πρωτοκόλλου, Διαδικασία
 - **Query**: `scope=new|all` (default `new`). Όταν `all`, περιλαμβάνει όλες τις αιτήσεις του snapshot.


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

---

## Ανάλυση Κώδικα

### src/main.py
Το σημείο εισόδου της εφαρμογής. Διαχειρίζεται τη ροή εκτέλεσης βάσει των παραμέτρων.

- **`main()`**: 
  - Αρχικοποιεί τον `argparse` για τα ορίσματα (`--save-baseline`, `--compare`, κλπ).
  - Φορτώνει το configuration καλώντας την `utils.load_config`.
  - Δημιουργεί το αντικείμενο `PKMMonitor`.
  - Εκτελεί τη λογική διακλάδωσης:
    - Αν δοθούν ορίσματα "μίας εκτέλεσης" (save/compare/list), κάνει login, φέρνει τα δεδομένα, εκτελεί την ενέργεια και τερματίζει.
    - Αν δεν δοθούν ορίσματα, ξεκινά το continuous monitoring (`monitor.start_monitoring()`).
- **`save_baseline(active_procedures)`**: 
  - Δημιουργεί τον φάκελο `data/` αν δεν υπάρχει.
  - Αποθηκεύει τη λίστα των ενεργών διαδικασιών σε JSON αρχείο, προσθέτοντας metadata (`timestamp`, `count`).
- **`compare_with_baseline(current, baseline)`**: 
  - Μετατρέπει τις λίστες σε dictionaries με κλειδί το `docid` για γρήγορη αναζήτηση.
  - Ελέγχει για:
    - **New**: `docid` που υπάρχει στο current αλλά όχι στο baseline (και είναι ενεργό).
    - **Removed**: `docid` που υπάρχει στο baseline αλλά όχι στο current.
    - **Activated/Deactivated**: Αλλαγή στο πεδίο `ενεργή`.
    - **Modified**: Αλλαγές σε άλλα πεδία (π.χ. τίτλος, κατάσταση) για ενεργές διαδικασίες.
- **`print_comparison_results(changes, baseline_data)`**:
  - Εμφανίζει τα αποτελέσματα με χρωματιστή μορφοποίηση και emojis για εύκολη ανάγνωση.

### src/monitor.py
Περιέχει την επιχειρησιακή λογική για την επικοινωνία με την πλατφόρμα.

- **`PKMMonitor` class**:
  - **`__init__`**: Αρχικοποιεί το `requests.Session`, απενεργοποιεί τα SSL warnings (λόγω self-signed certificates) και ορίζει τα URLs.
  - **`login()`**: 
    - Κάνει πρώτα GET στη σελίδα login για να πάρει το `JSESSIONID` cookie.
    - Εκτελεί POST request με τα credentials.
    - Ψάχνει το JWT token είτε στα headers είτε στο JSON response body.
    - Αποθηκεύει το token στο `self.jwt_token`.
  - **`fetch_page()`**: 
    - Ελέγχει αν υπάρχει login, αλλιώς κάνει login.
    - Προσθέτει το JWT token στον header `Authorization: Bearer ...`.
    - Προσθέτει timestamp (`_dc`) στα query params για αποφυγή caching.
    - Ανιχνεύει αν το session έληξε (αν το response URL γύρισε σε login page) και κάνει αυτόματα re-login.
    - Αποθηκεύει το raw response σε `api_response.json` για debugging.
  - **`parse_table_data(json_data)`**: 
    - Ελέγχει την εγκυρότητα του JSON (`success: true`).
    - Κάνει iterate στα records του `data`.
    - Αποκωδικοποιεί HTML entities (π.χ. `&Alpha;` -> `Α`) στην περιγραφή.
    - Χαρτογραφεί τα κρυπτικά ονόματα πεδίων του API (π.χ. `W003_P_FLD4`) σε φιλικά ονόματα (`τίτλος`).
    - Φιλτράρει ποιες διαδικασίες είναι ενεργές (`W003_P_FLD3 == 'ΝΑΙ'`).
  - **`start_monitoring()`**: 
    - Τρέχει σε ατέρμονο βρόχο (while True).
    - Καλεί την `fetch_page` και συγκρίνει τα νέα δεδομένα με τα προηγούμενα (`previous_data`).
    - Εμφανίζει ειδοποιήσεις (print/sound/toast) αν βρεθούν αλλαγές.
    - Περιμένει `check_interval` δευτερόλεπτα.

### src/utils.py
Διαχείριση ρυθμίσεων.

- **`load_config()`**: 
  - Φορτώνει μεταβλητές περιβάλλοντος από το αρχείο `.env` χρησιμοποιώντας τη βιβλιοθήκη `python-dotenv`.
  - Διαβάζει το αρχείο `config.yaml` με τη βιβλιοθήκη `PyYAML`.
  - Ενσωματώνει τα credentials (`PKM_USERNAME`, `PKM_PASSWORD`) στο configuration dictionary, ώστε να μην υπάρχουν hardcoded κωδικοί στον κώδικα.

