# PKM Monitor API - Πλήρης Οδηγός Endpoints

## 📖 Βασική Χρήση

**Base URL:** `http://localhost:8000`

**API Documentation (Swagger):** `http://localhost:8000/docs`

**Alternative Documentation (ReDoc):** `http://localhost:8000/redoc`

---

## 📊 ΠΛΗΡΗΣ ΑΝΑΦΟΡΑ

### GET /sede/daily
Επιστρέφει την πλήρη ημερήσια αναφορά ΣΗΔΕ με όλα τα δεδομένα.

**Response:** Πλήρες JSON με active, all, incoming

---

## 📈 ΣΤΑΤΙΣΤΙΚΑ & ΣΥΝΟΨΗ

### GET /sede/summary
Σύνοψη με βασικά νούμερα (totals, changes)

**Response:**
```json
{
  "totals": {
    "active_procedures": 29,
    "all_procedures": 114,
    "incoming_total": 114,
    "incoming_real": 10,
    "incoming_test": 104
  },
  "changes": {
    "active_new": 0,
    "incoming_new_real": 0,
    "incoming_new_test": 3
  }
}
```

### GET /sede/stats
Λεπτομερή στατιστικά με ποσοστά

**Response:** Procedures stats, incoming stats με percentages, baselines

---

## 📥 ΕΙΣΕΡΧΟΜΕΝΕΣ ΑΙΤΗΣΕΙΣ

### GET /sede/incoming
Όλες οι εισερχόμενες αιτήσεις

### GET /sede/incoming/new
Μόνο νέες αιτήσεις (real + test)

**Response:**
```json
{
  "date": "2025-12-16",
  "real": [...],
  "test": [...],
  "total": 3
}
```

### GET /sede/incoming/real
Μόνο πραγματικές αιτήσεις (χωρίς δοκιμαστικές)

### GET /sede/incoming/test
Μόνο δοκιμαστικές αιτήσεις

### GET /sede/incoming/changes
Αλλαγές εισερχόμενων (new, removed, modified)

### GET /sede/incoming/{date}
Snapshot συγκεκριμένης ημερομηνίας

**Example:** `/sede/incoming/2025-12-15`

---

## 📋 ΔΙΑΔΙΚΑΣΙΕΣ

### GET /sede/procedures/active
Μόνο ενεργές διαδικασίες

### GET /sede/procedures/all
Όλες οι διαδικασίες

### GET /sede/procedures/changes
Αλλαγές διαδικασιών (new, activated, deactivated, modified)

### GET /sede/procedures/inactive
Πλήθος ανενεργών διαδικασιών

---

## 🔍 ΑΝΑΖΗΤΗΣΗ & ΦΙΛΤΡΑ

### GET /sede/search?q={query}
Αναζήτηση σε διαδικασίες και αιτήσεις

**Example:** `/sede/search?q=ΑΓΓΕΛΟΣ`

**Response:**
```json
{
  "query": "ΑΓΓΕΛΟΣ",
  "incoming": [...],
  "procedures": [...],
  "totals": {
    "incoming": 2,
    "procedures": 0
  }
}
```

### GET /sede/incoming/filter
Φιλτράρει εισερχόμενες αιτήσεις

**Parameters:**
- `party` - Όνομα συναλλασσόμενου
- `procedure` - Κωδικός ή τίτλος διαδικασίας
- `date_from` - Από ημερομηνία (YYYY-MM-DD)
- `date_to` - Έως ημερομηνία (YYYY-MM-DD)

**Example:** `/sede/incoming/filter?party=ΑΓΓΕΛΟΣ&date_from=2025-12-01`

---

## 📅 ΙΣΤΟΡΙΚΟ & TRENDS

### GET /sede/history/daily?days={n}
Ιστορικό τελευταίων n ημερών

**Example:** `/sede/history/daily?days=7`

**Response:**
```json
{
  "days": 7,
  "history": [
    {
      "date": "2025-12-16",
      "total": 114,
      "real": 10,
      "test": 104
    },
    ...
  ]
}
```

### GET /sede/comparison?date1={date1}&date2={date2}
Σύγκριση δύο ημερομηνιών

**Example:** `/sede/comparison?date1=2025-12-15&date2=2025-12-16`

**Response:**
```json
{
  "date1": "2025-12-15",
  "date2": "2025-12-16",
  "date1_stats": {...},
  "date2_stats": {...},
  "changes": {...},
  "diff": {
    "total": 0,
    "real": 0,
    "test": 3
  }
}
```

### GET /sede/trends/weekly
Weekly trends (τελευταίες 4 εβδομάδες)

**Response:**
```json
{
  "weeks": [
    {
      "week": 1,
      "days": [...],
      "totals": {
        "total": 800,
        "real": 70,
        "test": 730
      }
    },
    ...
  ]
}
```

---

## ⚡ HEALTH & STATUS

### GET /health
Health check του API

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-16 10:00:00",
  "api_version": "1.0.0",
  "data_available": {
    "active_baseline": true,
    "all_baseline": true
  }
}
```

### GET /sede/baseline
Πληροφορίες baseline

**Response:** Timestamps και counts για active/all/incoming baselines

### GET /sede/last-update
Πότε ανανεώθηκαν τα δεδομένα

---

## 📄 EXPORT

### GET /sede/export/csv
Export εισερχόμενων αιτήσεων σε CSV

**Response:** Κατέβασμα CSV αρχείου

---

## 💡 Παραδείγματα Χρήσης

### cURL
```bash
# Σύνοψη
curl http://localhost:8000/sede/summary

# Νέες πραγματικές αιτήσεις
curl http://localhost:8000/sede/incoming/real

# Αναζήτηση
curl "http://localhost:8000/sede/search?q=AOK"

# Ιστορικό
curl http://localhost:8000/sede/history/daily?days=7

# CSV Export
curl http://localhost:8000/sede/export/csv -o incoming.csv
```

### Python
```python
import httpx

# Σύνοψη
response = httpx.get("http://localhost:8000/sede/summary")
summary = response.json()
print(f"Ενεργές: {summary['totals']['active_procedures']}")

# Φίλτρο
response = httpx.get("http://localhost:8000/sede/incoming/filter", 
                     params={"party": "ΑΓΓΕΛΟΣ", "date_from": "2025-12-01"})
results = response.json()
print(f"Βρέθηκαν: {results['total']} αιτήσεις")
```

### JavaScript
```javascript
// Στατιστικά
const response = await fetch('http://localhost:8000/sede/stats');
const stats = await response.json();
console.log(`Real: ${stats.incoming.real_percentage}%`);

// Σύγκριση
const comp = await fetch(
  'http://localhost:8000/sede/comparison?date1=2025-12-15&date2=2025-12-16'
);
const diff = await comp.json();
console.log(`Διαφορά: ${diff.diff.total} αιτήσεις`);
```

---

## 📌 Σημειώσεις

✅ Όλα τα endpoints επιστρέφουν JSON  
✅ Error responses: `{"error": "...", "message": "..."}`  
✅ Ημερομηνίες σε format: YYYY-MM-DD  
✅ Για production: Προσθήκη authentication & rate limiting

---

## 🚀 Εκκίνηση

```bash
# Development (με reload)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Ανοίξε `http://localhost:8000/docs` για interactive documentation! 📖
