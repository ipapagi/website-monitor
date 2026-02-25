"""
ΑΝΑΛΥΤΙΚΗ ΔΙΑΔΡΟΜΗ ΧΡΕΩΣΕΩΝ - Όλα τα Βήματα

Αυτό το documentation εξηγεί ΑΚΡΙΒΩΣ που μπαίνουν οι χρεώσεις και ποια αρχεία
τροποποιούνται σε κάθε στάδιο του workflow.
"""

# ════════════════════════════════════════════════════════════════════════════════
# ΒΗΜΑ 1: LOGIN - Δημιουργία Session
# ════════════════════════════════════════════════════════════════════════════════
ΑΡΧΕΙΟ: src/session.py
ΚΛΑΣΗ: PKMSession
ΣΥΝΑΡΤΗΣΗ: login()

ΤΥΠΙΚΗ ΕΚΤΕΛΕΣΗ:
  monitor = PKMMonitor(..., username="supervisor", password="xxx")
  monitor.login()
  ✅ self.logged_in = True
  ✅ self.session = requests.Session() με cookies
  
ΑΠΟΤΕΛΕΣΜΑ:
  - Authenticated session για τα υπόλοιπα API calls
  - Χρησιμοποιείται στο Βήμα 2 και 5


# ════════════════════════════════════════════════════════════════════════════════
# ΒΗΜΑ 2: FETCH INCOMING REQUESTS
# ════════════════════════════════════════════════════════════════════════════════
ΑΡΧΕΙΟ: src/daily_report.py
ΣΥΝΑΡΤΗΣΗ: _prepare_incoming(monitor, config)

Κώδικας:
  incoming_params = config.get("incoming_api_params", INCOMING_DEFAULT_PARAMS).copy()
  data = fetch_incoming_records(monitor, incoming_params)
  
  ↓ ΚΑΛΕΙ: src/incoming.py::fetch_incoming_records()
  
  ΑΡΧΕΙΟ: src/incoming.py
  ΣΥΝΑΡΤΗΣΗ: fetch_incoming_records(monitor, incoming_params)
  
  API CALL:
    GET /services/SearchServices/getSearchDataByQueryId
        ?queryId=6          ← INCOMING REQUESTS
        &queryOwner=2
        &isCase=false
        &stateId=welcomeGrid-45_dashboard0
        &limit=100
  
  ΑΠΟΤΕΛΕΣΜΑ:
    ✅ data = {
        'success': True,
        'data': [177 records με fields: DOCID, W007_P_FLD21, DESCRIPTION, etc...]
      }
    ✅ data['data'] αποθηκεύεται στη μνήμη


# ════════════════════════════════════════════════════════════════════════════════
# ΒΗΜΑ 3: SIMPLIFY RECORDS
# ════════════════════════════════════════════════════════════════════════════════
ΑΡΧΕΙΟ: src/daily_report.py
ΕΠΙ ΣΤΡΟΦΗ ΣΤΟ: src/incoming.py::simplify_incoming_records()

Κώδικας:
  records = simplify_incoming_records(data.get("data", []))
  
  ΤΙ ΚΑΝΕΙ:
    - Εξάγει τα βασικά πεδία από τα RAW API records
    - W007_P_FLD21 → case_id
    - W007_P_FLD3 → submitted_at
    - W007_P_FLD13 → party
    - DOCID → doc_id
  
  ΑΠΟΤΕΛΕΣΜΑ:
    ✅ 177 simplified records στη μνήμη με fields:
        {
          'case_id': '106653',        ← PKM (ΤΟ ΚΛΕΙΔΙ ΣΥΣΧΕΤΙΣΗΣ!)
          'protocol_number': '',
          'protocol_date': '',
          'submitted_at': '2026-02-10 10:15:30',
          'party': 'ΚΗΠΟΣ-258403847',
          'doc_id': '44160',
          'procedure': None,          ← Θα συμπληρωθει αργότερα
          'directory': None           ← Θα συμπληρωθει αργότερα
        }


