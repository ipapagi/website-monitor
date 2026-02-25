# Αλλαγές στη Δομή FastAPI

## Τι Άλλαξε

### Πριν
- `python -m src.main` χωρίς arguments → ξεκίνημα FastAPI
- `python -m src.main --args` → κανονικό πρόγραμμα

### Τώρα
- `uvicorn src.main:app --host 0.0.0.0 --port 8000` → **μόνο** FastAPI
- `python -m src.main [--args]` → **μόνο** κανονικό πρόγραμμα (email + terminal)

## Αλλαγές στον Κώδικα

### `src/main.py`

**Αφαιρέθηκε:**
```python
def setup_fastapi_server():
    # ... εκτέλεση uvicorn.run()
```

**Προστέθηκε:**
```python
def create_fastapi_app():
    """Δημιουργεί και επιστρέφει το FastAPI application"""
    app = FastAPI(...)
    @app.get("/sede/daily")
    async def get_sede_daily():
        # ...
    return app

# Global app instance για uvicorn
if FASTAPI_AVAILABLE:
    app = create_fastapi_app()

if __name__ == '__main__':
    # Πάντα τρέχει το κανονικό πρόγραμμα
    main()
```

## Πλεονεκτήματα

✅ **Καθαρός διαχωρισμός:**
- FastAPI = μόνο API (χωρίς email, χωρίς terminal output)
- Normal = μόνο email + terminal (χωρίς API server)

✅ **Σωστή χρήση uvicorn:**
- Το uvicorn διαχειρίζεται το app instance
- Όχι programmatic uvicorn.run() που δημιουργούσε προβλήματα

✅ **if __name__ == "__main__":**
- Χρησιμοποιείται σωστά μόνο για το normal program
- Το FastAPI δεν εξαρτάται από αυτό

✅ **Production ready:**
- Μπορείς να χρησιμοποιήσεις gunicorn + uvicorn workers
- Καλύτερος έλεγχος του server lifecycle

## Εκτέλεση

### FastAPI Server
```bash
# Development
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# Custom port
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

### Κανονικό Πρόγραμμα
```bash
python -m src.main --send-daily-email
python -m src.main --check-incoming-portal
python -m src.main --save-baseline
```

## Δοκιμή

```bash
# Test structure
python test_fastapi_structure.py

# Test FastAPI endpoint (σε ξεχωριστό terminal)
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Σε άλλο terminal:
curl http://localhost:8000/sede/daily
```
