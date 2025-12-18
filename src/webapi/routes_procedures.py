"""Endpoints for procedures changes and counts."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.report_service import load_digest

router = APIRouter()


def _report():
    return load_digest()


@router.get("/sede/procedures/active", tags=["Διαδικασίες"])
async def get_procedures_active():
    """Επιστρέφει μόνο ενεργές διαδικασίες."""
    try:
        report = _report()
        return JSONResponse(
            content={
                "generated_at": report.get("generated_at"),
                "total": report.get("active", {}).get("total", 0),
                "baseline_timestamp": report.get("active", {}).get("baseline_timestamp"),
                "changes": report.get("active", {}).get("changes"),
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης ενεργών διαδικασιών"},
            status_code=500,
        )


@router.get("/sede/procedures/all", tags=["Διαδικασίες"])
async def get_procedures_all():
    """Επιστρέφει όλες τις διαδικασίες."""
    try:
        report = _report()
        return JSONResponse(
            content={
                "generated_at": report.get("generated_at"),
                "total": report.get("all", {}).get("total", 0),
                "baseline_timestamp": report.get("all", {}).get("baseline_timestamp"),
                "changes": report.get("all", {}).get("changes"),
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης διαδικασιών"},
            status_code=500,
        )


@router.get("/sede/procedures/changes", tags=["Διαδικασίες"])
async def get_procedures_changes():
    """Επιστρέφει αλλαγές διαδικασιών."""
    try:
        report = _report()
        active_changes = report.get("active", {}).get("changes") or {}
        all_changes = report.get("all", {}).get("changes") or {}
        return JSONResponse(
            content={
                "generated_at": report.get("generated_at"),
                "active": {
                    "new": active_changes.get("new", []),
                    "activated": active_changes.get("activated", []),
                    "deactivated": active_changes.get("deactivated", []),
                    "removed": active_changes.get("removed", []),
                    "modified": active_changes.get("modified", []),
                },
                "all": {
                    "new": all_changes.get("new", []),
                    "activated": all_changes.get("activated", []),
                    "deactivated": all_changes.get("deactivated", []),
                    "removed": all_changes.get("removed", []),
                    "modified": all_changes.get("modified", []),
                },
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης αλλαγών διαδικασιών"},
            status_code=500,
        )


@router.get("/sede/procedures/inactive", tags=["Διαδικασίες"])
async def get_procedures_inactive():
    """Επιστρέφει μόνο ανενεργές διαδικασίες."""
    try:
        report = _report()
        active_total = report.get("active", {}).get("total", 0)
        all_total = report.get("all", {}).get("total", 0)
        inactive_count = all_total - active_total
        return JSONResponse(
            content={
                "generated_at": report.get("generated_at"),
                "total": inactive_count,
                "message": "Για λίστα ανενεργών, χρησιμοποίησε /sede/procedures/all και φίλτραρε ενεργή=ΟΧΙ",
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία υπολογισμού ανενεργών"},
            status_code=500,
        )
