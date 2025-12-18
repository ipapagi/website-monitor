"""Incoming requests endpoints."""
from datetime import datetime, timedelta

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from incoming import compare_incoming_records, load_incoming_snapshot
from services.report_service import load_digest
from test_users import classify_records, get_record_stats

router = APIRouter()


def _incoming_section():
    report = load_digest()
    return report.get("incoming", {})


@router.get("/sede/incoming", tags=["Εισερχόμενες Αιτήσεις"])
async def get_incoming():
    """Επιστρέφει όλες τις εισερχόμενες αιτήσεις."""
    try:
        incoming = _incoming_section()
        return JSONResponse(
            content={
                "date": incoming.get("date"),
                "reference_date": incoming.get("reference_date"),
                "total": incoming.get("stats", {}).get("total", 0),
                "records": incoming.get("records", []),
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης εισερχόμενων"},
            status_code=500,
        )


@router.get("/sede/incoming/new", tags=["Εισερχόμενες Αιτήσεις"])
async def get_incoming_new():
    """Επιστρέφει μόνο νέες αιτήσεις (real + test)."""
    try:
        incoming = _incoming_section()
        return JSONResponse(
            content={
                "date": incoming.get("date"),
                "real": incoming.get("real_new", []),
                "test": incoming.get("test_new", []),
                "total": len(incoming.get("real_new", [])) + len(incoming.get("test_new", [])),
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης νέων αιτήσεων"},
            status_code=500,
        )


@router.get("/sede/incoming/real", tags=["Εισερχόμενες Αιτήσεις"])
async def get_incoming_real():
    """Επιστρέφει μόνο πραγματικές αιτήσεις."""
    try:
        incoming = _incoming_section()
        records = incoming.get("records", [])
        real, _ = classify_records(records)
        return JSONResponse(
            content={"date": incoming.get("date"), "total": len(real), "records": real},
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης πραγματικών αιτήσεων"},
            status_code=500,
        )


@router.get("/sede/incoming/test", tags=["Εισερχόμενες Αιτήσεις"])
async def get_incoming_test():
    """Επιστρέφει μόνο δοκιμαστικές αιτήσεις."""
    try:
        incoming = _incoming_section()
        records = incoming.get("records", [])
        _, test = classify_records(records)
        return JSONResponse(
            content={"date": incoming.get("date"), "total": len(test), "records": test},
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης δοκιμαστικών αιτήσεων"},
            status_code=500,
        )


@router.get("/sede/incoming/changes", tags=["Εισερχόμενες Αιτήσεις"])
async def get_incoming_changes():
    """Επιστρέφει μόνο αλλαγές εισερχόμενων."""
    try:
        incoming = _incoming_section()
        changes = incoming.get("changes", {})
        return JSONResponse(
            content={
                "date": incoming.get("date"),
                "reference_date": incoming.get("reference_date"),
                "new": changes.get("new", []),
                "removed": changes.get("removed", []),
                "modified": changes.get("modified", []),
                "totals": {
                    "new": len(changes.get("new", [])),
                    "removed": len(changes.get("removed", [])),
                    "modified": len(changes.get("modified", [])),
                },
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης αλλαγών"},
            status_code=500,
        )


@router.get("/sede/incoming/{date}", tags=["Εισερχόμενες Αιτήσεις"])
async def get_incoming_by_date(date: str):
    """Επιστρέφει snapshot συγκεκριμένης ημερομηνίας (YYYY-MM-DD)."""
    try:
        snapshot = load_incoming_snapshot(date)
        if not snapshot:
            return JSONResponse(content={"error": f"Δεν βρέθηκε snapshot για {date}"}, status_code=404)

        records = snapshot.get("records", [])
        stats = get_record_stats(records)
        return JSONResponse(
            content={"date": date, "total": len(records), "stats": stats, "records": records},
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": f"Αποτυχία ανάκτησης snapshot {date}"},
            status_code=500,
        )


@router.get("/sede/history/daily", tags=["Ιστορικό"])
async def get_daily_history(days: int = 7):
    """Επιστρέφει ιστορικό τελευταίων n ημερών."""
    try:
        history = []
        today = datetime.now()

        for i in range(days):
            snapshot_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            snapshot = load_incoming_snapshot(snapshot_date)
            if snapshot:
                records = snapshot.get("records", [])
                stats = get_record_stats(records)
                history.append(
                    {
                        "date": snapshot_date,
                        "total": len(records),
                        "real": stats.get("real", 0),
                        "test": stats.get("test", 0),
                    }
                )

        return JSONResponse(content={"days": days, "history": history}, status_code=200)
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης ιστορικού"},
            status_code=500,
        )


@router.get("/sede/comparison", tags=["Ιστορικό"])
async def compare_dates(date1: str, date2: str):
    """Σύγκριση δύο ημερομηνιών."""
    try:
        snap1 = load_incoming_snapshot(date1)
        snap2 = load_incoming_snapshot(date2)
        if not snap1:
            return JSONResponse(content={"error": f"Δεν βρέθηκε snapshot για {date1}"}, status_code=404)
        if not snap2:
            return JSONResponse(content={"error": f"Δεν βρέθηκε snapshot για {date2}"}, status_code=404)

        records1 = snap1.get("records", [])
        records2 = snap2.get("records", [])
        stats1 = get_record_stats(records1)
        stats2 = get_record_stats(records2)
        changes = compare_incoming_records(records2, snap1)

        return JSONResponse(
            content={
                "date1": date1,
                "date2": date2,
                "date1_stats": {"total": len(records1), "real": stats1.get("real", 0), "test": stats1.get("test", 0)},
                "date2_stats": {"total": len(records2), "real": stats2.get("real", 0), "test": stats2.get("test", 0)},
                "changes": changes,
                "diff": {
                    "total": len(records2) - len(records1),
                    "real": stats2.get("real", 0) - stats1.get("real", 0),
                    "test": stats2.get("test", 0) - stats1.get("test", 0),
                },
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία σύγκρισης"},
            status_code=500,
        )


@router.get("/sede/trends/weekly", tags=["Ιστορικό"])
async def get_weekly_trends():
    """Επιστρέφει weekly trends."""
    try:
        weeks = []
        today = datetime.now()

        for week in range(4):
            week_data = {"week": week + 1, "days": []}
            for day in range(7):
                date_str = (today - timedelta(days=(week * 7 + day))).strftime("%Y-%m-%d")
                snapshot = load_incoming_snapshot(date_str)
                if snapshot:
                    records = snapshot.get("records", [])
                    stats = get_record_stats(records)
                    week_data["days"].append(
                        {"date": date_str, "total": len(records), "real": stats.get("real", 0), "test": stats.get("test", 0)}
                    )

            if week_data["days"]:
                week_data["totals"] = {
                    "total": sum(d["total"] for d in week_data["days"]),
                    "real": sum(d["real"] for d in week_data["days"]),
                    "test": sum(d["test"] for d in week_data["days"]),
                }
                weeks.append(week_data)

        return JSONResponse(content={"weeks": weeks}, status_code=200)
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης trends"},
            status_code=500,
        )
