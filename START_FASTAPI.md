# Εκκίνηση FastAPI Server

## Προτεινόμενος Τρόπος

Χρησιμοποίησε το `uvicorn` για να ξεκινήσεις το FastAPI server:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Επιλογές

### Development Mode (με auto-reload)
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
Ανανεώνει αυτόματα όταν αλλάζουν τα αρχεία.

### Custom Port
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

### Localhost Only
```bash
uvicorn src.main:app --host 127.0.0.1 --port 8000
```

### Production (με workers)
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Πρόσβαση

- **API Endpoint:** http://localhost:8000/sede/daily
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Σημαντικό

⚠️ Το `python -m src.main` **ΔΕΝ** ξεκινά το FastAPI server πια.  
Τρέχει το κανονικό πρόγραμμα με email + terminal output.

✅ Για FastAPI, χρησιμοποίησε **πάντα** το `uvicorn src.main:app`
