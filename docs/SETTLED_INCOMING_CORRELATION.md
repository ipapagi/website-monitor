# Συσχέτιση Εισερχόμενων με Διεκπεραιωμένες Υποθέσεις & Χρεώσεις

## Επισκόπηση

Το σύστημα παρέχει τρεις κύριες λειτουργίες συσχέτισης:

1. **Settled Cases** - Αφαίρεση διεκπεραιωμένων αιτήσεων από αναφορές
2. **Charge Matching** - Εύρεση υπαλλήλου που έχει χρεωθεί για κάθε αίτηση
3. **API Enrichment** - Δύο-βηματική API κλήση για ενδιαφερόμενες χρεώσεις

---

## 🔴 NEW: Charge Matching & API Enrichment

### Overview

Το σύστημα τώρα ταιριάζει χρεώσεις και εμπλουτίζει records με ονόματα υπαλλήλων.

**Success Rates:**
- Direct matching (queryId=19): 55/177 (31.1%)
- API enrichment (two-step): 37/122 (92.5% of unmatched)
- **Total:** 92/177 (52%)

### Charge Matching (Direct)

```python
from charges import fetch_charges, add_charge_info

# Ανάκτηση χρεώσεων
charges_records, charges_by_pkm = fetch_charges(monitor)

# Εμπλουτισμός records
records = add_charge_info(records, charges_by_pkm)

# Κάθε record τώρα έχει:
# record['_charge'] = {
#     'charged': True/False,
#     'employee': 'ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ'
# }
```

### API Enrichment (Two-Step)

Για records **χωρίς** direct match:

**Step 1:** GET `/7/{doc_id}` → Extract charge DOCID from W007_P_FLD7.docIds[0]  
**Step 2:** GET `/2/{charge_doc_id}` → Extract employee from W001_P_FLD10

```python
from charges import enrich_charge_with_employee

# Εμπλουτισμός απλής αίτησης
employee = enrich_charge_with_employee(monitor, doc_id)

# Returns: "ΑΝΑΝΙΑΔΟΥ ΘΕΟΦΑΝΩ" ή None
```

### Integration

Όλες οι αναφορές τώρα χρησιμοποιούν:

```python
# Με API enrichment ενεργοποιημένο (92.5% success)
records = add_charge_info(
    records, 
    charges_by_pkm, 
    monitor=monitor,          # ← Χρεώνεται για API calls
    enrich_missing=True        # ← Ενεργοποίηση enrichment
)
```

**Files Modified:**
- `src/charges.py` (Lines 485-604): New enrichment functions
- `src/charges.py` (Line 428): **CRITICAL** - Department filter fix
  - Use ONLY `W001_P_FLD10` (employee names)
  - Removed `USER_GROUP_ID_TO` (departments not acceptable)
- `src/daily_report.py`, `src/sede_report.py`, `src/weekly_report_generator.py`: Integration

---

## Μηχανισμός Συσχέτισης (Settled Cases)

### Πεδία Συσχέτισης

| Endpoint | Πεδίο | Περιγραφή |
|----------|-------|-----------|
| **Εισερχόμενες** | `W007_P_FLD7` | "Αφορά Υπόθεση" - Περιέχει τον κωδικό υπόθεσης |
| **Διεκπεραιωμένες** | `W001_P_FLD2` | "Κωδ. Υπόθεσης" - Μοναδικός κωδικός υπόθεσης |

### Format Κωδικού Υπόθεσης

```
Εισερχόμενες (W007_P_FLD7): "Αίτημα 2026/105673 ΜΟΥΡΑΤΙΔΟΥ-128272645"
                                     ^^^^^^^^^^^^
Διεκπεραιωμένες (W001_P_FLD2):      "2026/105673"
```

### Κανόνας για Συμπληρωματικά Αιτήματος (NEW)

Για records με τύπο `Συμπληρωματικά Αιτήματος`:

1. Γίνεται extract του parent case key (`YYYY/CASE_ID`) από το πεδίο `related_case` (W007_P_FLD7 extended text)
2. Γίνεται lookup του parent key στο settled index (`W001_P_FLD2` από queryId=19)
3. Αν το parent case είναι διεκπεραιωμένο, τότε και το supplement record θεωρείται διεκπεραιωμένο

Με αυτόν τον κανόνα, τα supplement records που δείχνουν σε ήδη διεκπεραιωμένη υπόθεση **εξαιρούνται** από τα open apps reports/exports.

## Λειτουργίες API

### 1. `correlate_incoming_with_settled()`