# ════════════════════════════════════════════════════════════════════════════════
# ΒΗΜΑ 4: ENRICH RECORD DETAILS
# ════════════════════════════════════════════════════════════════════════════════
ΑΡΧΕΙΟ: src/daily_report.py
Κώδικας:
  to_enrich = [r for r in records if not r.get('procedure') or not r.get('directory')]
  if to_enrich:
      enrich_record_details(monitor, to_enrich)
  
  ↓ ΚΑΛΕΙ: src/api.py::enrich_record_details()
  
  ΤΙ ΚΑΝΕΙ:
    - Κάνει API calls για κάθε record που λείπει procedure/directory
    - Ενημερώνει τα records στη μνήμη με procedure και directory
  
  ΑΠΟΤΕΛΕΣΜΑ:
    ✅ 177 records τώρα έχουν:
        {
          ...προηγούμενα fields...
          'procedure': 'ΔΑΟ-ΦΖΠ-25 Χορηγούμενα πτυχία...',
          'directory': 'ΓΕΝΙΚΗ ΔΙΕΥΘΥΝΣΗ ΑΓΡΟΤΙΚΗΣ...'
        }


# ════════════════════════════════════════════════════════════════════════════════
# ΒΗΜΑ 5A: FETCH CHARGES ← 🔴 ΝΕΟ ΒΗΜΑ!
# ════════════════════════════════════════════════════════════════════════════════
ΑΡΧΕΙΟ: src/daily_report.py
ΝΕΟΣ ΚΩΔΙΚΑΣ (προστέθηκε στο _prepare_incoming):

    # Ανάκτηση χρεώσεων και εμπλουτισμός records
    try:
        from charges import fetch_charges, add_charge_info
        print("📋 Ανάκτηση χρεώσεων υπαλλήλων...")
        charges_records, charges_by_pkm = fetch_charges(monitor)
        print(f"   Βρέθηκαν {len(charges_records)} χρεώσεις")
        records = add_charge_info(records, charges_by_pkm)
        print(f"   ✅ Εμπλουτισμός με χρεώσεις ολοκληρώθηκε")
    except Exception as exc:
        print(f"   ⚠️  Αποτυχία ανάκτησης χρεώσεων: {exc}")

↓ ΚΑΛΕΙ: src/charges.py::fetch_charges()

ΑΡΧΕΙΟ: src/charges.py (ΝΕΟ ΑΡΧΕΙΟ!)
ΣΥΝΑΡΤΗΣΗ: fetch_charges(session)

API CALL:
  GET /services/SearchServices/getSearchDataByQueryId
      ?queryId=19         ← SETTLED/CHARGED CASES
      &queryOwner=2
      &isCase=false
      &stateId=welcomeGrid-45_dashboard0
      &limit=100

ΑΠΟΤΕΛΕΣΜΑ:
  ✅ charges_records = [55 records με fields: 
      DOCID, W007_P_FLD21, W001_P_FLD10, DESCRIPTION, etc
    ]

↓ ΜΕΣΩ: src/charges.py::_extract_pkm_from_description()

ΤΙ ΚΑΝΕΙ:
  - Διαβάζει κάθε DESCRIPTION: "Αίτημα 2026/106653 ΚΗΠΟΣ-258403847"
  - Εξάγει το PKM: "106653" με regex
  - Δημιουργεί mapping:
      charges_by_pkm = {
        '106653': {DOCID: 44066, W001_P_FLD10: 'ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ', ...},
        '105673': {DOCID: 44067, W001_P_FLD10: 'ΓΑΛΟΥΠΗ ΕΥΑΓΓΕΛΙΑ', ...},
        ...
      }

ΑΠΟΤΕΛΕΣΜΑ:
  ✅ charges_by_pkm dict με 55 entries
  ✅ Κλειδί = PKM (case_id), Τιμή = charge record


