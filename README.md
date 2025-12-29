# PKM Website Monitor

Εφαρμογή Python για παρακολούθηση ενεργών διαδικασιών και εισερχόμενων αιτήσεων στην πλατφόρμα PKM (Περιφέρεια Κεντρικής Μακεδονίας).

## Χαρακτηριστικά

- ✅ Αυτόματο login στην πλατφόρμα PKM
- ✅ Ανάκτηση και παρακολούθηση ενεργών διαδικασιών
- ✅ Αποθήκευση baseline για σύγκριση αλλαγών
- ✅ Ανίχνευση αλλαγών (νέες, τροποποιημένες, ενεργοποιημένες/απενεργοποιημένες)
- ✅ Παρακολούθηση εισερχόμενων αιτήσεων με ημερήσια snapshots
- ✅ Εμπλουτισμός εγγραφών με στοιχεία διαδικασίας και διεύθυνσης
- ✅ Διαχωρισμός πραγματικών/δοκιμαστικών αιτήσεων
- ✅ Ημερήσιες αναφορές με email/PDF και τίτλους ιστορικής σύγκρισης
- ✅ Desktop notifications και ηχητικές ειδοποιήσεις
- ✅ Continuous monitoring

## Project Structure

```
website-monitor/
├── src/
│   ├── main.py              # Entry point
│   ├── monitor.py           # PKMMonitor class (continuous monitoring)
│   ├── session.py           # Session management, login, HTTP requests
│   ├── notifications.py     # Desktop notifications & sounds
│   ├── config.py            # Configuration & paths
│   ├── baseline.py          # Baseline management (ενεργές & όλες)
│   ├── procedures.py        # Procedures cache
│   ├── incoming.py          # Incoming requests management
│   ├── api.py               # API calls & record enrichment
│   ├── display.py           # Output formatting (CLI incoming compare)
│   ├── report_display.py    # Output formatting (daily digest)
│   ├── formatters.py        # Κοινές συναρτήσεις μορφοποίησης (text/HTML/PDF)
│   ├── test_users.py        # Διαχείριση δοκιμαστικών χρηστών
│   ├── backfill_snapshots.py # Ενημέρωση παλαιότερων snapshots
│   └── utils.py             # Utilities
├── config/
│   └── config.yaml          # Ρυθμίσεις URLs και API
├── data/
│   ├── incoming_requests/   # Ημερήσια snapshots αιτήσεων
│   ├── active_procedures_baseline.json
│   ├── all_procedures_baseline.json
│   ├── procedures_cache.json
│   └── test_users.json      # Λίστα δοκιμαστικών χρηστών
├── .env                     # Credentials (δεν είναι στο repo)
├── requirements.txt
└── README.md
```

## Εγκατάσταση

1. **Clone το repository:**
   ```bash
   git clone <repository-url>
   cd website-monitor
   ```

2. **Δημιουργία virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Εγκατάσταση dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ρύθμιση credentials:**
   ```bash
   copy .env.example .env   # Windows
   cp .env.example .env     # Linux/Mac
   ```
   Επεξεργάσου το `.env` και πρόσθεσε τα credentials.

## Ρύθμιση

### Αρχείο `.env`
```env
PKM_USERNAME=your_username
PKM_PASSWORD=your_password

# Email Configuration (STARTTLS παράδειγμα)
EMAIL_ADDRESS=itsxed@rcm.gov.gr
EMAIL_PASSWORD=your_encrypted_password_here
EMAIL_SMTP_SERVER=mailsmtp.rcm.gov.ar
EMAIL_SMTP_PORT=587          # 587 για STARTTLS, ή 465 για SSL
EMAIL_USE_TLS=true           # true για STARTTLS, false για SSL
EMAIL_NOTIFICATIONS_ENABLED=true
# Προαιρετικό: custom διαδρομή για admins
# ADMINS_FILE=data/admins.json
```

### Αρχείο `data/admins.json`
```json
{
  "admins": [
    {
      "name": "Admin User 1",
      "email": "admin1@example.com",
      "notify_on_error": true,
      "notify_on_recovery": true
    }
  ]
}
```

### Αρχείο `data/test_users.json`
Ρύθμιση δοκιμαστικών χρηστών για διαχωρισμό από πραγματικές αιτήσεις:
```json
{
  "internal_user_suffix": "(Εσωτ. χρήστης)",
  "test_users": ["", ""],
  "test_companies": []
}
```

## Χρήση

### Ενεργές Διαδικασίες
```bash
python src/main.py --save-baseline      # Αποθήκευση baseline ενεργών
python src/main.py --compare            # Σύγκριση με baseline
python src/main.py --list-active        # Εμφάνιση ενεργών διαδικασιών
```

### Όλες οι Διαδικασίες
```bash
python src/main.py --save-all-baseline  # Αποθήκευση baseline όλων
python src/main.py --compare-all        # Σύγκριση όλων με baseline
python src/main.py --list-all           # Εμφάνιση όλων των διαδικασιών
```

