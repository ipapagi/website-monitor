# ΧΡΕΩΣΕΙΣ ΕΚΚΡΕΜΩΝ ΥΠΟΘΕΣΕΩΝ - Οδηγός Χρήσης

## Επισκόπηση

Το module **charges.py** παρέχει λειτουργικότητα για την ανάκτηση και διαχείριση χρεώσεων υπαλλήλων σε εκκρεμείς υποθέσεις. Οι χρεώσεις αντλούνται από το API endpoint `queryId=19` και συσχετίζονται με τις εισερχόμενες αιτήσεις.

## Βασικά Στοιχεία

- **API Endpoint**: `/services/SearchServices/getSearchDataByQueryId?queryId=19&queryOwner=2`
- **Κρίσιμο Πεδίο**: `W001_P_FLD10` (Όνομα υπαλλήλου)
- **Κλειδί Συσχέτισης**: `W007_P_FLD21` (PKM/Αριθμός Πρωτοκόλλου)
- **Στήλη Excel**: "Ανάθεση σε"

## Δομή Δεδομένων

### API Response Fields (queryId=19)
```
W007_P_FLD21  = Αριθμός ΠΚΜ/Πρωτοκόλλου (κλειδί συσχέτισης)
W001_P_FLD10  = Υπάλληλος στον οποίο έχει χρεωθεί
W001_P_FLD1   = Case ID
DOCID         = Document ID
DESCRIPTION   = Περιγραφή υπόθεσης
```

### Charge Info Structure
Κάθε record εμπλουτίζεται με το πεδίο `_charge`:

```python
{
    'charged': True/False,         # Αν έχει χρεωθεί
    'employee': 'Όνομα Υπαλλήλου', # Υπάλληλος (αν χρεωμένη)
    'doc_id': '12345',             # Document ID
    'case_id': 'CASE123',          # Case ID
    'description': '...'            # Περιγραφή
}
```

## Χρήση

### 1. Βασική Ανάκτηση Χρεώσεων

```python
from session import PKMSession
from charges import fetch_charges

session = PKMSession(...)
session.login()

# Ανάκτηση χρεώσεων
charges_records, charges_by_pkm = fetch_charges(session)

print(f"Συνολικές χρεώσεις: {len(charges_records)}")
print(f"Χρεώσεις με PKM: {len(charges_by_pkm)}")
```

### 2. Εμπλουτισμός Incoming Records

```python
from charges import add_charge_info
from incoming import fetch_incoming_records, simplify_incoming_records

# Ανάκτηση εισερχόμενων
incoming_data = fetch_incoming_records(session, params)
records = simplify_incoming_records(incoming_data.get('data', []))

# Εμπλουτισμός με χρεώσεις
enriched = add_charge_info(records, charges_by_pkm)

# Έλεγχος χρέωσης
for rec in enriched:
    charge = rec.get('_charge', {})
    if charge.get('charged'):
        print(f"PKM {rec['protocol_number']}: {charge['employee']}")
    else:
        print(f"PKM {rec['protocol_number']}: Μη χρεωμένη")
```

### 3. Φιλτράρισμα και Στατιστικά

```python
from charges import (
    filter_charged, 
    filter_uncharged, 
    get_charge_statistics,
    print_charge_statistics
)

# Φιλτράρισμα
charged = filter_charged(enriched)
uncharged = filter_uncharged(enriched)

print(f"Χρεωμένες: {len(charged)}")
print(f"Μη χρεωμένες: {len(uncharged)}")

# Στατιστικά
stats = get_charge_statistics(enriched)
print(f"Ποσοστό χρέωσης: {stats['charged_percentage']:.1f}%")
print(f"Μοναδικοί υπάλληλοι: {stats['unique_employees']}")

# Εκτύπωση πλήρων στατιστικών
print_charge_statistics(enriched)
```

### 4. Ανάκτηση Πληροφορίας για Συγκεκριμένο Record

```python
from charges import get_charge_info

record = enriched[0]
charge_info = get_charge_info(record, charges_by_pkm)

if charge_info:
    print(f"PKM: {charge_info['pkm']}")
    print(f"Υπάλληλος: {charge_info['employee']}")
    print(f"Case ID: {charge_info['case_id']}")
```

## Ενσωμάτωση στο Excel

Το module **xls_export.py** έχει ενημερωθεί να περιλαμβάνει τη στήλη "Ανάθεση σε":

```python
from xls_export import build_requests_xls

# Δημιουργία Excel με χρεώσεις
xls_bytes = build_requests_xls(digest, scope='new')

# Ή αποθήκευση σε αρχείο
build_requests_xls(digest, scope='new', file_path='report.xlsx')
```

### Στήλες Excel (Νέα Δομή)

| Στήλη | Περιεχόμενο |
|-------|-------------|
| Δ/νση | Διεύθυνση υπηρεσίας |
| Αρ. Πρωτοκόλλου | Αριθμός πρωτοκόλλου (formatted) |
| Διαδικασία | Όνομα διαδικασίας |
| Συναλλασσόμενος | Αιτών |
| **Ανάθεση σε** | **Υπάλληλος (νέα στήλη)** |

