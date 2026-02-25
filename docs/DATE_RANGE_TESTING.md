# Date Range Testing Feature & Weekly Report Date Handling

## 🔴 NEW: Date Normalization & Monday Auto-Adjustment

### Date Normalization

The weekly report generator now accepts flexible date formats without leading zeros:

```bash
# All these commands are equivalent:
python src/weekly_report_generator.py --date=2026-02-09
python src/weekly_report_generator.py --date=2026-2-9
```

**Tested Formats:**
- `2026-02-09` (standard)
- `2026-2-9` (no leading zeros)
- `2026-12-5` (single digit month and day)
- `2026-2-19` (single digit month, two-digit day)

All normalize to: `YYYY-MM-DD` format

### Monday Auto-Adjustment

If the provided date is not a Monday, the system automatically uses the previous Monday:

```bash
# These all generate the report for the same Monday week:
python src/weekly_report_generator.py --date=2026-02-16  # Monday - exact date
python src/weekly_report_generator.py --date=2026-02-17  # Tuesday → Monday 2026-02-16
python src/weekly_report_generator.py --date=2026-02-18  # Wednesday → Monday 2026-02-16
python src/weekly_report_generator.py --date=2026-02-19  # Thursday → Monday 2026-02-16
python src/weekly_report_generator.py --date=2026-02-20  # Friday → Monday 2026-02-16
python src/weekly_report_generator.py --date=2026-02-21  # Saturday → Monday 2026-02-16
python src/weekly_report_generator.py --date=2026-02-22  # Sunday → Monday 2026-02-16
```

User receives feedback:
```
ℹ️  Adjusting to previous Monday: 2026-02-16
```

**Test Results:**
- ✅ All 7 weekdays correctly adjust to previous Monday
- ✅ Normalized dates used in filenames
- ✅ Week boundaries correctly calculated (Mon-Sun)

---

## Υπάρχουσα Δυνατότητα (Original - directory_emails.py):

## Χρήση

```bash
.venv\Scripts\python.exe src\directory_emails.py --date=YYYY-MM-DD
```

## Λογική

Όταν ορίσετε μια ημερομηνία με `--date=YYYY-MM-DD`:

1. **Βρίσκει** το snapshot για αυτή την ημερομηνία
2. **Ορίζει** το range από εκείνη την ημερομηνία μέχρι (αλλά όχι συμπεριλαμβανομένης) την επόμενη ημερομηνία
3. **Φορτώνει** όλα τα αιτήματα από αυτό το range
4. **Δημιουργεί** emails με attachments για αυτό το range

### Παραδείγματα

#### Παράδειγμα 1: Ημερομηνία με επόμενο snapshot
```bash
--date=2025-12-02
```
**Snapshots διαθέσιμα**: 2025-12-02, 2025-12-03, 2025-12-04, 2025-12-05, 2025-12-09, ...

**Range που φορτώνεται**: 2025-12-02 μέχρι 2025-12-09 (αποκλειστικά)
- Φορτώνει: `2025-12-02.json` 
- Δεν φορτώνει: `2025-12-09.json` (αυτό ξεκινά το επόμενο range)

#### Παράδειγμα 2: Ημερομηνία χωρίς επόμενο snapshot (τελευταία)
```bash
--date=2026-02-04
```
**Range που φορτώνεται**: 2026-02-04 μέχρι σήμερα
- Φορτώνει όλα τα snapshots από 2026-02-04 και μετά

## Τεχνικά

- Χρησιμοποιεί `INCOMING_FORCE_BASELINE_DATE` environment variable
- Ανακτά όλα τα διαθέσιμα snapshot dates από `data/incoming_requests/`
- Υπολογίζει το range σύμφωνα με τη Sequential Logic του Compare Applications
- Φορτώνει όλα τα records από τα snapshots στο range
- Χρησιμοποιεί το προηγούμενο snapshot ως baseline για σύγκριση αλλαγών
