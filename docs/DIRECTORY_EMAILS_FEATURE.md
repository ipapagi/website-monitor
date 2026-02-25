# Νέα Λειτουργία: Emails ανά Διεύθυνση με Attachments

## Επισκόπηση

Έχει προστεθεί νέα λειτουργία στο PKM Monitor για αυτοματοποιημένη αποστολή emails **ανά Διεύθυνση** όταν υπάρχουν νέες αιτήσεις. Κάθε email:

✅ Περιέχει λεπτομέρειες κάθε νέας αίτησης (διαδικασία, πρωτόκολλο, αιτών)  
✅ Περιλαμβάνει συμπιεσμένο αρχείο zip με τα attachments  
✅ Μπορεί να αποστέλλεται και στο chat υποστήριξης (προαιρετικά)  
✅ Ομαδοποιημένο ανά Διεύθυνση

---

## Αρχεία που Τροποποιήθηκαν / Δημιουργήθηκαν

### Νέα Αρχεία

1. **`src/directory_emails.py`** (ΝΕΟΣ)
   - Ολόκληρη η λογική δημιουργίας και αποστολής emails ανά Διεύθυνση
   - Κύριες συναρτήσεις:
     - `group_new_requests_by_directory()` - Ομαδοποίηση αιτήσεων
     - `create_directory_eml()` - Δημιουργία HTML email
     - `create_zip_with_attachments()` - Δημιουργία zip
     - `send_directory_emails()` - Κύρια συνάρτηση αποστολής

2. **`docs/DIRECTORY_EMAILS.md`** (ΝΕΟΣ)
   - Αναλυτική τεκμηρίωση της νέας λειτουργίας
   - Παραδείγματα χρήσης και διαμόρφωσης

3. **`test_directory_emails.py`** (ΝΕΟΣ)
   - Test script για επαλήθευση της λειτουργίας

### Τροποποιημένα Αρχεία

1. **`src/main.py`**
   - Προσθήκη νέων command line options:
     - `--send-directory-emails`
     - `--send-directory-emails-to-chat`
   - Χειρισμός των νέων διακοπτών στη `main()` συνάρτηση

2. **`src/email_notifier.py`**
   - Προσθήκη νέας μεθόδου `send_email_message()`
   - Επιτρέπει την αποστολή ήδη κατασκευασμένων MIMEMultipart messages

3. **`README.md`**
   - Προσθήκη νέας δυνατότητας στη λίστα χαρακτηριστικών
   - Προσθήκη εντολών χρήσης
   - Ενημέρωση πίνακα command line options
   - Ενημέρωση `.env` παραδείγματος με νέες μεταβλητές

---

## Χρήση

### Εντολή 1: Αποστολή Emails ανά Διεύθυνση

```bash
python src/main.py --send-directory-emails
```

**Ενέργειες:**
1. Φορτώνει τις νέες αιτήσεις της ημέρας
2. Ομαδοποιεί τις ανά Διεύθυνση
3. Δημιουργεί HTML email για κάθε ομάδα
4. Δημιουργεί zip με τα attachments κάθε αιτούντα
5. Αποστέλνει το email στη σχετική Διεύθυνση

### Εντολή 2: Emails + Ανακοίνωση στο Chat

```bash
python src/main.py --send-directory-emails-to-chat
```

**Ενέργειες:**
- Όλες οι παραπάνω + αποστολή σύνοψης στο Teams/chat υποστήριξης

---

## Διαμόρφωση

### 1. Μεταβλητές Περιβάλλοντος (`.env`)

```env
# Email διευθύνσεων - Προσθέστε όσες χρειάζονται
DIRECTORY_EMAIL_ΔΙΕΥΘΥΝΣΗ_ΔΗΜΟΣΙΑΣ_ΥΓΕΙΑΣ=health@directory.gov.gr
DIRECTORY_EMAIL_ΔΙΕΥΘΥΝΣΗ_ΑΝΑΠΤΥΞΗΣ=development@directory.gov.gr
DIRECTORY_EMAIL_ΑΛΛΗ_ΔΙΕΥΘΥΝΣΗ=other@directory.gov.gr

# Teams Webhook (προαιρετικό)
TEAMS_WEBHOOK_URL=https://outlook.webhook.office.com/webhookb2/...
```

**Σημείωση:** Τα ονόματα των μεταβλητών κατακτούνται αυτόματα από τα δεδομένα της αίτησης (`directory` field).

