"""Excel export for new incoming requests (real and test)."""
from __future__ import annotations

import io
from datetime import datetime
from typing import Dict, List

try:
    import xlwt  # .xls writer
except ImportError:  # pragma: no cover
    xlwt = None


def _format_protocol(rec: Dict) -> str:
    """Compose protocol string like "<case_id>(<protocol_number>)/DD-MM-YYYY"."""
    # case_id is outside, protocol_number is inside parentheses (same as CLI format)
    case_id = (rec.get("case_id") or "").strip()
    protocol = (rec.get("protocol_number") or "").strip()
    submitted_at = (rec.get("submitted_at") or "").strip()
    try:
        # Accept ISO or date-like strings
        dt = datetime.fromisoformat(submitted_at.replace(" ", "T")) if "-" in submitted_at else None
    except Exception:
        dt = None
    date_str = dt.strftime("%d-%m-%Y") if dt else ""
    if case_id and protocol and date_str:
        return f"{case_id}({protocol})/{date_str}"
    if case_id and date_str:
        return f"{case_id}/{date_str}"
    if protocol and date_str:
        return f"{protocol}/{date_str}"
    return case_id or protocol or date_str or ""


def _write_sheet(ws, rows: List[Dict], title: str):
    headers = ["Δ/νση", "Αρ. Πρωτοκόλλου", "Διαδικασία"]
    # Styles
    header_style = xlwt.easyxf("font: bold on; pattern: pattern solid, fore_colour pale_blue;") if xlwt else None
    # Text format to prevent Excel from auto-converting numbers
    text_style = xlwt.easyxf("", num_format_str="@") if xlwt else None
    normal_style = xlwt.easyxf("") if xlwt else None

    # Sort rows by submitted_at ascending (older first, most recent last)
    def _parse_date(s: str):
        if not s:
            return None
        s = str(s).strip()
        try:
            # Try ISO with optional time
            return datetime.fromisoformat(s.replace(" ", "T"))
        except Exception:
            pass
        # Try common formats
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(s[:10], fmt)
            except Exception:
                continue
        return None

    rows_sorted = sorted(
        rows,
        key=lambda rec: (
            _parse_date(rec.get("submitted_at")) or datetime.min,
            str(rec.get("protocol_number") or ""),
        ),
    )

    # Title row
    ws.write(0, 0, title, header_style)
    # Header row
    for c, h in enumerate(headers):
        ws.write(1, c, h, header_style)

    # Prepare column values for width calculation
    col_vals = [[], [], []]
    for rec in rows_sorted:
        col_vals[0].append(rec.get("directory", ""))
        col_vals[1].append(_format_protocol(rec))
        col_vals[2].append(rec.get("procedure", ""))

    # Compute and set column widths based on max content length (plus padding)
    # Excel width units: 256 per character.
    for idx in range(3):
        max_len = max([len(str(v)) for v in (col_vals[idx] + [headers[idx]])], default=len(headers[idx]))
        # Cap width to avoid excessively wide columns; add small padding
        width_chars = min(max_len + 2, 80)
        ws.col(idx).width = 256 * width_chars

    # Write data rows
    r = 2
    for i in range(len(rows_sorted)):
        ws.write(r, 0, col_vals[0][i], normal_style)
        ws.write(r, 1, col_vals[1][i], text_style)  # Use text format for protocol to preserve formatting
        ws.write(r, 2, col_vals[2][i], normal_style)
        r += 1


def build_requests_xls(digest: Dict, scope: str = "new", file_path: str | None = None) -> bytes | str:
    """Build an XLS with two sheets (test, real).

    scope:
      - "new": only today's new requests (incoming.real_new / incoming.test_new)
      - "all": all requests from the snapshot (classified via test_users)

    Returns bytes if file_path is None; else writes to file_path and returns the path.
    """
    if xlwt is None:
        raise ImportError("xlwt is not installed. Please 'pip install xlwt'.")

    incoming = digest.get("incoming", {})
    if scope == "all":
        try:
            from test_users import classify_records
            real_rows, test_rows = classify_records(incoming.get("records", []) or [])
        except Exception:
            # Fallback: treat all as real
            real_rows = incoming.get("records", []) or []
            test_rows = []
        title_test = "Δοκιμαστικές Αιτήσεις (Όλες)"
        title_real = "Πραγματικές Αιτήσεις (Όλες)"
    else:
        real_rows = incoming.get("real_new", []) or []
        test_rows = incoming.get("test_new", []) or []
        title_test = "Νέες Δοκιμαστικές Αιτήσεις"
        title_real = "Νέες Πραγματικές Αιτήσεις"

    wb = xlwt.Workbook()
    ws_test = wb.add_sheet("Δοκιμαστικές")
    ws_real = wb.add_sheet("Πραγματικές")

    _write_sheet(ws_test, test_rows, title_test)
    _write_sheet(ws_real, real_rows, title_real)

    if file_path:
        wb.save(file_path)
        return file_path

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
