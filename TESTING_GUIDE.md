# Οδηγός Δοκιμής - Νέα Δομή FastAPI

## Βήμα 1: Έλεγχος Δομής

Τρέξε στο **Python Debug Console**:
```python
python test_fastapi_structure.py
```

Αναμενόμενο output:
```
✅ app instance imported successfully
✅ App routes available
✅ /sede/daily endpoint exists
✅ create_fastapi_app() works correctly
✅ main() function still available
✅ All structure tests passed!
```

## Βήμα 2: Εκκίνηση FastAPI Server

Στο **Python Debug Console** (ή νέο terminal με .venv):
```python
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Πρέπει να δεις:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Βήμα 3: Δοκιμή Endpoint

Σε νέο terminal ή browser:
```bash
curl http://localhost:8000/sede/daily
```

Ή άνοιξε στο browser:
- http://localhost:8000/sede/daily (JSON response)
- http://localhost:8000/docs (Swagger UI)

## Βήμα 4: Δοκιμή Κανονικού Προγράμματος

Στο **Python Debug Console** (ενώ το FastAPI τρέχει σε άλλο terminal):
```python
python -m src.main --help
```

Πρέπει να δεις το help menu, όχι το FastAPI server.

## Βήμα 5: Δοκιμή Email

```python
python -m src.main --send-daily-email
```

Πρέπει να:
- ✅ Συνδεθεί στο portal
- ✅ Ανακτήσει δεδομένα
- ✅ Τυπώσει στο terminal
- ✅ Στείλει email
- ✅ Δημιουργήσει PDF
- ❌ ΔΕΝ πρέπει να ξεκινήσει FastAPI server

## Επιβεβαίωση

✅ FastAPI = μόνο API (με uvicorn)
✅ Normal = μόνο email + terminal (με python -m)
✅ Κανένας overlap μεταξύ των δύο

## Σε περίπτωση προβλήματος

Αν κάτι δεν δουλεύει:
1. Στείλε το error message
2. Πες ποια εντολή τρέχεις
3. Θα το διορθώσω αμέσως
