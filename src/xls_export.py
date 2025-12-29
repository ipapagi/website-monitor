"""Excel export for new incoming requests (real and test)."""
from __future__ import annotations

import io
from datetime import datetime
from typing import Dict, List

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
except ImportError:  # pragma: no cover
    Workbook = None
    Font = None
    PatternFill = None


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

    header_font = Font(bold=True) if Font else None
    header_fill = PatternFill("solid", fgColor="DAE8FC") if PatternFill else None

    def _parse_date(s: str):
        if not s:
            return None
        s = str(s).strip()
        try:
            return datetime.fromisoformat(s.replace(" ", "T"))
        except Exception:
            pass
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

    title_cell = ws.cell(row=1, column=1, value=title)
    if header_font:
        title_cell.font = header_font

    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=c, value=h)
        if header_font:
            cell.font = header_font
        if header_fill:
            cell.fill = header_fill

    col_vals = [[], [], []]
    for rec in rows_sorted:
        col_vals[0].append(rec.get("directory", ""))
        col_vals[1].append(_format_protocol(rec))
        col_vals[2].append(rec.get("procedure", ""))

    for idx in range(3):
        max_len = max([len(str(v)) for v in (col_vals[idx] + [headers[idx]])], default=len(headers[idx]))
        width_chars = min(max_len + 2, 80)
        col_letter = chr(ord("A") + idx)
        ws.column_dimensions[col_letter].width = width_chars

    r = 3
    for i in range(len(rows_sorted)):
        ws.cell(row=r, column=1, value=col_vals[0][i])
        ws.cell(row=r, column=2, value=col_vals[1][i])
        ws.cell(row=r, column=3, value=col_vals[2][i])
        r += 1


def build_requests_xls(digest: Dict, scope: str = "new", file_path: str | None = None) -> bytes | str:
        """Build an XLSX with two sheets (test, real).

        scope:
            - "new": only today's new requests (incoming.real_new / incoming.test_new)
            - "all": all requests from the snapshot (classified via test_users)

        Returns bytes if file_path is None; else writes to file_path and returns the path.
        """
        if Workbook is None:
                raise ImportError("openpyxl is not installed. Please 'pip install openpyxl'.")

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

    wb = Workbook()
    ws_test = wb.active
    ws_test.title = "Δοκιμαστικές"
    ws_real = wb.create_sheet("Πραγματικές")

    _write_sheet(ws_test, test_rows, title_test)
    _write_sheet(ws_real, real_rows, title_real)

    if file_path:
        wb.save(file_path)
        return file_path

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
