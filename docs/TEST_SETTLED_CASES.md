# 🧪 Δοκιμή Ενσωμάτωσης Διεκπεραιωμένων Υποθέσεων

## Γρήγορη Δοκιμή 

### 1️⃣ **Δοκιμή Endpoint απευθείας** (Πιο αξιόπιστο)

Ανοίξτε ένα terminal και δοκιμάστε το endpoint με curl:

```bash
# Αντικαταστήστε τα ${PLACEHOLDER} με τις πραγματικές τιμές της εγκατάστασης
curl -X GET "http://yourserver.com/services/SearchServices/getSearchDataByQueryId?isPoll=false&queryId=19&queryOwner=2&isCase=false&stateId=welcomeGrid-45_dashboard0&start=0&limit=50"
```

Αναμενόμενη απάντηση:
```json
{
  "success": true,
  "data": [
    {
      "DOCID": "43342",
      "W007_P_FLD21": "941802",
      "W003_P_FLD75": "AOK-ΠΓ-268",
      ...
    }
  ],
  "total": 500
}
```

---

### 2️⃣ **Δοκιμή με Python Script**

Δημιουργήστε ένα νέο αρχείο: `test_settled_cases.py`

```python
"""Δοκιμή integrated settled_cases module"""
import sys
from datetime import datetime
from src.monitor import PKMMonitor
from src.config import SETTLED_CASES_DEFAULT_PARAMS
from src.settled_cases import (
    fetch_settled_cases,
    simplify_settled_records,
    get_settled_cases_for_date,
    save_settled_cases_snapshot,
    get_settlement_statistics
)

# Αρχικοποίηση Monitor (χρησιμοποιήστε τις δικές σας παραμέτρους)
monitor = PKMMonitor(
    base_url="http://yourserver.com",
    urls={
        'home': 'http://yourserver.com',
        'login': 'http://yourserver.com/login',
        'api': 'http://yourserver.com/api'
    },
    login_params={
        'username_field': 'uname',
        'password_field': 'pswd',
        'submit_button': 'login'
    },
    username="your_username",
    password="your_password"
)

def test_basic_fetch():
    """Δοκιμή 1: Βασική ανάκτηση δεδομένων"""
    print("\n🧪 Test 1: Βασική ανάκτηση διεκπεραιωμένων υποθέσεων")
    print("-" * 60)
    
    result = fetch_settled_cases(monitor, SETTLED_CASES_DEFAULT_PARAMS)
    
    print(f"✅ Success: {result.get('success')}")
    print(f"📊 Total records: {result.get('total')}")
    
    if result.get('data'):
        print(f"📋 Sample record keys: {list(result['data'][0].keys())}")
    
    return result

def test_simplification(raw_result):
    """Δοκιμή 2: Απλοποίηση εγγραφών"""
    print("\n🧪 Test 2: Απλοποίηση εγγραφών")
    print("-" * 60)
    
    simplified = simplify_settled_records(raw_result.get('data', []))
    
    print(f"✅ Simplified records: {len(simplified)}")
    if simplified:
        first = simplified[0]
        print(f"📋 Sample simplified record:")
        for key, value in first.items():
            if key != 'procedure_title':  # Αποφύγετε πολύ μεγάλα strings
                print(f"   {key}: {value}")
    
    return simplified

def test_date_filter():
    """Δοκιμή 3: Φίλτρο ημερομηνίας"""
    print("\n🧪 Test 3: Ανάκτηση για συγκεκριμένη ημερομηνία")
    print("-" * 60)
    
    today = datetime.now().strftime('%Y-%m-%d')
    result = get_settled_cases_for_date(monitor, today)
    
    print(f"📅 Date: {result.get('date')}")
    print(f"📊 Found: {result.get('total')} cases settled today")
    print(f"🕐 Fetched at: {result.get('fetched_at')}")
    
    return result

def test_snapshot_save(simplified_records):
    """Δοκιμή 4: Αποθήκευση snapshot"""
    print("\n🧪 Test 4: Αποθήκευση snapshot")
    print("-" * 60)
    
    today = datetime.now().strftime('%Y-%m-%d')
    path = save_settled_cases_snapshot(today, simplified_records)
    
    print(f"✅ Snapshot saved to: {path}")
    print(f"📊 Records in snapshot: {len(simplified_records)}")
    
    return path

def test_statistics(simplified_records):
    """Δοκιμή 5: Στατιστικά"""
    print("\n🧪 Test 5: Στατιστικά ολοκλήρωσης")
    print("-" * 60)
    
    stats = get_settlement_statistics(simplified_records)
    
    print(f"📊 Total cases: {stats.get('total')}")
    if stats.get('avg_days') is not None:
        print(f"⏱️  Average days to settle: {stats.get('avg_days'):.1f}")
        print(f"📉 Min days: {stats.get('min_days')}")
        print(f"📈 Max days: {stats.get('max_days')}")
        print(f"📊 Median days: {stats.get('median_days')}")
    
    return stats

def main():
    """Εκτέλεση όλων των δοκιμών"""
    print("\n" + "=" * 60)
    print("🚀 ΟΛΟΚΛΗΡΩΜΕΝΗ ΔΟΚΙΜΗ SETTLED CASES MODULE")
    print("=" * 60)
    
    try:
        # Test 1: Fetch
        raw_result = test_basic_fetch()
        if not raw_result.get('success'):
            print("❌ Ανεπιτυχής ανάκτηση - ακύρωση:")
            return
        
        # Test 2: Simplify
        simplified = test_simplification(raw_result)
        if not simplified:
            print("⚠️  Δεν υπάρχουν απλοποιημένες εγγραφές - συνεχίζοντας")
            simplified = []
        
        # Test 3: Date filter
        test_date_filter()
        
        # Test 4: Save snapshot
        if simplified:
            test_snapshot_save(simplified)
        
        # Test 5: Statistics
        if simplified:
            test_statistics(simplified)
        
        print("\n" + "=" * 60)
        print("✅ ΟΛΕ ΟΙ ΔΟΚΙΜΕΣ ΟΛΟΚΛΗΡΩΘΗΚΑΝ ΕΠΙΤΥΧΩΣ!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Σφάλμα κατά την εκτέλεση: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
```

