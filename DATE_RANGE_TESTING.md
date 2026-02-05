# Date Range Testing Feature

## Δυνατότητα

Το σύστημα τώρα υποστηρίζει δοκιμή με συγκεκριμένη ημερομηνία range, ακριβώς όπως η δυνατότητα "Compare Applications Date Snapshot".

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
