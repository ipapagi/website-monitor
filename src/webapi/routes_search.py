"""Search and filter endpoints."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.report_service import load_digest

router = APIRouter()


def _report():
    return load_digest()


@router.get("/sede/search", tags=["Αναζήτηση"])
async def search(q: str):
    """Αναζήτηση σε εισερχόμενες και διαδικασίες."""
    try:
        report = _report()
        query = q.lower()
        results = {"query": q, "incoming": [], "procedures": []}

        incoming = report.get("incoming", {})
        for record in incoming.get("records", []):
            if (
                query in str(record.get("case_id", "")).lower()
                or query in str(record.get("party", "")).lower()
                or query in str(record.get("subject", "")).lower()
                or query in str(record.get("procedure", "")).lower()
            ):
                results["incoming"].append(record)

        all_changes = report.get("all", {}).get("changes") or {}
        for change_type in ["new", "activated", "deactivated", "modified"]:
            for item in all_changes.get(change_type, []):
                proc = item.get("new", item) if isinstance(item, dict) and "new" in item else item
                if query in str(proc.get("κωδικός", "")).lower() or query in str(proc.get("τίτλος", "")).lower():
                    if proc not in results["procedures"]:
                        results["procedures"].append(proc)

        results["totals"] = {"incoming": len(results["incoming"]), "procedures": len(results["procedures"])}
        return JSONResponse(content=results, status_code=200)
    except Exception as e:  # pragma: no cover
        return JSONResponse(content={"error": str(e), "message": "Αποτυχία αναζήτησης"}, status_code=500)


@router.get("/sede/incoming/filter", tags=["Αναζήτηση"])
async def filter_incoming(party: str = None, procedure: str = None, date_from: str = None, date_to: str = None):
    """Φιλτράρει εισερχόμενες αιτήσεις."""
    try:
        report = _report()
        records = report.get("incoming", {}).get("records", [])
        filtered = []

        for record in records:
            if party and party.lower() not in str(record.get("party", "")).lower():
                continue
            if procedure and procedure.lower() not in str(record.get("procedure", "")).lower():
                continue
            submitted = record.get("submitted_at", "")[:10]
            if date_from and submitted < date_from:
                continue
            if date_to and submitted > date_to:
                continue
            filtered.append(record)

        return JSONResponse(
            content={
                "filters": {"party": party, "procedure": procedure, "date_from": date_from, "date_to": date_to},
                "total": len(filtered),
                "records": filtered,
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(content={"error": str(e), "message": "Αποτυχία φιλτραρίσματος"}, status_code=500)
