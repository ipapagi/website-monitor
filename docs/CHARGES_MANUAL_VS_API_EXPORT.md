# 🔄 EXCEL EXPORT: Manual vs API Endpoint

## 🎯 Σύγκριση - Που Ενημερώνονται τα Αρχεία

| ΜΕΘΟΔΟΣ | Manual Command | API Endpoint |
|---------|--------|---------|
| **Εντολή** | `python -m src.main --export-incoming-xls` | `GET /sede/export/xls?scope=all` |
| **Αρχείο Αποθήκευση** | ✅ **ΝΑΙ** - Δημιουργεί/Ενημερώνει αρχείο | ❌ **ΟΧΙ** - In-memory, δεν αποθηκεύει |
| **Filename** | `incoming_new_YYYY-MM-DD.xlsx` ή `Διαδικασίες - εισερχόμενες αιτήσεις.xlsx` | Το ίδιο, αλλά δεν αποθηκεύεται |
| **Φάκελος** | `data/` |Κανένας - Επιστρέφεται ως download |
| **Πού Βρίσκεται** | Δίσκος (persistent) | RAM (volatile - χάνεται όταν κλείνει browser) |
| **Χρήση** | Automation, scripts, scheduled tasks | Web UI, API clients (curl, Postman, browser) |

---

## 📍 MANUAL COMMAND FLOW

### Εντολή:
```bash
python -m src.main --export-incoming-xls
```

### Κωδικάς:
**Αρχείο**: [src/main.py](src/main.py)  
**Γραμμές**: 216-235

```python
if args.export_incoming_xls or args.export_incoming_xls_all:
    from services.report_service import load_digest
    from xls_export import build_requests_xls
    
    digest = load_digest()
    date_str = (digest.get('incoming', {}) or {}).get('date') or datetime.now().strftime('%Y-%m-%d')
    out_dir = os.path.join(get_project_root(), 'data')
    os.makedirs(out_dir, exist_ok=True)
    
    scope = 'all' if args.export_incoming_xls_all else 'new'
    
    if scope == 'all':
        out_path = os.path.join(out_dir, "Διαδικασίες - εισερχόμενες αιτήσεις.xlsx")
    else:
        out_path = os.path.join(out_dir, f"incoming_{scope}_{date_str}.xlsx")
    
    # 🔴 ΑΠΟΘΗΚΕΥΣΗ ΣΤΟΝ ΔΙΣΚΟ
    build_requests_xls(digest, scope=scope, file_path=out_path)  # ← file_path=""
    print(f"✅ Δημιουργήθηκε XLS ({scope}): {out_path}")
```

### Αποτέλεσμα:

```
CLI → load_digest() → build_requests_xls(..., file_path="...") 
   → xls_export.build_requests_xls() {
       # Αν file_path υπάρχει:
       if file_path:
           wb.save(file_path)  # ← Αποθηκεύει
           return file_path    # ← Επιστρέφει path
   }
   → 📁 data/Διαδικασίες - εισερχόμενες αιτήσεις.xlsx ✅
```

**Αποτέλεσμα**: Αρχείο δημιουργείται στο `data/` και παραμένει εκεί.

---

## 🌐 API ENDPOINT FLOW

### Αίτημα HTTP:
```
GET /sede/export/xls?scope=all HTTP/1.1
Host: localhost:8000
```

### Κώδικας:
**Αρχείο**: [src/webapi/routes_export.py](src/webapi/routes_export.py)  
**Γραμμές**: 43-65

```python
@router.get("/sede/export/xls", tags=["Export"])
async def export_xls(scope: str = Query(default="new", pattern="^(new|all)$")):
    """Επιστρέφει Excel (.xlsx) με δύο φύλλα: Δοκιμαστικές και Πραγματικές."""
    try:
        from urllib.parse import quote
        
        report = load_digest()  # ← Φορτώνει digest
        incoming = report.get("incoming", {})
        date_str = incoming.get("date") or report.get("generated_at", "")[:10]

        # 🔵 ΔΕΝ ΑΠΟΘΗΚΕΥΕΙ ΣΤΟΝ ΔΙΣΚΟ
        xls_bytes = build_requests_xls(report, scope=scope)  # ← file_path=None (default)
        
        filename = "Διαδικασίες - εισερχόμενες αιτήσεις.xlsx" if scope == "all" else f"incoming_{scope}_{date_str}.xlsx"
        filename_encoded = quote(filename, safe="")
        
        # Επιστρέφει bytes (in-memory)
        return StreamingResponse(
            iter([xls_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename*=UTF-8\'\'{filename_encoded}'},
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
```