# ════════════════════════════════════════════════════════════════════════════════
# ΒΗΜΑ 5B: ADD CHARGE INFO ← 🔴 ΣΗΜΑΝΤΙΚΟ: ΕΔΩ ΜΠΑΙΝΟΥΝ ΟΙ ΧΡΕΩΣΕΙΣ!
# ════════════════════════════════════════════════════════════════════════════════
ΑΡΧΕΙΟ: src/daily_report.py
Κώδικας:
  records = add_charge_info(records, charges_by_pkm)

↓ ΚΑΛΕΙ: src/charges.py::add_charge_info()

ΤΙ ΚΑΝΕΙ - ΛΕΙΤΟΥΡΓΙΑ ΚΑΤΑ RECORD:
  for rec in incoming_records:  # 177 records
      enriched_rec = rec.copy()
      
      # Ανάκτηση PKM
      pkm = str(rec.get('case_id', '')).strip()  # π.χ. '106653'
      
      # Αναζήτηση στο charges_by_pkm
      if pkm in charges_by_pkm:
          charge = charges_by_pkm[pkm]
          employee = get_employee_from_charge(charge)
          
          # 🔴 ΠΡΟΣΘΗΚΗ _charge FIELD
          enriched_rec['_charge'] = {
              'charged': True,
              'employee': 'ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ',  ← ΑΠΟ W001_P_FLD10
              'doc_id': charge.get('DOCID'),
              'case_id': charge.get('W001_P_FLD1'),
              'description': charge.get('DESCRIPTION')
          }
      else:
          # 🔴 ΑΝ ΔΕΝ ΒΡΕΘΕΙ - ΑΔΕΙΟ _charge
          enriched_rec['_charge'] = {
              'charged': False,
              'employee': None,
              ...
          }
      
      enriched.append(enriched_rec)

ΑΠΟΤΕΛΕΣΜΑ:
  ✅ 177 records ΣΤΗΝ ΜΝΗΜΗ με νέο field '_charge':
      {
        'case_id': '106653',
        'procedure': 'ΔΑΟ-ΦΖΠ-32',
        'directory': 'ΓΕΝ. ΔΙΕ. ΑΓΡΟΤΙΚΗΣ...',
        'party': 'ΚΗΠΟΣ-258403847',
        '_charge': {
          'charged': True,
          'employee': 'ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ'  ← 🔴 ΤΟ ΚΡΙΣΙΜΟ ΠΕΔΙΟ!
        }
      }


# ════════════════════════════════════════════════════════════════════════════════
# ΒΗΜΑ 6: COMPARE & CLASSIFY
# ════════════════════════════════════════════════════════════════════════════════
ΑΡΧΕΙΟ: src/daily_report.py
Κώδικας:
  changes = compare_incoming_records(records, prev_snap)
  real_new, test_new = classify_records(changes.get("new", []))

ΤΙ ΚΑΝΕΙ:
  - Συγκρίνει με το προηγούμενο snapshot
  - Εντοπίζει νέα, αφαιρεθέντα, τροποποιημένα records
  - Τα classified records ΚΡΑΤΟΥΝ το _charge field!

ΑΠΟΤΕΛΕΣΜΑ:
  ✅ real_new = [νέα records με _charge]
  ✅ test_new = [test records με _charge]


# ════════════════════════════════════════════════════════════════════════════════
# ΒΗΜΑ 7: SAVE SNAPSHOT ← 🔴 ΑΠΟΘΗΚΕΥΕΤΑΙ ΣΤΟ ΑΡΧΕΙΟ!
# ════════════════════════════════════════════════════════════════════════════════
ΑΡΧΕΙΟ: src/incoming.py
ΣΥΝΑΡΤΗΣΗ: save_incoming_snapshot(date_str, records)

Κώδικας:
  payload = {'date': date_str, 'count': len(records), 'records': records}
  with open(get_incoming_snapshot_path(date_str), 'w', encoding='utf-8') as f:
      json.dump(payload, f, ensure_ascii=False, indent=2)

ΑΠΟΤΕΛΕΣΜΑ:
  ✅ Αρχείο: data/incoming_requests/2026-02-16.json
  ✅ Περιέχει 177 records με _charge field