Συσχετίζει όλες τις εισερχόμενες με τις διεκπεραιωμένες και επιστρέφει πλήρη ανάλυση.

```python
from settled_cases import correlate_incoming_with_settled

# Ανάκτηση δεδομένων
incoming = [...]  # Λίστα εισερχόμενων (raw ή simplified)
settled = [...]   # Λίστα διεκπεραιωμένων (raw ή simplified)

# Συσχέτιση
result = correlate_incoming_with_settled(incoming, settled)

# Δομή αποτελέσματος
{
    'correlated': [
        {
            'incoming': {...},      # Η εισερχόμενη αίτηση
            'settled': {...},       # Η διεκπεραιωμένη υπόθεση
            'case_code': '2026/105673'
        },
        ...
    ],
    'incoming_without_settled': [...],  # Εισερχόμενες χωρίς διεκπεραίωση
    'settled_without_incoming': [...],  # Διεκπεραιωμένες χωρίς εισερχόμενη
    'stats': {
        'total_incoming': 175,
        'total_settled': 55,
        'matched': 14,
        'match_rate': 0.08  # 8%
    }
}
```

### 2. `filter_out_settled_from_incoming()`

Αφαιρεί τις διεκπεραιωμένες από τις εισερχόμενες αιτήσεις.

```python
from settled_cases import filter_out_settled_from_incoming

# Φιλτράρισμα
active_incoming = filter_out_settled_from_incoming(incoming, settled)

print(f"Εισερχόμενες: {len(incoming)}")
print(f"Διεκπεραιωμένες: {len(settled)}")
print(f"Ενεργές: {len(active_incoming)}")
```

**Χρήση σε αναφορές:**

```python
# Στην daily_report.py ή άλλο report generator
from settled_cases import fetch_settled_cases, filter_out_settled_from_incoming

# Ανάκτηση διεκπεραιωμένων
settled_result = fetch_settled_cases(monitor)
settled_records = settled_result.get('data', [])

# Φιλτράρισμα εισερχόμενων
active_incoming = filter_out_settled_from_incoming(
    all_incoming_records,
    settled_records
)

# Δημιουργία αναφοράς μόνο με ενεργές
generate_report(active_incoming)
```

### 3. `get_settled_for_incoming()`

Βρίσκει τη διεκπεραιωμένη υπόθεση για μια συγκεκριμένη εισερχόμενη αίτηση.

```python
from settled_cases import get_settled_for_incoming

# Για μια συγκεκριμένη εισερχόμενη
incoming_record = {...}
settled_record = get_settled_for_incoming(incoming_record, all_settled)

if settled_record:
    print(f"✅ Η αίτηση έχει διεκπεραιωθεί")
    print(f"   Κωδ. Υπόθεσης: {settled_record.get('W001_P_FLD2')}")
    print(f"   Ημ/νία: {settled_record.get('W001_P_FLD8')}")
else:
    print(f"⏳ Η αίτηση εκκρεμεί")
```

## Παραδείγματα Χρήσης

### Παράδειγμα 1: Πλήρης Ανάλυση Συσχέτισης

```python
from monitor import PKMMonitor
from settled_cases import fetch_settled_cases, correlate_incoming_with_settled
from config import load_config
from utils import load_config

# Σύνδεση
config = load_config('config/config.yaml')
monitor = PKMMonitor(...)
monitor.login()

# Ανάκτηση δεδομένων
monitor.api_params = config['api_params']
incoming_data = monitor.fetch_page()
incoming_records = incoming_data.get('data', [])

settled_result = fetch_settled_cases(monitor)
settled_records = settled_result.get('data', [])

# Συσχέτιση
correlation = correlate_incoming_with_settled(incoming_records, settled_records)

# Αποτελέσματα
print(f"\n📊 Στατιστικά Συσχέτισης:")
print(f"   Εισερχόμενες: {correlation['stats']['total_incoming']}")
print(f"   Διεκπεραιωμένες: {correlation['stats']['total_settled']}")
print(f"   Αντιστοιχίες: {correlation['stats']['matched']}")
print(f"   Ποσοστό: {correlation['stats']['match_rate']:.1%}")

print(f"\n✅ Διεκπεραιωμένες αιτήσεις:")
for item in correlation['correlated']:
    case_code = item['case_code']
    inc = item['incoming']
    settled = item['settled']
    party = inc.get('W007_P_FLD13', '')[:40]
    completion = settled.get('W001_P_FLD8', '')
    print(f"   • {case_code:15} | {party:40} | {completion}")

print(f"\n⏳ Ενεργές αιτήσεις ({len(correlation['incoming_without_settled'])}):")
for inc in correlation['incoming_without_settled'][:5]:
    party = inc.get('W007_P_FLD13', '')[:40]
    subject = inc.get('W007_P_FLD6', '')[:50]
    print(f"   • {party:40} | {subject}")
```

