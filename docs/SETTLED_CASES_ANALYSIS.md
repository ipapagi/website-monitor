# Ανάλυση: Ενσωμάτωση "Διεκπεραιωμένων Υποθέσεων"

## 🔍 Συσχέτιση με Υπάρχον API

### ✅ Το Endpoint που Μνημόνευσες

```
GET /services/SearchServices/getSearchDataByQueryId?_dc=1770903173444&isPoll=false&queryId=19&queryOwner=2&isCase=false&stateId=welcomeGrid-45_dashboard0&page=1&start=0&limit=500
```

### ✅ Υπάρχουσα Υλοποίησή σου (Εισερχόμενες Αιτήσεις)

```
/services/SearchServices/getSearchDataByQueryId?isPoll=false&queryId=6&queryOwner=2&isCase=false&stateId=welcomeGrid-23_dashboard0&page=1&start=0&limit=200
```

**Στο αρχείο:** [src/config.py](src/config.py#L32-L40)

---

## 🎯 Η Συσχέτιση

Και τα δύο endpoints χρησιμοποιούν το **ίδιο backend service** (`SearchServices/getSearchDataByQueryId`), διαφέρουν όμως στις παράμετροι:

| Παράμετρος | Εισερχόμενες (queryId=6) | Διεκπεραιωμένες (queryId=19) |
|------------|--------------------------|------------------------------|
| **queryId** | `6` | `19` |
| **stateId** | `welcomeGrid-23_dashboard0` | `welcomeGrid-45_dashboard0` |
| **URI Location** | Dashboard tab 23 | Dashboard tab 45 |
| **Τι εκτελεί** | Αναζήτηση εγγράφων με κατάσταση "Εισερχόμενες" | Αναζήτηση εγγράφων με κατάσταση "Διεκπεραιωμένες" |

---

## 📊 Δεδομένα που Περιμένουμε

Βασιζόμενοι στη δομή των εισερχόμενων αιτήσεων σου, τα δεδομένα θα έχουν παρόμοια δομή:

```json
{
  "success": true,
  "data": [
    {
      "DOCID": "43342",
      "W007_P_FLD21": "941802",  // Case ID
      "W003_P_FLD75": "AOK-ΠΓ-268",  // Procedure Code
      "W003_P_FLD4": "Διαδικασία παραχώρησης...",  // Title
      "DESCRIPTION": "...",
      "W007_P_FLD20": "2025-12-10",  // Closed/Settled Date
      "W007_P_FLD19": "Ολοκληρωμένη",  // Status
      "CDATE": "2025-12-15 10:19:59",  // Submission/Creation Date
      ...
    }
  ],
  "total": 500
}
```

---

## 🔧 Τι Χρειάζεται να Κάνεις

### 1️⃣ **Δημιουργία Νέων Παραμέτρων** (ένα δευτερόλεπτο)

Προσθέστε σε [src/config.py](src/config.py) μια νέα σταθερά:

```python
SETTLED_CASES_DEFAULT_PARAMS = {
    'isPoll': False,
    'queryId': 19,
    'queryOwner': 2,
    'isCase': False,
    'stateId': 'welcomeGrid-45_dashboard0',
    'page': 1,
    'start': 0,
    'limit': 200
}
```

---

### 2️⃣ **Δημιουργία Module για Settled Cases** 

Αντίστοιχα του [src/incoming.py](src/incoming.py), δημιουργήστε ένα νέο αρχείο:

**`src/settled_cases.py`**

```python
"""Διαχείριση διεκπεραιωμένων υποθέσεων"""
import os
import json
from datetime import datetime
from config import get_project_root, SETTLED_CASES_DEFAULT_PARAMS
from api import sanitize_party_name

def get_settled_cases_snapshot_path(date_str):
    """Path για settled cases snapshot συγκεκριμένης ημερομηνίας"""
    settled_dir = os.path.join(get_project_root(), 'data', 'settled_cases')
    os.makedirs(settled_dir, exist_ok=True)
    return os.path.join(settled_dir, f'settled_{date_str}.json')

def save_settled_cases_snapshot(date_str, records):
    """Αποθηκεύει snapshot διεκπεραιωμένων υποθέσεων"""
    payload = {'date': date_str, 'count': len(records), 'records': records}
    with open(get_settled_cases_snapshot_path(date_str), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def fetch_settled_cases(monitor, settled_params=None):
    """Ανακτά διεκπεραιωμένες υποθέσεις με pagination αν χρειάζεται"""
    if settled_params is None:
        settled_params = SETTLED_CASES_DEFAULT_PARAMS.copy()
    else:
        settled_params = settled_params.copy()
    
    params = settled_params.copy()
    original_params = monitor.api_params.copy()
    all_records = []
    
    try:
        # Πρώτο request
        monitor.api_params = params
        data = monitor.fetch_page()
        
        if not data or not data.get('success'):
            return {'success': False, 'data': [], 'total': 0}
        
        all_records.extend(data.get('data', []))
        total = data.get('total', len(all_records))
        
        # Pagination αν υπάρχουν περισσότερες εγγραφές
        limit = params.get('limit', 200)
        while len(all_records) < total:
            params['start'] = len(all_records)
            monitor.api_params = params
            data = monitor.fetch_page()
            if not data or not data.get('success'):
                break
            new_records = data.get('data', [])
            if not new_records:
                break
            all_records.extend(new_records)
            print(f"  📋 Ανακτήθηκαν {len(all_records)}/{total} διεκπεραιωμένες υποθέσεις...")
        
        return {'success': True, 'data': all_records, 'total': total}
    finally:
        monitor.api_params = original_params

def simplify_settled_records(records):
    """Απλοποιεί τις εγγραφές διεκπεραιωμένων υποθέσεων"""
    simplified = []
    for rec in records:
        # Βασικά πεδία
        case_id = str(rec.get('W007_P_FLD21', '') or rec.get('DOCID', '')).strip()
        if not case_id:
            continue
        
        # Πεδία που μας ενδιαφέρουν
        simplified.append({
            'case_id': case_id,
            'doc_id': str(rec.get('DOCID', '')).strip(),
            'procedure_code': rec.get('W003_P_FLD75', ''),
            'procedure_title': rec.get('W003_P_FLD4', ''),
            'party': sanitize_party_name(rec.get('PARTY_NAME', '')),
            'settled_date': rec.get('W007_P_FLD20', ''),  # Ημερομηνία ολοκλήρωσης
            'status': rec.get('W007_P_FLD19', 'Ολοκληρωμένη'),
            'submission_date': rec.get('CDATE', ''),
            'protocol_number': rec.get('W007_P_FLD17', ''),
            'directory': rec.get('W007_P_FLD24', ''),
        })
    
    return simplified
```

---

### 3️⃣ **Ενσωμάτωση σε Daily Report** (προαιρετικά αλλά χρήσιμο)

Προσθέστε εντολή στον `daily_report.py` για να μπορείτε να βλέπετε τις διεκπεραιωμένες υποθέσεις της ημέρας:

```python
def get_settled_cases_for_date(monitor, target_date):
    """Ανακτά διεκπεραιωμένες υποθέσεις για συγκεκριμένη ημερομηνία"""
    from settled_cases import fetch_settled_cases, simplify_settled_records
    
    result = fetch_settled_cases(monitor, SETTLED_CASES_DEFAULT_PARAMS)
    if not result.get('success'):
        return None
    
    records = simplify_settled_records(result.get('data', []))
    
    # Φίλτρο: Μόνο εγγραφές που ολοκληρώθηκαν την συγκεκριμένη ημερομηνία
    today_settled = [r for r in records if r.get('settled_date', '').startswith(target_date)]
    
    return {
        'date': target_date,
        'total': len(today_settled),
        'records': today_settled,
        'fetched_at': datetime.now().isoformat()
    }
```

---

### 4️⃣ **Προσθήκη Endpoint στο FastAPI** (αν θέλετε API)

Σε [src/main.py](src/main.py), προσθέστε:

```python
@app.get("/sede/settled-cases/{date}")
async def get_settled_cases_for_date(date: str):
    """Διεκπεραιωμένες υποθέσεις ημερομηνίας YYYY-MM-DD"""
    from settled_cases import get_settled_cases_for_date
    
    result = get_settled_cases_for_date(monitor_instance, date)
    return result or {'error': 'No settled cases for this date', 'date': date}

@app.get("/sede/settled-cases")
async def get_all_settled_cases():
    """Όλες οι διεκπεραιωμένες υποθέσεις (τελευταία fetch)"""
    from settled_cases import fetch_settled_cases
    
    result = fetch_settled_cases(monitor_instance, SETTLED_CASES_DEFAULT_PARAMS)
    return result
```

---

## 🧪 Δοκιμή του Endpoint

### 1️⃣ **Με `curl` αν το endpoint είναι ενεργό**

```bash
curl -X GET "http://yourserver.com/services/SearchServices/getSearchDataByQueryId?isPoll=false&queryId=19&queryOwner=2&isCase=false&stateId=welcomeGrid-45_dashboard0&page=1&start=0&limit=50"
```

### 2️⃣ **Με Python στο environment σας**

```python
import requests
from src.session import PKMSession

session = PKMSession(
    base_url="http://yourserver.com",
    urls={...},
    login_params={...},
    username="...",
    password="..."
)

# Δοκιμή endpoint
params = {
    'isPoll': False,
    'queryId': 19,
    'queryOwner': 2,
    'isCase': False,
    'stateId': 'welcomeGrid-45_dashboard0',
    'page': 1,
    'start': 0,
    'limit': 50
}

response = session.fetch_data(params)
print(f"Success: {response.get('success')}")
print(f"Total records: {response.get('total')}")
print(f"Sample record: {response.get('data', [{}])[0]}")
```

---

## ✅ Σύνοψη Βημάτων

| Βήμα | Περιγραφή | Δυσκολία | Χρόνος |
|------|-----------|----------|--------|
| 1 | Προσθήκη σταθερών σε config.py | ⭐☆☆ | 2 λεπτά |
| 2 | Δημιουργία settled_cases.py | ⭐⭐☆ | 10 λεπτά |
| 3 | Ενσωμάτωση στο daily_report | ⭐⭐☆ | 5 λεπτά |
| 4 | Προσθήκη endpoints στο FastAPI | ⭐☆☆ | 5 λεπτά |
| 5 | Δοκιμή και fine-tuning | ⭐⭐⭐ | 20-30 λεπτά |

---

## ⚠️ Σημειώσεις

1. **Το `queryId=19` είναι για διεκπεραιωμένες υποθέσεις** - αυτό είναι πιθανόν το σωστό, αλλά **ελέγξτε στο UI του portal τι queryId χρησιμοποιεί το σύστημα** για το tab "Διεκπεραιωμένες Υποθέσεις" όταν φορτώνει τα δεδομένα (DevTools → Network tab)

2. **Τα δεδομένα που θα λάβετε θα έχουν παρόμοια δομή** με τις εισερχόμενες αιτήσεις, αλλά:
   - Δεν θα έχουν πεδίο `is_test` (ή θα είναι πάντα false)
   - Θα έχουν πεδία για ημερομηνία ολοκλήρωσης (`W007_P_FLD20`)
   - Θα έχουν διαφορετικό status field

3. **Πιθανές εναλλακτικές queryIds:**
   - `queryId=6` → Εισερχόμενες
   - `queryId=19` → Διεκπεραιωμένες (ή mightΕΊναι άλλο - **ελέγξτε**)
   - Άλλες τιμές για άλλα είδη αναζητήσεων (π.χ., σε εξέλιξη, διανεμημένες κλπ)

---

## 🔗 Σχετικά αρχεία

- [src/config.py](src/config.py) - Configuration
- [src/incoming.py](src/incoming.py) - Παρόμοια υλοποίηση για εισερχόμενες
- [src/api.py](src/api.py) - API utilities
- [src/monitor.py](src/monitor.py) - Monitor class
- [src/main.py](src/main.py) - FastAPI app
