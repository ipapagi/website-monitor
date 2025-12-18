"""Export endpoints."""
import csv
import io

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse

from services.report_service import load_digest
from xls_export import build_requests_xls

router = APIRouter()


@router.get("/sede/export/csv", tags=["Export"])
async def export_csv():
    """Επιστρέφει δεδομένα σε CSV format."""
    try:
        report = load_digest()
        incoming = report.get("incoming", {})
        records = incoming.get("records", [])

        output = io.StringIO()
        if records:
            fieldnames = list(records[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sede_incoming_{incoming.get('date')}.csv"},
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(content={"error": str(e), "message": "Αποτυχία export CSV"}, status_code=500)


@router.get("/sede/export/xls", tags=["Export"])
async def export_xls(scope: str = Query(default="new", pattern="^(new|all)$", description="new: μόνο νέες, all: όλες οι αιτήσεις")):
    """Επιστρέφει Excel (.xls) με δύο φύλλα: Δοκιμαστικές και Πραγματικές.

    Επιλογή `scope`: "new" για νέες ή "all" για όλες οι αιτήσεις.
    """
    try:
        report = load_digest()
        incoming = report.get("incoming", {})
        date_str = incoming.get("date") or report.get("generated_at", "")[:10]

        xls_bytes = build_requests_xls(report, scope=scope)
        return StreamingResponse(
            iter([xls_bytes]),
            media_type="application/vnd.ms-excel",
            headers={"Content-Disposition": f"attachment; filename=incoming_{scope}_{date_str}.xls"},
        )
    except ImportError as ie:  # Missing xlwt
        return JSONResponse(content={"error": str(ie), "message": "Λείπει το xlwt για εξαγωγή .xls"}, status_code=500)
    except Exception as e:  # pragma: no cover
        return JSONResponse(content={"error": str(e), "message": "Αποτυχία export XLS"}, status_code=500)
