# Chat Sessions Index
## Website-Monitor Project

**Index Last Updated:** 2026-03-11

---

## Active Sessions

### 🔵 [2026-03-11] Open Test Requests Tracker XLSX
**File:** `2026-03-11_open_test_requests_tracker_xlsx.md`  
**Status:** Completed  
**Topics:**
- Persistent XLS tracker για ανοικτές δοκιμαστικές
- Μη διαγραφή διεκπεραιωμένων rows
- Συμπλήρωση `Ημ/νία Κλεισίματος`
- Σταθερό export αρχείο αντί για timestamped

**Key Changes:**
- `src/xls_export.py` - merge current open + existing rows, close-date update
- `src/main.py` - fixed output path `data/outputs/Ανοικτές_δοκιμαστικές.xlsx`

**Discoveries:**
- Με timestamped output δεν μπορεί να διατηρηθεί ιστορικό εκκρεμών/διεκπεραιωμένων.
- Η ενιαία αποθήκευση σε σταθερό αρχείο επιτρέπει append νέων και marking κλεισίματος.

### 🔵 [2026-02-17] Case Inquiry & Charge Investigation
**File:** `2026-02-17_case_inquiry_and_charge_investigation.md`  
**Status:** Active Investigation  
**Topics:**
- Case inquiry tools (get_case_details.py, search_protocol.py)
- Protocol number vs Case ID distinction
- Charge source verification (queryId=3 USER_GROUP_ID_TO)
- HTML entity decoding for Greek text
- Department assignment tracking

**Key Scripts:**
- `get_case_details.py` - Query case from multiple sources
- `search_protocol.py` - Search by protocol number

**Discoveries:**
- 793923 is protocol number (not PKM)
- Department charges come from queryId=3
- HTML entities in DESCRIPTION need decoding

---

## Archived/Completed Sessions
*(None yet - sessions will be archived when no longer under active development)*

---

## Quick Navigation

### By Topic

#### 📋 Case Management
- [2026-02-17] Case Inquiry & Charge Investigation

#### 💰 Charge/Billing System
- [2026-02-17] Case Inquiry & Charge Investigation (charge sources)

#### 📊 Data Analysis & Queries
- [2026-02-17] Case Inquiry & Charge Investigation (queryId reference)

#### 🛠️ Tool Development
- [2026-02-17] Case Inquiry & Charge Investigation (scripts created)

#### 🐛 Debugging & Fixes
- [2026-02-17] Case Inquiry & Charge Investigation (HTML decoding issue)
- [2026-03-11] Open Test Requests Tracker XLSX (persistent close-date tracking)

---

## Scripts Created by Session

| Script | Session | Purpose |
|--------|---------|---------|
| `get_case_details.py` | 2026-02-17 | Query case from multiple sources |
| `search_protocol.py` | 2026-02-17 | Search by protocol number |
| `debug_793923_full.py` | 2026-02-17 | Debug - extract all fields |
| `deep_search_793923.py` | 2026-02-17 | Debug - field-by-field search |

---

## Code Modifications by Session

| File | Session | Change |
|------|---------|--------|
| `src/xls_export.py` | 2026-03-11 | Persistent open-test tracker and close-date updates |
| `src/main.py` | 2026-03-11 | Stable output filename for open-test tracker export |

---

## Important Discoveries by Topic

### Protocol vs Case ID
- **Session:** 2026-02-17
- **Finding:** Two distinct ID systems in use
  - Protocol: `793923` (in DESCRIPTION)
  - Case/PKM: `105139` (W007_P_FLD21 in queryId=6)

### QueryId Mapping
- **Session:** 2026-02-17
- **Table:** See session notes for full reference
- **Key:** queryId=3 (Routing) has best charge coverage

### HTML Encoding Issue
- **Session:** 2026-02-17
- **Problem:** `&Alpha;&#943;&tau;&eta;&mu;&alpha;` = `Αίτημα`
- **Solution:** `html.unescape()`

---

## Related External Documentation

These are maintained separately and referenced from sessions:

- `docs/API_COMPLETE_GUIDE.md` - API endpoints
- `docs/API_QUICK_REFERENCE.md` - Common queries
- `docs/FASTAPI_INTEGRATION.md` - Backend integration
- `docs/DIRECTORIES_MANAGEMENT.md` - Directory system

---

## How to Use This Index

1. **Starting new work?** → Check "Quick Navigation" → find relevant session
2. **Debugging?" → Look up script or file in tables above
3. **Need full details?** → Click session link and read full notes
4. **Adding new session?** → Update this index + create new dated file

---

## Policy

**Every chat session must create notes** in `docs/chats_notes/POLICY.md`

See `POLICY.md` for complete guidelines.

---

*Maintained by: AI Agents & Project Contributors*  
*Last Updated: 2026-02-17*