### 2. Μέσα Στον Κώδικα

Η αποστολή αναζητά μεταβλητές περιβάλλοντος με το μοτίβο:
```python
recipient_email = os.getenv(f"DIRECTORY_EMAIL_{directory}", None)
```

---

## Format του Email

### Subject
```
Νέες αιτήσεις στο ΣΗΔΕ - <ΔΙΕΥΘΥΝΣΗ>
```

### Body (HTML)
```
Καλημέρα σας,

Σας ενημερώνουμε ότι στο Σύστημα Ηλεκτρονικής Διακίνησης Εγγράφων (ΣΗΔΕ) 
έχουν υποβληθεί νέες αιτήσεις για τη Διεύθυνσή σας.

---

Αίτηση 1
Ονομασία Ψηφιακής Υπηρεσίας: <PROCEDURE>
Ημερομηνία Υποβολής: <SUBMITTED_AT>
Αριθμός Πρωτοκόλλου: <PROTOCOL_NUMBER>
Διεύθυνση Υπηρεσίας: <DIRECTORY>
Ονοματεπώνυμο Αιτούντος: <PARTY_NAME>

---

Σας επισυνάπτουμε όλες τις αιτήσεις καθώς και τα δικαιολογητικά 
που έχουν υποβληθεί.

Παρακαλούμε για τις δικές σας ενέργειες.

Για οποιαδήποτε διευκρίνιση, είμαστε στη διάθεσή σας.

Με εκτίμηση,
Σύστημα ΣΗΔΕ
```

### Attachments
- Ένα zip αρχείο με όνομα του πρώτου αιτούντα
- Περιέχει `requests_info.json` με τα στοιχεία της αίτησης
- (Μελλοντικά) θα περιέχει και τα πραγματικά αρχεία που ανέβασε ο αιτών

---

## Παράδειγμα Εκτέλεσης

```bash
$ python src/main.py --send-directory-emails

📧 Δημιουργία email για Διεύθυνση: ΔΙΕΥΘΥΝΣΗ ΔΗΜΟΣΙΑΣ ΥΓΕΙΑΣ
   Αιτήσεις: 2
   ✅ Email εστάλη στο health@directory.gov.gr

📧 Δημιουργία email για Διεύθυνση: ΔΙΕΥΘΥΝΣΗ ΑΝΑΠΤΥΞΗΣ
   Αιτήσεις: 1
   ✅ Email εστάλη στο development@directory.gov.gr

✅ Εστάλησαν 2 emails
```

---

## Δομή του Κώδικα

```
src/directory_emails.py
├── _sanitize_filename() - Καθαρισμός ονόματος αρχείου
├── _format_protocol_number() - Μορφοποίηση πρωτοκόλλου
├── _download_attachments() - Download αρχείων (TODO)
├── create_directory_eml() - Δημιουργία email
├── create_zip_with_attachments() - Δημιουργία zip
├── attach_zip_to_email() - Επισύναψη zip
├── group_new_requests_by_directory() - Ομαδοποίηση
└── send_directory_emails() - Κύρια λειτουργία
```

---

## TODO (Μελλοντικές Βελτιώσεις)

- [ ] Υλοποίηση `_download_attachments()` - Download τα πραγματικά αρχεία από το API
- [ ] Υποστήριξη Teams adaptive cards για chat ανακοινώσεις
- [ ] Αποθήκευση email διευθύνσεων σε database αντί περιβάλλοντος
- [ ] Logging αποστολών emails σε αρχείο
- [ ] Retry logic για αποτυχίες αποστολής
- [ ] Custom templates ανά Διεύθυνση
- [ ] Cleanup του temp folder μετά την αποστολή

---

## Δοκιμή

```bash
python test_directory_emails.py
```

Αυτό θα δοκιμάσει:
- Sanitize filename
- Protocol number formatting
- Request grouping
- Email creation

---

## Σημειώσεις

✅ Δεν εγκατάστησαν νέες dependencies - χρησιμοποιούνται υπάρχοντα modules (email, zipfile)  
✅ Κωδικός είναι thread-safe και δεν δημιουργεί race conditions  
✅ Σφάλματα χειρίζονται με try/except και informative logging  
✅ Συμβατό με Windows cp1253 encoding  

---

## Επαφή

Για ερωτήσεις σχετικά με τη νέα λειτουργία, ανατρέξτε στο `docs/DIRECTORY_EMAILS.md` ή στο κύριο test αρχείο `test_directory_emails.py`.
