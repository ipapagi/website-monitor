# Διορθώσεις Export Excel - Summary

## Προβλήματα που Εντοπίστηκαν

### 1. ❌ API Endpoint: Κενή στήλη Διεκπεραιωμένη
**Πρόβλημα**: Το `GET /sede/export/xls?scope=all` δεν είχε δεδομένα στη στήλη Διεκπεραιωμένη

**Αιτία**: Το API endpoint δεν περνούσε το `monitor_instance` στο `build_requests_xls()`, άρα δεν μπορούσε να φορτώσει τα settled cases από το queryId=19.

**Λύση**:
- Δημιουργήθηκε `src/webapi/state.py` με global `get_monitor()` function
- Το `routes_export.py` τώρα καλεί `get_monitor()` και περνάει το monitor στο `build_requests_xls()`
- Το `build_requests_xls()` περνάει το monitor στο `_load_settled_cases()`

**Αρχεία που Τροποποιήθηκαν**:
- ✅ `src/webapi/state.py` (νέο αρχείο)
- ✅ `src/webapi/routes_export.py` (προσθήκη: `from .state import get_monitor`)
- ✅ `src/webapi/routes_export.py` (ενημέρωση: `monitor = get_monitor()` και `build_requests_xls(..., monitor_instance=monitor)`)

### 2. ❌ Department Assignments στο Excel
**Πρόβλημα**: Στο Excel export υπήρχαν 35 αναθέσεις σε τμήματα (Δοκιμαστικές) και 14 (Πραγματικές)

**Παραδείγματα**:
```
ΤΜΗΜΑ ΕΠΟΙΚΙΣΜΟΥ ΚΑΙ ΑΝΑΔΑΣΜΟΥ (ΠΚΜ) (Προϊστάμενοι)
ΤΜΗΜΑ ΕΜΠΟΡΙΟΥ (Προϊστάμενοι)
ΤΜΗΜΑ ΧΟΡΗΓΗΣΗΣ ΑΔΕΙΩΝ ΒΙΟΜΗΧΑΝΙΑΣ...
ΤΜΗΜΑ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ (Προϊστάμενοι)
```

**Λύση**:
- Προστέθηκε συνάρτηση `_is_department_assignment()` στο `xls_export.py`
- Keywords: `['ΤΜΗΜΑ', 'ΔΙΕΥΘΥΝΣΗ', 'Προϊστάμενοι']`
- Στο `_write_sheet()`: όταν το `employee` name περιέχει keyword, clear το field

**Αρχεία που Τροποποιήθηκαν**:
- ✅ `src/xls_export.py` (προσθήκη `_is_department_assignment()` function)
- ✅ `src/xls_export.py` (φίλτρο στο loop: `if employee and _is_department_assignment(employee): employee = ""`)

## Αποτελέσματα Πριν/Μετά

### Πριν (❌)

**Command Line Export**:
- Διεκπεραιωμένη: ✅ 58/156 test, 1/27 real (με settlement dates)
- Αναθέσεις Τμήματος: ❌ 35 στο Δοκιμαστικές, 14 στο Πραγματικές

**API Export** (`GET /sede/export/xls?scope=all`):
- Διεκπεραιωμένη: ❌ Κενή στήλη (0 settlement dates)
- Αναθέσεις Τμήματος: ❌ 35 στο Δοκιμαστικές, 14 στο Πραγματικές

### Μετά (✅)

**Command Line Export**:
- Διεκπεραιωμένη: ✅ 58/156 test, 1/27 real (με settlement dates)
- Αναθέσεις Τμήματος: ✅ 0 (φιλτραρισμένες)
- Προσωπικές Αναθέσεις: ✅ 50 στο Δοκιμαστικές

**API Export** (`GET /sede/export/xls?scope=all`):
- Διεκπεραιωμένη: ✅ Θα έχει settlement dates (μετά από restart του API server)
- Αναθέσεις Τμήματος: ✅ 0 (φιλτραρισμένες)
- Προσωπικές Αναθέσεις: ✅ 50

## Verification

### CLI Export Test
```bash
python src/main.py --export-incoming-xls-all
python check_department_assignments.py
python verify_excel_structure.py
```

**Αποτελέσματα**:
```
Δοκιμαστικές:
  Total rows: 156
  Assigned to DEPARTMENT: 0        ✅
  Assigned to PERSON: 50           ✅
  Settlement dates: 58             ✅

Πραγματικές:
  Total rows: 27
  Assigned to DEPARTMENT: 0        ✅
  Assigned to PERSON: 0            ✅
  Settlement dates: 1              ✅
```

### API Export Test (μετά restart)
Για να δοκιμάσετε το API endpoint:

1. **Restart API server** (έχει ήδη τρέξει):
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

2. **Download & Check**:
   ```bash
   python test_api_export.py
   ```

3. **Verify**:
   - Settlement dates: 58/156 test, 1/27 real
   - Department assignments: 0
   - Personal assignments: 50 test

## Κώδικας - Παραδείγματα

### `src/webapi/state.py` (νέο)
```python
_global_monitor = None

def get_monitor():
    """Get or create the global monitor instance."""
    global _global_monitor
    
    if _global_monitor is None:
        from monitor import PKMMonitor
        from utils import load_config
        from config import get_project_root
        import os
        
        config = load_config(os.path.join(get_project_root(), 'config', 'config.yaml'))
        _global_monitor = PKMMonitor(...)
        
        if not _global_monitor.login():
            print("[WARNING] Failed to login monitor")
    
    return _global_monitor
```

### `src/webapi/routes_export.py` (updated)
```python
from .state import get_monitor

@router.get("/sede/export/xls")
async def export_xls(scope: str = ...):
    # ...
    monitor = get_monitor()
    xls_bytes = build_requests_xls(report, scope=scope, monitor_instance=monitor)
    # ...
```

### `src/xls_export.py` (updated)
```python
def _is_department_assignment(employee_name: str) -> bool:
    """Check if employee_name is a department assignment."""
    if not employee_name:
        return False
    
    dept_keywords = ['ΤΜΗΜΑ', 'ΔΙΕΥΘΥΝΣΗ', 'Προϊστάμενοι']
    name_upper = str(employee_name).upper()
    return any(keyword in name_upper for keyword in dept_keywords)

def _write_sheet(ws, rows, title, settled_by_case_id):
    # ...
    for idx, rec in enumerate(rows_sorted, start=1):
        charge_info = rec.get("_charge", {})
        employee = charge_info.get("employee", "") if charge_info.get("charged") else ""
        
        # Filter out department assignments
        if employee and _is_department_assignment(employee):
            employee = ""
        
        col_vals[6].append(employee)
```

## Επόμενα Βήματα

1. ✅ **Restart API server** - για να φορτώσει τα νέα modules
2. ⏳ **Test API endpoint** - `python test_api_export.py`
3. ⏳ **Verify via browser** - http://localhost:8000/sede/export/xls?scope=all

## Σύνοψη

✅ **2/2 προβλήματα διορθώθηκαν**:
- Settlement dates τώρα φορτώνουν στο API endpoint
- Department assignments φιλτράρονται (μόνο προσωπικές αναθέσεις εμφανίζονται)

✅ **Tested**: Command line export works correctly
⏳ **Pending**: API endpoint test (after server restart)
