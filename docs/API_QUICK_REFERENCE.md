# API Quick Reference

## 🎯 Τα πιο χρήσιμα endpoints

```bash
# Σύνοψη (γρήγορη επισκόπηση)
GET /sede/summary

# Νέες πραγματικές αιτήσεις
GET /sede/incoming/real

# Αναζήτηση
GET /sede/search?q=KEYWORD

# Ιστορικό 7 ημερών
GET /sede/history/daily?days=7

# Health check
GET /health
```

## 📊 Κατηγορίες Endpoints

| Κατηγορία | Endpoints | Χρήση |
|-----------|-----------|-------|
| **Πλήρης Αναφορά** | `/sede/daily` | Όλα τα δεδομένα |
| **Στατιστικά** | `/sede/summary`, `/sede/stats` | Νούμερα & ποσοστά |
| **Εισερχόμενες** | `/sede/incoming/*` | Αιτήσεις (all, new, real, test, changes, {date}) |
| **Διαδικασίες** | `/sede/procedures/*` | Procedures (active, all, changes, inactive) |
| **Αναζήτηση** | `/sede/search`, `/sede/incoming/filter` | Query & filters |
| **Ιστορικό** | `/sede/history/*`, `/sede/comparison`, `/sede/trends/*` | Trends & history |
| **Status** | `/health`, `/sede/baseline`, `/sede/last-update` | System info |
| **Export** | `/sede/export/*` | CSV download |

## 🔥 Top 10 Endpoints

1. **`GET /sede/summary`** - Γρήγορη επισκόπηση
2. **`GET /sede/incoming/new`** - Νέες αιτήσεις
3. **`GET /sede/incoming/real`** - Πραγματικές μόνο
4. **`GET /sede/search?q=X`** - Αναζήτηση
5. **`GET /sede/stats`** - Λεπτομερή στατιστικά
6. **`GET /sede/history/daily?days=7`** - Weekly history
7. **`GET /sede/incoming/filter?party=X`** - Φίλτρο
8. **`GET /sede/procedures/changes`** - Αλλαγές διαδικασιών
9. **`GET /sede/comparison?date1=X&date2=Y`** - Σύγκριση
10. **`GET /health`** - Health check

## 💻 Quick Commands

```bash
# Install & Run
pip install fastapi uvicorn
uvicorn src.main:app --reload

# Test
curl http://localhost:8000/health
curl http://localhost:8000/sede/summary

# Docs
open http://localhost:8000/docs
```

## 📖 Full Documentation

👉 **[API_COMPLETE_GUIDE.md](API_COMPLETE_GUIDE.md)** - Πλήρης οδηγός με παραδείγματα