### Παράδειγμα 2: Δημιουργία Αναφοράς Μόνο με Ενεργές

```python
def generate_active_requests_report(monitor, date):
    """Δημιουργεί αναφορά μόνο με ενεργές (μη διεκπεραιωμένες) αιτήσεις"""
    from incoming import load_incoming_snapshot
    from settled_cases import fetch_settled_cases, filter_out_settled_from_incoming
    
    # Φόρτωση snapshot εισερχόμενων
    snapshot = load_incoming_snapshot(date)
    if not snapshot:
        print(f"❌ Δεν βρέθηκε snapshot για {date}")
        return
    
    incoming_records = snapshot.get('records', [])
    
    # Ανάκτηση διεκπεραιωμένων
    settled_result = fetch_settled_cases(monitor)
    settled_records = settled_result.get('data', [])
    
    # Φιλτράρισμα
    active_records = filter_out_settled_from_incoming(
        incoming_records,
        settled_records
    )
    
    print(f"\n📋 Ενεργές Αιτήσεις για {date}")
    print(f"   Σύνολο εισερχόμενων: {len(incoming_records)}")
    print(f"   Διεκπεραιωμένες: {len(incoming_records) - len(active_records)}")
    print(f"   Ενεργές: {len(active_records)}")
    
    # Δημιουργία αναφοράς με τις ενεργές
    return active_records

# Χρήση
active = generate_active_requests_report(monitor, '2026-02-13')
```

### Παράδειγμα 3: Έλεγχος Κατάστασης Αίτησης

```python
def check_request_status(incoming_record, monitor):
    """Ελέγχει αν μια αίτηση έχει διεκπεραιωθεί"""
    from settled_cases import fetch_settled_cases, get_settled_for_incoming
    
    # Ανάκτηση διεκπεραιωμένων
    settled_result = fetch_settled_cases(monitor)
    settled_records = settled_result.get('data', [])
    
    # Έλεγχος
    settled = get_settled_for_incoming(incoming_record, settled_records)
    
    party = incoming_record.get('W007_P_FLD13', '')
    
    if settled:
        case_code = settled.get('W001_P_FLD2', '')
        completion_date = settled.get('W001_P_FLD8', '')
        status = settled.get('W001_P_FLD9', '')
        
        print(f"✅ ΔΙΕΚΠΕΡΑΙΩΘΗΚΕ")
        print(f"   Συναλλασσόμενος: {party}")
        print(f"   Κωδ. Υπόθεσης: {case_code}")
        print(f"   Ημ/νία: {completion_date}")
        print(f"   Κατάσταση: {status}")
    else:
        print(f"⏳ ΕΚΚΡΕΜΕΙ")
        print(f"   Συναλλασσόμενος: {party}")
        pkm_number = incoming_record.get('W007_P_FLD21', '')
        if pkm_number:
            print(f"   Αρ. ΠΚΜ: {pkm_number}")

# Χρήση
check_request_status(some_incoming_record, monitor)
```

## Ενσωμάτωση σε Υπάρχοντα Reports

### Daily Report με Φιλτράρισμα

```python
# Στο src/daily_report.py

def send_daily_report_filtered(date, exclude_settled=True):
    """Αποστολή ημερήσιας αναφοράς με επιλογή αποκλεισμού διεκπεραιωμένων"""
    
    # ... existing code ...
    
    if exclude_settled:
        from settled_cases import fetch_settled_cases, filter_out_settled_from_incoming
        
        # Ανάκτηση διεκπεραιωμένων
        settled_result = fetch_settled_cases(monitor)
        settled_records = settled_result.get('data', [])
        
        # Φιλτράρισμα από όλα τα records (new, all, etc.)
        if new_records:
            new_records = filter_out_settled_from_incoming(new_records, settled_records)
        
        print(f"ℹ️  Αφαιρέθηκαν διεκπεραιωμένες: {len(settled_records)} αφορούν εισερχόμενες")
    
    # ... continue with report generation ...
```

### Weekly Report με Στατιστικά