### Αποτέλεσμα:

```
GET /sede/export/xls?scope=all 
   → load_digest() → build_requests_xls(..., file_path=None) 
   → xls_export.build_requests_xls() {
       # Αν file_path είναι None:
       buf = io.BytesIO()
       wb.save(buf)     # ← Σε RAM (όχι δίσκο)
       buf.seek(0)
       return buf       # ← Επιστρέφει bytes
   }
   → 📥 Download (χρήστης αποθηκεύει ή χάνεται)
```

**Αποτέλεσμα**: Αρχείο δεν αποθηκεύεται στο δίσκο - ο χρήστης λαμβάνει το αρχείο ως download.

---

## 🔍 KEY DIFFERENCE: `file_path` Parameter

### Στο xls_export.py

**Αρχείο**: [src/xls_export.py](src/xls_export.py)  
**Γραμμές**: 112-152

```python
def build_requests_xls(digest: Dict, scope: str = "new", file_path: str | None = None) -> bytes | str:
    """Build an XLSX with two sheets (test, real).

    Args:
        digest: The digest dict
        scope: "new" or "all"
        file_path: 
            - If None → Returns bytes (for API)
            - If str → Saves to disk and returns path (for CLI)
    """
    # ... sheet creation code ...
    
    if file_path:
        # 🔴 MANUAL COMMAND PATH
        wb.save(file_path)  # ← Saves to disk
        return file_path    # ← Returns path string
    
    # 🔵 API ENDPOINT PATH
    buf = io.BytesIO()
    wb.save(buf)  # ← Creates in-memory buffer
    buf.seek(0)
    return buf.getvalue()  # ← Returns bytes
```

---

## 📊 EXECUTION TABLE

### Manual Command: `python -m src.main --export-incoming-xls-all`

```
Step                        | What Happens
═══════════════════════════════════════════════════════════════
1. Parse arguments          | scope = 'all'
2. Load digest              | From services.report_service
3. build_requests_xls(      | file_path = "data/Διαδικασίες -..."
   file_path="...")         |
4. Create workbook          | 2 sheets (test, real)
5. Add data from digest     | Include _charge field
6. wb.save(file_path)       | ✅ Writes to data/Διαδικασίες -...xlsx
7. Return file_path         | Print success message
8. File exists on disk      | ✅ Persistent - survives reboot
```

### API Endpoint: `GET /sede/export/xls?scope=all`

```
Step                        | What Happens
═══════════════════════════════════════════════════════════════
1. Client makes GET request | scope=all parameter
2. FastAPI routes to        | export_xls() function
3. Load digest              | From services.report_service
4. build_requests_xls(      | file_path = None (default)
   file_path=None)          |
5. Create workbook          | 2 sheets (test, real)
6. Add data from digest     | Include _charge field
7. buf = io.BytesIO()       | Create in-memory buffer
8. wb.save(buf)             | ✅ Writes to RAM
9. buf.seek(0)              | Reset buffer position
10. Return StreamingResponse | 📥 Send bytes to client
11. Client downloads file   | Saves or discards (user choice)
12. RAM freed after response | ❌ Not persistent
```

---

## 💾 WHERE FILES ARE STORED

### Manual Command - Files Saved to Disk

```
project-root/
│
data/
├── 📊 incoming_new_2026-02-16.xlsx          [Manual: scope=new]
├── 📊 incoming_all_2026-02-16.xlsx          [Manual: scope=all]
├── 📊 Διαδικασίες - εισερχόμενες αιτήσεις.xlsx  [Manual: scope=all, fixed name]
│
├── incoming_requests/
│   └── 2026-02-16.json                      [JSON snapshot with _charge]
```

### API Endpoint - Files NOT Saved

```
No files created on disk.
Only bytes sent to client's browser/HTTP client.
```

---

## 🌍 CLIENT PERSPECTIVE

