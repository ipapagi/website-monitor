"""Export endpoints."""
import csv
import io

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from services.report_service import load_digest

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
