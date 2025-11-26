# PKM Website Monitor

Εφαρμογή Python για παρακολούθηση ενεργών διαδικασιών στην πλατφόρμα PKM (Περιφέρεια Κεντρικής Μακεδονίας).

## Χαρακτηριστικά

- ✅ Αυτόματο login στην πλατφόρμα PKM
- ✅ Ανάκτηση ενεργών διαδικασιών
- ✅ Αποθήκευση baseline για σύγκριση
- ✅ Ανίχνευση αλλαγών (νέες, τροποποιημένες, απενεργοποιημένες)
- ✅ Desktop notifications και ηχητικές ειδοποιήσεις
- ✅ Continuous monitoring

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
   ```

3. **Εγκατάσταση dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ρύθμιση credentials:**
   ```bash
   # Αντίγραψε το .env.example σε .env
   copy .env.example .env
   
   # Επεξεργάσου το .env και πρόσθεσε τα credentials
   notepad .env
   ```

## Ρύθμιση

### Αρχείο `.env`
```env
PKM_USERNAME=your_username
PKM_PASSWORD=your_password
```

### Αρχείο `config/config.yaml`
Περιέχει τις ρυθμίσεις URLs και API parameters (δεν χρειάζεται αλλαγή).

## Χρήση

### Αποθήκευση Baseline
Αποθηκεύει τις τρέχουσες ενεργές διαδικασίες:
```bash
python -m src.main --save-baseline
```

### Σύγκριση με Baseline
Συγκρίνει τις τρέχουσες διαδικασίες με το αποθηκευμένο baseline:
```bash
python -m src.main --compare
```

### Εμφάνιση Ενεργών Διαδικασιών
```bash
python -m src.main --list-active
```

### Continuous Monitoring
```bash
python -m src.main
```

### Συνδυασμός Παραμέτρων
```bash
python -m src.main --save-baseline --list-active
python -m src.main --compare --list-active
```

## Project Structure
```
website-monitor/
├── src/
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── monitor.py       # PKMMonitor class
│   └── utils.py         # Utilities
├── config/
│   └── config.yaml      # Configuration
├── data/
│   └── .gitkeep         # Baseline storage
├── logs/
│   └── .gitkeep         # Log files
├── .env.example         # Example credentials
├── .gitignore
├── requirements.txt
└── README.md
```

## License
MIT License