ΠΑΡΑΔΕΙΓΜΑ ΠΕΡΙΕΧΟΜΕΝΟΥ:
  {
    "date": "2026-02-16",
    "count": 177,
    "records": [
      {
        "case_id": "106653",
        "procedure": "ΔΑΟ-ΦΖΠ-32 ...",
        "directory": "ΓΕΝ. ΔΙΕ. ΑΓΡΟΤΙΚΗΣ ...",
        "party": "ΚΗΠΟΣ-258403847",
        "_charge": {
          "charged": true,
          "employee": "ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ"
        }
      },
      ...
    ]
  }


# ════════════════════════════════════════════════════════════════════════════════
# ΒΗΜΑ 8: BUILD DIGEST
# ════════════════════════════════════════════════════════════════════════════════
ΑΡΧΕΙΟ: src/daily_report.py
ΣΥΝΑΡΤΗΣΗ: build_daily_digest()

Κώδικας:
  digest = {
      "generated_at": "16/02/2026 10:21:45",
      "incoming": {
          "date": "2026-02-16",
          "records": records,         ← 177 records με _charge!
          "real_new": real_new,       ← με _charge
          "test_new": test_new,       ← με _charge
          ...
      },
      ...
  }

ΑΠΟΤΕΛΕΣΜΑ:
  ✅ digest dict με incoming.records που έχουν _charge field


# ════════════════════════════════════════════════════════════════════════════════
# ΒΗΜΑ 9: EXPORT TO EXCEL ← 🔴 ΕΔΩΞ ΕΜΦΑΝΙΖΕΤΑΙ ΣΤΟ EXCEL!
# ════════════════════════════════════════════════════════════════════════════════
ΑΡΧΕΙΟ: src/xls_export.py
ΣΥΝΑΡΤΗΣΗ: build_requests_xls(digest, scope='all', file_path='report.xlsx')

Κώδικας:
  incoming = digest.get("incoming", {})
  records = incoming.get("records", [])  ← 177 records με _charge
  
  ↓ ΚΑΛΕΙ: _write_sheet(ws, records, title)
  
  def _write_sheet(ws, rows, title):
      headers = ["Δ/νση", "Αρ. Πρωτοκόλλου", "Διαδικασία", 
                 "Συναλλασσόμενος", "Ανάθεση σε"]  ← 🔴 ΝΕΑ ΣΤΗΛΗ!
      
      for rec in rows:
          # Στήλη 5: Ανάθεση σε
          charge_info = rec.get("_charge", {})
          employee = charge_info.get("employee", "") if charge_info.get("charged") else ""
          
          ws.cell(row=r, column=5, value=employee)  ← 🔴 ΕΔΩΞ ΕΜΦΑΝΙΖΕΤΑΙ!

ΑΠΟΤΕΛΕΣΜΑ:
  ✅ Excel file: data/outputs/reports/2026-02-16_XXXXXX.xlsx
  ✅ 5 στήλες:
      1. Δ/νση
      2. Αρ. Πρωτοκόλλου
      3. Διαδικασία
      4. Συναλλασσόμενος
      5. Ανάθεση σε ← 'ΑΝΤΩΝΙΑΔΗΣ ΠΡΟΚΟΠΙΟΣ' ή κενό


# ════════════════════════════════════════════════════════════════════════════════
# ΣΧΕΣΗ ΑΡΧΕΙΩΝ - ΠΟΙΑ ΑΡΧΕΙΑ ΤΡΟΠΟΠΟΙΗΘΗΚΑΝ
# ════════════════════════════════════════════════════════════════════════════════

📝 ΤΡΟΠΟΠΟΙΗΜΕΝΑ ΑΡΧΕΙΑ:

1. ✨ src/charges.py (ΝΕΟ ΑΡΧΕΙΟ)
   - fetch_charges(): Ανάκτηση από API
   - _extract_pkm_from_description(): Εξαγωγή PKM
   - add_charge_info(): Εμπλουτισμός records
   - get_employee_from_charge(): Εξαγωγή ονόματος