## Αυτόματη Ενσωμάτωση

Η λειτουργικότητα ενσωματώνεται αυτόματα στο **daily_report.py**:

```python
from daily_report import build_daily_digest

# Το digest περιλαμβάνει αυτόματα τις χρεώσειςdigest = build_daily_digest()

# Τα incoming records έχουν πλέον _charge info
incoming = digest['incoming']
for rec in incoming['records']:
    charge = rec.get('_charge', {})
    print(f"{rec['protocol_number']}: {charge.get('employee', 'N/A')}")
```

## Δοκιμή

Για δοκιμή της λειτουργικότητας:

```bash
# Δοκιμή χρεώσεων
python test_charges.py

# Δημιουργία ημερήσιου report με χρεώσεις
python src/daily_report.py

# Αποστολή emails με χρεώσεις
python src/directory_emails.py
```

## Παράδειγμα Εξόδου

```
📊 ΣΤΑΤΙΣΤΙΚΑ ΧΡΕΩΣΕΩΝ
============================================================
Σύνολο αιτήσεων:      175
Χρεωμένες:            128 (73.1%)
Μη χρεωμένες:         47
Μοναδικοί υπάλληλοι:  15

Υπάλληλοι:
  • Γεωργίου Μαρία: 23 αιτήσεις
  • Παπαδόπουλος Ιωάννης: 18 αιτήσεις
  • Κωνσταντίνου Ελένη: 15 αιτήσεις
  ...
============================================================
```

## Αντιμετώπιση Προβλημάτων

### Πρόβλημα: Δεν βρίσκονται χρεώσεις

**Λύση**: Ελέγξτε ότι:
- Το queryId=19 είναι σωστό για το περιβάλλον σας
- Το session έχει τα σωστά δικαιώματα
- Το πεδίο W001_P_FLD10 περιέχει τον υπάλληλο

### Πρόβλημα: Δεν συσχετίζονται οι χρεώσεις

**Λύση**: Ελέγξτε ότι:
- Τα PKM/protocol_number ταιριάζουν
- Το πεδίο W007_P_FLD21 στις χρεώσεις αντιστοιχεί στο protocol_number των incoming

### Πρόβλημα: Κενή στήλη "Ανάθεση σε" στο Excel

**Λύση**: Βεβαιωθείτε ότι:
- Τα records έχουν εμπλουτιστεί με `add_charge_info()`
- Το `_charge` dictionary υπάρχει στα records
- Το `xls_export.py` έχει ενημερωθεί

## Τεχνικές Λεπτομέρειες

### Performance

- **Χρόνος ανάκτησης χρεώσεων**: ~1-2 δευτερόλεπτα
- **Χρόνος εμπλουτισμού**: O(n) όπου n = αριθμός incoming records
- **Memory footprint**: Minimal (mapping dictionary)

### Caching

Προς το παρόν δεν υπάρχει caching. Οι χρεώσεις ανακτώνται κάθε φορά. Για μελλοντική βελτίωση:

```python
# TODO: Προσθήκη caching για χρεώσεις
# Παρόμοιο με το procedures_cache.json
```

## API Reference

### Functions

#### `fetch_charges(session) -> Tuple[List[dict], Dict[str, dict]]`
Ανακτά χρεώσεις από το API.

**Returns**:
- `charges_records`: Λίστα με όλες τις χρεώσεις
- `charges_by_pkm`: Dictionary με mapping PKM -> charge

#### `add_charge_info(records, charges_by_pkm) -> List[dict]`
Εμπλουτίζει incoming records με charge info.

#### `get_employee_from_charge(charge) -> Optional[str]`
Εξάγει το όνομα υπαλλήλου από charge record.

#### `get_charge_info(record, charges_by_pkm) -> Optional[dict]`
Επιστρέφει charge info για συγκεκριμένο record.

#### `filter_charged(records) -> List[dict]`
Φιλτράρει χρεωμένα records.

#### `filter_uncharged(records) -> List[dict]`
Φιλτράρει μη χρεωμένα records.

#### `get_charge_statistics(records) -> dict`
Υπολογίζει στατιστικά χρεώσεων.

#### `print_charge_statistics(records) -> None`
Εκτυπώνει formatted στατιστικά.

## Σχετικά Αρχεία

- **Module**: [src/charges.py](../src/charges.py)
- **Tests**: [test_charges.py](../test_charges.py)
- **Excel Export**: [src/xls_export.py](../src/xls_export.py)
- **Integration**: [src/daily_report.py](../src/daily_report.py)

## Μελλοντικές Επεκτάσεις

1. **Caching**: Αποθήκευση χρεώσεων σε cache για ταχύτερη ανάκτηση
2. **Ιστορικό**: Παρακολούθηση αλλαγών χρεώσεων στο χρόνο
3. **Alerts**: Ειδοποιήσεις για μη χρεωμένες αιτήσεις
4. **Dashboard**: Οπτικοποίηση φόρτου εργασίας ανά υπάλληλο
5. **Export**: Επιπλέον export formats (CSV, JSON)