### Manual Command

```bash
$ python -m src.main --export-incoming-xls-all
✅ Δημιουργήθηκε XLS (all): data/Διαδικασίες - εισερχόμενες αιτήσεις.xlsx

# Check if file exists
$ ls -la data/*.xlsx
-rw-r--r--  1 user  staff  150K Feb 16 12:34 data/Διαδικασίες - εισερχόμενες αιτήσεις.xlsx

# ✅ File is persistent on disk
```

### API Endpoint

```
Browser: http://localhost:8000/sede/export/xls?scope=all
   ↓
Server processes request
   ↓
Browser: [Download Dialog]
   ↓
User: "Save" or "Cancel"
   ↓
If Save: File saved to user's Downloads folder
If Cancel: Bytes discarded from RAM
   
✅ File NOT on server disk
```

---

## 📝 SUMMARY TABLE

| Aspect | Manual | API |
|--------|--------|-----|
| **Διατήρηση** | Μόνιμο (δίσκος) | Προσωρινό (RAM) |
| **Ενημέρωση** | Κάθε φορά που τρέχει | Κάθε φορά που καλείται |
| **Χρησιμοποιητής** | Developer/Automation | Web User/API Client |
| **Έλεγχος** | `ls -la data/*.xlsx` | Browser history |
| **Ιστορικό** | Αθροίζεται (παλιά αρχεία μένουν) | Όχι (χάνεται πάντα) |
| **Χρησιμότητα** | Αρχειοθέτηση, logging, scripts | On-demand downloads |

---

## ❓ ΑΠΑΝΤΗΣΗ ΣΤΗΝ ΕΡΩΤΗΣΗ

> Δηλαδή το Διαδικασίες - εισερχόμενες αιτήσεις.xlsx ενημερώνεται και όταν καλείται το endpoint?

**ΑΠΑΝΤΗΣΗ:**

- ✅ **Ενημερώνεται** όταν τρέχει: `python -m src.main --export-incoming-xls-all`
  - Το αρχείο δημιουργείται ή αντικαθίσταται στο `data/`
  
- ❌ **ΔΕΝ ενημερώνεται** όταν καλείται: `GET /sede/export/xls?scope=all`
  - Δεν δημιουργείται αρχείο στο δίσκο
  - Επιστρέφονται bytes στον client ως download
  - Ο χρήστης μπορεί να αποθηκεύσει το αρχείο όπου θέλει ή να το σβήσει

### Αν θέλατε Στόχο: Auto-Save από API

Θα περάσαμε `file_path` στο endpoint, όπως κάνει ο manual command:

```python
# ❌ ΑΥΤΟ ΔΕΝ ΓΙΝΕΤΑΙ ΣΤΟ API
# @router.get("/sede/export/xls")
# async def export_xls(scope: str):
#     xls_bytes = build_requests_xls(report, scope=scope, file_path="data/auto-save.xlsx")

# Αντί αυτού, τα bytes επιστρέφονται στον client
```

---

## 🎯 ΧΡΗΣΗΣ ΠΕΡΙΠΤΩΣΗΣ

### Μήνα 1: Automation
```bash
# Scheduled task (cron) - τρέχει κάθε μέρα 14:00
0 14 * * * cd /path/to/project && python -m src.main --export-incoming-xls-all

# ✅ Αρχείο αποθηκεύεται: data/Διαδικασίες - εισερχόμενες αιτήσεις.xlsx
# ✅ Παλιό αρχείο αντικαθίστανται
# ✅ Ιστορικό διατηρείται (κάθε αρχείο που αποθηκεύσατε αποθηκεύεται ξεχωριστά)
```

### Περίπτωση 2: Web UI
```
User opens browser: http://localhost:8000/sede/export/xls?scope=all
   ↓
Browser shows: "Download incoming_all_2026-02-16.xlsx?"
   ↓
User clicks: "Save"
   ↓
File saved to: ~/Downloads/incoming_all_2026-02-16.xlsx
   ↓
❌ NOT saved on server
```

---

**📅 Δημιουργία:** 16 Φεβρουαρίου 2026  
**🔗 Σχετικά αρχεία:** CHARGES_EXCEL_FILES.md, CHARGES_DETAILED_FLOW.md