2. ✏️ src/daily_report.py
   - Σειρά 110-123: Προσθήκη κώδικα ανάκτησης χρεώσεων
   - Κάλεσμα: records = add_charge_info(records, charges_by_pkm)

3. ✏️ src/xls_export.py
   - Σειρή 39: Προσθήκη "Ανάθεση σε" στο headers array
   - Σειρά 58-62: Εξαγωγή employee από _charge
   - Σειρή 69: Προσθήκη 5ης στήλης στο loop
   - Σειρή 101-105: Εγγραφή στη 5η στήλη


# ════════════════════════════════════════════════════════════════════════════════
# ΑΡΧΕΙΑ ΣΤΙΣ ΟΠΟΙΕΣ ΔΕΝ ΕΓΙΝΕ ΑΛΛΑΓΗ (αλλά χρησιμοποιούνται)
# ════════════════════════════════════════════════════════════════════════════════

📋 ΑΝΑΓΝΩΣΜΕΝΑ ΑΡΧΕΙΑ (όχι τροποποιημένα):

1. src/session.py
   - login(): Χρησιμοποιείται για σύνδεση

2. src/incoming.py
   - fetch_incoming_records(): Ανάκτηση API queryId=6
   - simplify_incoming_records(): Απλοποίηση records
   - save_incoming_snapshot(): Αποθήκευση με _charge

3. src/api.py
   - enrich_record_details(): Προσθήκη procedure/directory

4. src/test_users.py
   - classify_records(): Κατάταξη real/test με _charge

5. src/daily_report.py (ΚΥΡΙΑ ΡΟΧΗ - χρησιμοποιεί τα πάντα)
   - _prepare_incoming(): Κύρια συνάρτηση

6. data/config.yaml
   - Διαμόρφωση API endpoints


# ════════════════════════════════════════════════════════════════════════════════
# ΣΗΜΕΙΑ ΕΛΕΓΧΟΥ - ΠΟΥ ΝΑ ΒΓΆΛΕΤΕ LOGS
# ════════════════════════════════════════════════════════════════════════════════

Αν θέλετε να ακολουθήσετε τη ροή:

1️⃣ Python shell - Έλεγχος charges:
   from src.charges import fetch_charges
   charges_records, charges_by_pkm = fetch_charges(monitor)
   print(f"Charges: {len(charges_records)}, By PKM: {len(charges_by_pkm)}")

2️⃣ Python shell - Έλεγχος record:
   rec = records[0]
   print(f"PKM: {rec['case_id']}")
   print(f"Charge: {rec.get('_charge')}")
   print(f"Employee: {rec['_charge']['employee']}")

3️⃣ JSON file - Έλεγχος snapshot:
   cat data/incoming_requests/2026-02-16.json | grep -A10 "_charge"

4️⃣ Excel - Έλεγχος στήλης:
   Ανοίξτε το αρχείο Excel και δείτε τη 5η στήλη


# ════════════════════════════════════════════════════════════════════════════════
# ΔΥΝΑΜΙΚΟΤΗΤΑ - ΕΓΧΥΜΕΝΑ ΔΕΔΟΜΕΝΑ ΑΝΑΤΟΠΟΘΕΤΗΣΗ
# ════════════════════════════════════════════════════════════════════════════════

Τα δεδομένα ροή:

API (queryId=19)
  ↓ 55 records
charges.py::fetch_charges()
  ↓ charges_by_pkm dict
daily_report.py::_prepare_incoming()
  ↓ καλές charges.py::add_charge_info()
    ↓ 177 records + _charge field
daily_report.py::save_incoming_snapshot()
  ↓ data/incoming_requests/2026-02-16.json (με _charge)
    ↓ daily_report.py::build_daily_digest()
      ↓ digest dict με incoming.records που έχουν _charge
        ↓ xls_export.py::build_requests_xls()
          ↓ Excel file με 5 στήλες (η τελευταία είναι "Ανάθεση σε")
"""
