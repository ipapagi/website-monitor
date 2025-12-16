"""Health and status endpoints."""
import os
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import get_project_root
from services.report_service import load_digest

router = APIRouter()


@router.get("/health", tags=["Status"])
async def health_check():
    """Health check του API."""
    try:
        root = get_project_root()
        baseline_active = os.path.join(root, "data", "active_procedures_baseline.json")
        baseline_all = os.path.join(root, "data", "all_procedures_baseline.json")

        return JSONResponse(
            content={
                "status": "healthy",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "api_version": "1.0.0",
                "data_available": {
                    "active_baseline": os.path.exists(baseline_active),
                    "all_baseline": os.path.exists(baseline_all),
                },
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(content={"status": "unhealthy", "error": str(e)}, status_code=503)


@router.get("/sede/baseline", tags=["Status"])
async def get_baseline_info():
    """Επιστρέφει πληροφορίες baseline."""
    try:
        report = load_digest()
        return JSONResponse(
            content={
                "active_procedures": {
                    "timestamp": report.get("active", {}).get("baseline_timestamp"),
                    "count": report.get("active", {}).get("total", 0),
                },
                "all_procedures": {
                    "timestamp": report.get("all", {}).get("baseline_timestamp"),
                    "count": report.get("all", {}).get("total", 0),
                },
                "incoming": {
                    "current_date": report.get("incoming", {}).get("date"),
                    "reference_date": report.get("incoming", {}).get("reference_date"),
                },
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης baseline info"},
            status_code=500,
        )


@router.get("/sede/last-update", tags=["Status"])
async def get_last_update():
    """Επιστρέφει πότε ανανεώθηκαν τα δεδομένα."""
    try:
        root = get_project_root()
        incoming_today = os.path.join(root, "data", "incoming_requests", f'incoming_{datetime.now().strftime("%Y-%m-%d")}.json')
        last_update = None
        if os.path.exists(incoming_today):
            last_update = datetime.fromtimestamp(os.path.getmtime(incoming_today)).strftime("%Y-%m-%d %H:%M:%S")

        return JSONResponse(
            content={"last_update": last_update, "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης last update"},
            status_code=500,
        )