```python
# Στο src/weekly_report_generator.py

def add_settlement_statistics(report_data, monitor):
    """Προσθέτει στατιστικά διεκπεραίωσης στην εβδομαδιαία αναφορά"""
    from settled_cases import (
        fetch_settled_cases, 
        correlate_incoming_with_settled,
        simplify_settled_records
    )
    
    # Ανάκτηση
    incoming_records = report_data.get('all_records', [])
    settled_result = fetch_settled_cases(monitor)
    settled_raw = settled_result.get('data', [])
    settled_records = simplify_settled_records(settled_raw)
    
    # Συσχέτιση
    correlation = correlate_incoming_with_settled(incoming_records, settled_raw)
    
    # Προσθήκη στατιστικών
    report_data['settlement_stats'] = {
        'total_settled': len(settled_records),
        'matched_with_incoming': correlation['stats']['matched'],
        'match_rate': f"{correlation['stats']['match_rate']:.1%}",
        'completed_this_week': len([
            r for r in settled_records 
            if r.get('completion_date', '').startswith(report_data['week'])
        ])
    }
    
    return report_data
```

## Best Practices

### 1. **Caching Διεκπεραιωμένων**
```python
# Αποθήκευση για επαναχρησιμοποίηση
settled_cache = None

def get_settled_cached(monitor):
    global settled_cache
    if not settled_cache:
        result = fetch_settled_cases(monitor)
        settled_cache = result.get('data', [])
    return settled_cache
```

### 2. **Περιοδική Ενημέρωση**
```python
# Ενημέρωση cache κάθε 1 ώρα
import time
last_fetch = 0
CACHE_DURATION = 3600  # 1 hour

def get_settled_with_refresh(monitor):
    global settled_cache, last_fetch
    now = time.time()
    
    if not settled_cache or (now - last_fetch) > CACHE_DURATION:
        result = fetch_settled_cases(monitor)
        settled_cache = result.get('data', [])
        last_fetch = now
    
    return settled_cache
```

### 3. **Logging Συσχετίσεων**
```python
import logging

def log_correlation_info(correlation):
    """Καταγραφή πληροφοριών συσχέτισης"""
    logger = logging.getLogger(__name__)
    
    stats = correlation['stats']
    logger.info(f"Correlation completed:")
    logger.info(f"  - Total incoming: {stats['total_incoming']}")
    logger.info(f"  - Total settled: {stats['total_settled']}")
    logger.info(f"  - Matched: {stats['matched']} ({stats['match_rate']:.1%})")
    
    # Log διεκπεραιωμένες
    for item in correlation['correlated']:
        case_code = item['case_code']
        logger.debug(f"  ✅ {case_code} completed")
```

## Troubleshooting

### Δεν βρίσκει αντιστοιχίες

1. **Έλεγχος format πεδίου "Αφορά Υπόθεση":**
   ```python
   for rec in incoming_records[:5]:
       case_ref = rec.get('W007_P_FLD7', '')
       print(f"Case ref: {case_ref}")
   ```

2. **Έλεγχος κωδικών υπόθεσης:**
   ```python
   for rec in settled_records[:5]:
       case_code = rec.get('W001_P_FLD2', '')
       print(f"Case code: {case_code}")
   ```

3. **Test extraction:**
   ```python
   from settled_cases import _extract_case_code_from_reference
   
   test_refs = [
       "Αίτημα 2026/105673 ΜΟΥΡΑΤΙΔΟΥ-128272645",
       "2026/105673",
       "Αίτηση 2025/999999"
   ]
   
   for ref in test_refs:
       code = _extract_case_code_from_reference(ref)
       print(f"{ref} -> {code}")
   ```

### Performance Issues

Για μεγάλο όγκο δεδομένων:

```python
# Χρήση set για O(1) lookups
def fast_filter_settled(incoming, settled):
    from settled_cases import _extract_case_code_from_reference
    
    # Δημιουργία set από case codes
    settled_codes = {
        rec.get('W001_P_FLD2', '').strip().upper()
        for rec in settled
        if rec.get('W001_P_FLD2')
    }
    
    # Fast filtering
    active = []
    for inc in incoming:
        case_ref = inc.get('W007_P_FLD7', '')
        case_code = _extract_case_code_from_reference(case_ref)
        
        if not case_code or case_code not in settled_codes:
            active.append(inc)
    
    return active
```

## Σχετική Τεκμηρίωση

- [SETTLED_CASES_ANALYSIS.md](SETTLED_CASES_ANALYSIS.md) - Πλήρης ανάλυση διεκπεραιωμένων
- [SETTLED_CASES_SUMMARY.md](SETTLED_CASES_SUMMARY.md) - Σύντομη αναφορά
- [TEST_SETTLED_CASES.md](TEST_SETTLED_CASES.md) - Οδηγός testing
