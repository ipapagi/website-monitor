# FastAPI Endpoints - PKM Monitor

## Επισκόπηση

Το πρόγραμμα τώρα διαθέτει FastAPI endpoints για πρόσβαση στα δεδομένα της ημερήσιας αναφοράς ΣΗΔΕ.

## Εκκίνηση

### FastAPI Server (μόνο API)
```bash
# Τρόπος 1: Με uvicorn (Προτεινόμενο)
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Τρόπος 2: Με reload για development
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Τρόπος 3: Custom port
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

Αυτό θα ξεκινήσει **μόνο** το FastAPI server:
- 📡 Endpoint: `http://localhost:8000/sede/daily`
- 📖 API Documentation (Swagger UI): `http://localhost:8000/docs`
- 🎯 API Documentation (ReDoc): `http://localhost:8000/redoc`

### Κανονικό Πρόγραμμα (email + terminal)
```bash
python -m src.main --send-daily-email
python -m src.main --check-incoming-portal
python -m src.main --help
```

Αυτό θα τρέξει το κανονικό πρόγραμμα με email και terminal output.

## API Endpoints

### GET /sede/daily
Επιστρέφει την ημερήσια αναφορά ΣΗΔΕ σε JSON μορφή.

**Response 200 (Success):**
```json
{
  "generated_at": "15/12/2025 15:40:23",
  "base_url": "https://shde.pkm.gov.gr",
  "is_historical_comparison": false,
  "comparison_date": null,
  "reference_date": null,
  "active": {
    "total": 29,
    "baseline_timestamp": "2025-12-04 09:34:33.873806",
    "changes": { "new": [], "activated": [], ... }
  },
  "all": {
    "total": 114,
    "baseline_timestamp": "2025-12-05 05:11.929456",
    "changes": { "new": [], "activated": [], ... }
  },
  "incoming": {
    "date": "2025-12-15",
    "reference_date": "2025-12-12",
    "records": [...],
    "changes": { "new": [...], "removed": [], ... },
    "real_new": [...],
    "test_new": [...],
    "stats": {
      "total": 3,
      "real": 3,
      "test": 0,
      "test_breakdown": {}
    }
  }
}
```

**Response 500 (Error):**
```json
{
  "error": "Error message here",
  "message": "Αποτυχία ανάκτησης αναφοράς ΣΗΔΕ"
}
```

## Ιδιότητες

✅ **Υπάρχον πρόγραμμα λειτουργεί κανονικά:**
- Email notifications: `--send-daily-email`
- Terminal output: `--check-incoming-portal`
- Όλες οι άλλες εντολές δουλεύουν όπως πριν

✅ **FastAPI ξεκινά αυτόματα:**
- Μόνο όταν το αρχείο τρέχει χωρίς arguments
- Προαιρετικό (δεν απαιτείται FastAPI για τις άλλες λειτουργίες)

✅ **Δεδομένα χωρίς side effects:**
- Δεν στέλνει email
- Δεν τυπώνει στο terminal
- Επιστρέφει καθαρά JSON

## Παράδειγμα χρήσης

### cURL
```bash
curl http://localhost:8000/sede/daily
```

### Python
```python
import httpx
response = httpx.get("http://localhost:8000/sede/daily")
report = response.json()
print(report["active"]["total"])  # 29
```

### JavaScript/Node.js
```javascript
const response = await fetch('http://localhost:8000/sede/daily');
const report = await response.json();
console.log(report.active.total);  // 29
```

## Σημειώσεις

- Το endpoint καλεί τη συνάρτηση `get_daily_sede_report()` από `sede_report.py`
- Χρησιμοποιεί τα ίδια δεδομένα και τη δυνατότητα ιστορικής σύγκρισης
- Το server τρέχει στο `0.0.0.0:8000` (διαθέσιμο από οποιοδήποτε interface)
- Για παραγωγή, χρησιμοποίησε reverse proxy (nginx, Cloudflare, κλπ)
- Το `/sede/daily` μπορεί να τροφοδοτήσει Power Automate Flow που στέλνει adaptive card στο group chat υποστήριξης. Προαιρετικά, το Flow κατεβάζει το `/sede/export/xls?scope=new|all` και επισυνάπτει το ημερήσιο Excel log (νέες ή όλες οι αιτήσεις).