### Εισερχόμενες Αιτήσεις
```bash
python src/main.py --check-incoming-portal                # Έλεγχος νέων αιτήσεων
python src/main.py --check-incoming-portal --enrich-all   # + εμπλουτισμός όλων με ελλιπή στοιχεία
python src/main.py --compare-date 2025-12-05              # Σύγκριση snapshot ημερομηνίας
python src/main.py --send-daily-email                     # Ημερήσια αναφορά (email + PDF)
python src/main.py --export-incoming-xls                  # Εξαγωγή XLS (2 φύλλα: Δοκιμαστικές, Πραγματικές)
python src/main.py --export-incoming-xls-all             # Εξαγωγή XLS με ΟΛΕΣ τις αιτήσεις (δοκιμαστικές & πραγματικές)
```

#### Ιστορική σύγκριση ημερήσιας αναφοράς
- Ορίζεις στο `.env` το `INCOMING_FORCE_BASELINE_DATE=YYYY-MM-DD`
- Η ημερήσια αναφορά φορτώνει το snapshot αυτής της ημερομηνίας και το συγκρίνει με το αμέσως προηγούμενο διαθέσιμο snapshot
- Οι τίτλοι (terminal/email/PDF) δείχνουν ξεκάθαρα: «ΑΝΑΦΟΡΑ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ - Σύγκριση <ημερομηνία> με <προηγούμενη>»

### Ανάλυση Δοκιμαστικών/Πραγματικών Αιτήσεων
```bash
python src/main.py --analyze-test 2025-12-05              # Ανάλυση snapshot συγκεκριμένης ημερομηνίας
python src/main.py --check-incoming-portal --analyze-current  # Ανάλυση τρεχουσών αιτήσεων
```

### Ενημέρωση Παλαιότερων Snapshots
```bash
python src/backfill_snapshots.py                # Dry run - δείχνει τι θα αλλάξει
python src/backfill_snapshots.py --live         # Εφαρμογή αλλαγών
python src/backfill_snapshots.py --source 2025-12-05 --live  # Με συγκεκριμένη πηγή
```

### Συνδυασμοί
```bash
python src/main.py --save-baseline --list-active          # Αποθήκευση & εμφάνιση
python src/main.py --compare --list-active                # Σύγκριση & εμφάνιση
python src/main.py --compare-all --list-all               # Σύγκριση & εμφάνιση όλων
```

### Continuous Monitoring
```bash
python src/main.py                      # Ξεκινά continuous monitoring
```

## Command Line Options

| Option | Περιγραφή |
|--------|-----------|
| `--save-baseline` | Αποθηκεύει τις ενεργές διαδικασίες ως baseline |
| `--compare` | Συγκρίνει με το baseline ενεργών |
| `--list-active` | Εμφανίζει τις ενεργές διαδικασίες |
| `--save-all-baseline` | Αποθηκεύει όλες τις διαδικασίες ως baseline |
| `--compare-all` | Συγκρίνει όλες τις διαδικασίες με baseline |
| `--list-all` | Εμφανίζει όλες τις διαδικασίες |
| `--check-incoming-portal` | Ελέγχει εισερχόμενες αιτήσεις |
| `--enrich-all` | Εμπλουτίζει όλες τις εγγραφές με ελλιπή στοιχεία |
| `--compare-date YYYY-MM-DD` | Συγκρίνει snapshot συγκεκριμένης ημερομηνίας |
| `--analyze-test YYYY-MM-DD` | Αναλύει δοκιμαστικές/πραγματικές αιτήσεις |
| `--analyze-current` | Ανάλυση τρεχουσών αιτήσεων |
| `--send-daily-email` | Στέλνει ημερήσια αναφορά (email + PDF) |
| `--export-incoming-xls` | Εξάγει Excel (.xlsx) με δύο φύλλα: "Δοκιμαστικές" και "Πραγματικές" νέες αιτήσεις |
| `--export-incoming-xls-all` | Εξάγει Excel (.xlsx) με ΟΛΕΣ τις αιτήσεις του snapshot (δοκιμαστικές & πραγματικές) |
| `--no-monitor` | Δεν ξεκινά continuous monitoring |

## VS Code Launch Configurations

Το project περιλαμβάνει έτοιμες launch configurations στο `.vscode/launch.json` για εύκολο debugging.

## FastAPI Server

Εκκίνηση server για Teams/Power Automate και exports:

```bash
uvicorn src.main:app --reload
```

Χρήσιμα endpoints:
- `/sede/daily`: Ημερήσια σύνοψη (flat JSON). Περιλαμβάνει επιπλέον λίστες:
  - `incoming_real_new`: νέες πραγματικές αιτήσεις
  - `incoming_test_new`: νέες δοκιμαστικές αιτήσεις
  - `incoming_removed_list`: αφαιρεμένες αιτήσεις
- `/sede/export/xls`: Επιστρέφει `.xlsx` με δύο φύλλα (Δοκιμαστικές, Πραγματικές) και στήλες: Δ/νση, Αρ. Πρωτοκόλλου, Διαδικασία. Για scope=all, όνομα "Διαδικασίες - εισερχόμενες αιτήσεις.xlsx".
  - Παράμετρος `scope`: `new` (default) ή `all` για όλες τις αιτήσεις.

## License

MIT License