**Εκτέλεση:**
```bash
python test_settled_cases.py
```

---

### 3️⃣ **Δοκιμή FastAPI Endpoint** (αν το προσθέσετε)

Μόλις προσθέσετε τα endpoints στο `src/main.py`, δοκιμάστε τα:

```bash
# Εκκίνηση API server
uvicorn src.main:app --reload

# Σε άλλο terminal
curl http://localhost:8000/sede/settled-cases
curl http://localhost:8000/sede/settled-cases/2026-02-12
```

---

## ✅ Checklist Δοκιμής

- [ ] Ο endpoint του server απαντά με `success: true`
- [ ] Τα δεδομένα περιέχουν τουλάχιστον ένα record
- [ ] Τα πεδία που περιμένατε είναι παρόντα (`W007_P_FLD20`, `W007_P_FLD19`, κλπ)
- [ ] Λειτουργεί σωστά η απλοποίηση
- [ ] Το φίλτρο ημερομηνίας λειτουργεί
- [ ] Τα snapshots αποθηκεύονται σωστά
- [ ] Τα στατιστικά υπολογίζονται χωρίς σφάλματα

---

## 🔍 Troubleshooting

### ❌ "χαμηλή API response: `success: false`"

**Ενδεχόμενό αίτιο:** Το `queryId=19` ίσως να μην είναι σωστό για διεκπεραιωμένες υποθέσεις

**Λύση:** 
1. Ανοίξτε το UI του portal χρησιμοποιώντας DevTools (F12)
2. Πηγαίνετε στο tab "Network"
3. Ανοίξτε το tab "Διεκπεραιωμένες Υποθέσεις"
4. Δείτε τι `queryId` χρησιμοποιεί το request
5. Ενημερώστε το `SETTLED_CASES_DEFAULT_PARAMS` στο `config.py`

### ❌ "Τα πεδία που περιμένατε δεν υπάρχουν"

**Ενδεχόμενό αίτιο:** Τα field names είναι διαφορετικά

**Λύση:**
1. Τυπώστε ολόκληρο το record από τη δοκιμή Python
2. Δείτε ποια πεδία υπάρχουν πραγματικά
3. Ενημερώστε τη συνάρτηση `simplify_settled_records()` στο `src/settled_cases.py`

### ❌ "Δεν λειτουργεί η αρχική σύνδεση"

**Ενδεχόμενό αίτιο:** Προβλήματα με authentication - ίσως δεν έχει ενημερωθεί η session

**Λύση:**
```python
# Δοκιμάστε να φέρετε άλλα δεδομένα πρώτα για να δείτε αν η session είναι έγκυρη
result = monitor.fetch_page()  # Χρησιμοποιεί υπάρχουσες api_params
print(f"Session valid: {result is not None}")
```

---

## 📊 Αναμενόμενη Δομή Δεδομένων

Τα δεδομένα διεκπεραιωμένων υποθέσεων πρέπει να είναι παρόμοια με αυτά:

```json
{
  "case_id": "941802",
  "doc_id": "43342",
  "procedure_code": "AOK-ΠΓ-268",
  "procedure_title": "Διαδικασία παραχώρησης κατά χρήση ακινήτων...",
  "party": "ΑΓΓΕΛΟΣ ΓΑΡΟΥΦΑΛΙΑΣ",
  "settled_date": "2025-12-10",
  "status": "Ολοκληρωμένη",
  "submission_date": "2025-12-02 10:19:59.817827",
  "protocol_number": "5607",
  "directory": "ΔΙΕΥΘΥΝΣΗ ΠΟΛΙΤΙΚΗΣ ΓΗΣ",
  "days_to_settle": 8
}
```

---

## 🎯 Επόμενα Βήματα (αν όλα πάνε καλά)

1. ✅ Δοκιμάστε τη βασική ανάκτηση
2. ✅ Αποθηκεύστε ημερήσια snapshots αυτόματα
3. ✅ Προσθέστε στο daily report
4. ✅ Δημιουργήστε FastAPI endpoints
5. ✅ Ενσωματώστε στο monitoring system
