# PKM Website Monitor

Εφαρμογή Python για παρακολούθηση ενεργών διαδικασιών στην πλατφόρμα PKM (Περιφέρεια Κεντρικής Μακεδονίας).

## Χαρακτηριστικά

- ✅ Αυτόματο login στην πλατφόρμα PKM
- ✅ Ανάκτηση και παρακολούθηση ενεργών διαδικασιών
- ✅ Αποθήκευση baseline για σύγκριση αλλαγών
- ✅ Ανίχνευση αλλαγών (νέες, τροποποιημένες, ενεργοποιημένες/απενεργοποιημένες)
- ✅ Παρακολούθηση εισερχόμενων αιτήσεων με ημερήσια snapshots
- ✅ Εμπλουτισμός εγγραφών με στοιχεία διαδικασίας και διεύθυνσης
- ✅ Desktop notifications και ηχητικές ειδοποιήσεις
- ✅ Continuous monitoring

## Project Structure

```
website-monitor/
├── src/
│   ├── main.py          # Entry point
│   ├── monitor.py       # PKMMonitor class (continuous monitoring)
│   ├── session.py       # Session management, login, HTTP requests
│   ├── notifications.py # Desktop notifications & sounds
│   ├── config.py        # Configuration & paths
│   ├── baseline.py      # Baseline management (ενεργές & όλες)
│   ├── procedures.py    # Procedures cache
│   ├── incoming.py      # Incoming requests management
│   ├── api.py           # API calls & record enrichment
│   ├── display.py       # Output formatting
│   └── utils.py         # Utilities
├── config/
│   └── config.yaml      # Ρυθμίσεις URLs και API
├── data/
│   ├── incoming_requests/           # Ημερήσια snapshots αιτήσεων
│   ├── active_procedures_baseline.json
│   ├── all_procedures_baseline.json
│   └── procedures_cache.json
├── .env                 # Credentials (δεν είναι στο repo)
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
| `--no-monitor` | Δεν ξεκινά continuous monitoring |

## VS Code Launch Configurations

Το project περιλαμβάνει έτοιμες launch configurations στο `.vscode/launch.json` για εύκολο debugging.

## License

MIT License