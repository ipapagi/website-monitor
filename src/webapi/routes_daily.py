"""Daily and summary endpoints."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from incoming import load_incoming_snapshot
from services.report_service import load_digest, count_changes, incoming_stats
from test_users import get_record_stats

router = APIRouter()


class PeriodSummaryRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=90, description="Αριθμός ημερών για σύνοψη (1-90)")
    include_details: bool = Field(default=False, description="Συμπερίληψη λεπτομερειών ανά ημέρα")


@router.get("/sede/daily", tags=["Πλήρης Αναφορά"])
async def get_sede_daily():
    """Επιστρέφει ημερήσια αναφορά φιλική για Teams/Power Automate."""
    try:
        report = load_digest()
        incoming = report.get("incoming", {})
        incoming_changes = incoming.get("changes", {})
        active_changes = (report.get("active") or {}).get("changes") or {}
        all_changes = (report.get("all") or {}).get("changes") or {}

        payload = {
            "generated_at": report.get("generated_at", ""),
            "date": incoming.get("date") or report.get("generated_at", "")[:10],
            "base_url": report.get("base_url", ""),
            "is_historical_comparison": report.get("is_historical_comparison", False),
            "comparison_date": report.get("comparison_date"),
            "reference_date": report.get("reference_date") or incoming.get("reference_date"),
            "active_total": report.get("active", {}).get("total", 0),
            "all_total": report.get("all", {}).get("total", 0),
            "incoming_total": incoming.get("stats", {}).get("total", 0),
            "incoming_real": incoming.get("stats", {}).get("real", 0),
            "incoming_test": incoming.get("stats", {}).get("test", 0),
            "incoming_removed": len(incoming_changes.get("removed", [])),
            "active_new": len(active_changes.get("new", [])),
            "active_modified": len(active_changes.get("modified", [])),
            "all_new": len(all_changes.get("new", [])),
            "all_modified": len(all_changes.get("modified", [])),
            # Αναλυτική αναφορά νέων αιτήσεων (πραγματικές, δοκιμαστικές, αφαιρεμένες)
            "incoming_real_new": incoming.get("real_new", []),
            "incoming_test_new": incoming.get("test_new", []),
            "incoming_removed_list": incoming_changes.get("removed", []),
            "notes": [
                "Use in Teams/Power Automate cards",
                "Flat schema: no deep nesting for easy dynamic content mapping",
                "incoming_real_new/test_new/removed_list contain full record details",
            ],
        }

        return JSONResponse(content=payload, status_code=200)
    except Exception as e:  # pragma: no cover - runtime safeguard
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης αναφοράς ΣΗΔΕ"},
            status_code=500,
        )


@router.get("/sede/summary", tags=["Στατιστικά"])
async def get_summary():
    """Επιστρέφει σύνοψη με βασικά νούμερα."""
    try:
        report = load_digest()
        incoming = report.get("incoming", {})
        active_changes = (report.get("active") or {}).get("changes") or {}
        all_changes = (report.get("all") or {}).get("changes") or {}
        total, real, test = incoming_stats(report)

        summary = {
            "generated_at": report.get("generated_at"),
            "totals": {
                "active_procedures": report.get("active", {}).get("total", 0),
                "all_procedures": report.get("all", {}).get("total", 0),
                "incoming_total": total,
                "incoming_real": real,
                "incoming_test": test,
            },
            "changes": {
                "active_new": count_changes(active_changes, "new"),
                "active_modified": count_changes(active_changes, "modified"),
                "all_new": count_changes(all_changes, "new"),
                "incoming_new_real": len(incoming.get("real_new", [])),
                "incoming_new_test": len(incoming.get("test_new", [])),
                "incoming_removed": len(incoming.get("changes", {}).get("removed", [])),
            },
        }
        return JSONResponse(content=summary, status_code=200)
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης σύνοψης"},
            status_code=500,
        )


@router.get("/sede/stats", tags=["Στατιστικά"])
async def get_stats():
    """Επιστρέφει λεπτομερή στατιστικά."""
    try:
        report = load_digest()
        incoming = report.get("incoming", {})
        total, real, test = incoming_stats(report)

        return JSONResponse(
            content={
                "generated_at": report.get("generated_at"),
                "procedures": {
                    "active": report.get("active", {}).get("total", 0),
                    "all": report.get("all", {}).get("total", 0),
                    "inactive": report.get("all", {}).get("total", 0)
                    - report.get("active", {}).get("total", 0),
                },
                "incoming": {
                    "total": total,
                    "real": real,
                    "test": test,
                    "real_percentage": round(real / total * 100, 1) if total > 0 else 0,
                    "test_percentage": round(test / total * 100, 1) if total > 0 else 0,
                    "test_breakdown": incoming.get("stats", {}).get("test_breakdown", {}),
                },
                "baselines": {
                    "active": report.get("active", {}).get("baseline_timestamp"),
                    "all": report.get("all", {}).get("baseline_timestamp"),
                    "incoming": incoming.get("reference_date"),
                },
            },
            status_code=200,
        )
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης στατιστικών"},
            status_code=500,
        )


@router.post("/sede/summary/period", tags=["Στατιστικά"])
async def post_period_summary(request: PeriodSummaryRequest = Body(...)):
    """Επιστρέφει σύνοψη για συγκεκριμένο αριθμό ημερών (POST request)."""
    try:
        days = request.days
        include_details = request.include_details
        
        today = datetime.now()
        daily_data = []
        total_incoming = 0
        total_real = 0
        total_test = 0
        
        for i in range(days):
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            snapshot = load_incoming_snapshot(date_str)
            
            if snapshot:
                records = snapshot.get("records", [])
                stats = get_record_stats(records)
                day_total = len(records)
                day_real = stats.get("real", 0)
                day_test = stats.get("test", 0)
                
                total_incoming += day_total
                total_real += day_real
                total_test += day_test
                
                if include_details:
                    daily_data.append({
                        "date": date_str,
                        "total": day_total,
                        "real": day_real,
                        "test": day_test,
                    })
        
        # Υπολογισμός μέσων όρων
        avg_total = round(total_incoming / days, 1) if days > 0 else 0
        avg_real = round(total_real / days, 1) if days > 0 else 0
        avg_test = round(total_test / days, 1) if days > 0 else 0
        
        summary = {
            "period": {
                "days": days,
                "from": (today - timedelta(days=days - 1)).strftime("%Y-%m-%d"),
                "to": today.strftime("%Y-%m-%d"),
            },
            "totals": {
                "incoming": total_incoming,
                "real": total_real,
                "test": total_test,
                "real_percentage": round(total_real / total_incoming * 100, 1) if total_incoming > 0 else 0,
                "test_percentage": round(total_test / total_incoming * 100, 1) if total_incoming > 0 else 0,
            },
            "averages": {
                "daily_incoming": avg_total,
                "daily_real": avg_real,
                "daily_test": avg_test,
            },
        }
        
        if include_details:
            summary["daily_breakdown"] = daily_data
        
        return JSONResponse(content=summary, status_code=200)
    except Exception as e:  # pragma: no cover
        return JSONResponse(
            content={"error": str(e), "message": "Αποτυχία ανάκτησης σύνοψης περιόδου"},
            status_code=500,
        )
