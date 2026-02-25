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


def _is_department_assignment(employee_name: str) -> bool:
    """Check if employee_name is a department assignment (not a person).
    
    Returns True for departments, teams (προϊστάμενοι), etc.
    """
    if not employee_name:
        return False
    
    dept_keywords = ['ΤΜΗΜΑ', 'ΔΙΕΥΘΥΝΣΗ', 'Προϊστάμενοι']
    name_upper = str(employee_name).upper()
    return any(keyword in name_upper for keyword in dept_keywords)


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


def _write_sheet(ws, rows: List[Dict], title: str, settled_by_case_id: Dict = None):
    """Write sheet with incoming requests.
    
    Columns: Α/Α, Δ/νση, Αρ. Πρωτοκόλλου, ΤΥΠΟΣ, Διαδικασία, Συναλλασσόμενος, Ανάθεση σε, Διεκπεραιωμένη
    """
    if settled_by_case_id is None:
        settled_by_case_id = {}
    
    headers = ["Α/Α", "Δ/νση", "Αρ. Πρωτοκόλλου", "ΤΥΠΟΣ", "Διαδικασία", "Συναλλασσόμενος", "Ανάθεση σε", "Διεκπεραιωμένη"]

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

    # Title row (row 1)
    title_cell = ws.cell(row=1, column=1, value=title)
    if header_font:
        title_cell.font = header_font

    # Header row (row 2)
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=c, value=h)
        if header_font:
            cell.font = header_font
        if header_fill:
            cell.fill = header_fill

    # Data: 8 columns
    col_vals = [[], [], [], [], [], [], [], []]
    
    for idx, rec in enumerate(rows_sorted, start=1):
        # Ανάθεση σε (charge) - Priority: settled case charge > current incoming charge
        charge_info = rec.get("_charge", {})
        employee = charge_info.get("employee", "") if charge_info.get("charged") else ""
        
        # Check if case is in settled cases (queryId=19) - use its assignment
        case_id = str(rec.get("case_id", "")).strip()
        submission_year = str(rec.get("submission_year", "")).strip()
        assigned_employee = ""
        settled_date = ""
        
        # Try to match using YEAR/CASE_ID format (matches W001_P_FLD2 from settled cases)
        if submission_year and case_id:
            lookup_key = f"{submission_year}/{case_id}"
            if lookup_key in settled_by_case_id:
                settled_info = settled_by_case_id[lookup_key]
                settled_date = settled_info.get("settled_date", "")
                assigned_employee = settled_info.get("assigned_employee", "")
        
        # Priority: Use assignment from settled cases (W001_P_FLD10), else use incoming charge
        if assigned_employee:
            employee = assigned_employee
        elif employee and _is_department_assignment(employee):
            # Filter out department assignments - only show personal assignments
            employee = ""  # Clear department assignment - only show personal ones
        
        col_vals[0].append(idx)  # Α/Α
        col_vals[1].append(rec.get("directory", ""))
        col_vals[2].append(_format_protocol(rec))
        
        # ΤΥΠΟΣ (column 4) - show related case if this is a supplement
        doc_type = rec.get("document_category", "")
        related_case = (rec.get("related_case") or "").strip()
        if "Συμπληρωματι" in str(doc_type) and related_case:
            # Extract year/number from related_case
            # Format could be: "2026/117648" or "Αίτημα 2026/117648 NAME-123456"
            # We need to extract just "2026/117648"
            import re
            match = re.search(r'(\d{4}/\d+)', related_case)
            if match:
                case_number = match.group(1)
                doc_type = f"{doc_type}: {case_number}"
        
        col_vals[3].append(doc_type)
        col_vals[4].append(rec.get("procedure", ""))
        col_vals[5].append(rec.get("party", ""))
        col_vals[6].append(employee)  # Assignment from settled cases or current charge
        
        # Fallback: try protocol_number if available
        if not settled_date:
            protocol_num = str(rec.get("protocol_number", "")).strip()
            if protocol_num and protocol_num in settled_by_case_id:
                settled_date = settled_by_case_id[protocol_num].get("settled_date", "")
        
        col_vals[7].append(settled_date)

    # Column widths
    col_widths = [6, 100, 40, 42, 120, 60, 50, 25]  # Α/Α, Δ/νση, Protocol, ΤΥΠΟΣ, Διαδικασία, Party, Employee, Settled
    for idx in range(8):
        col_letter = chr(ord("A") + idx)
        ws.column_dimensions[col_letter].width = col_widths[idx]

    # Write data rows starting from row 3
    r = 3
    for i in range(len(rows_sorted)):
        for col_idx in range(8):
            ws.cell(row=r, column=col_idx + 1, value=col_vals[col_idx][i])
        r += 1
    
    # Freeze panes: freeze first 2 rows (title and header)
    ws.freeze_panes = "A3"


def build_requests_xls(digest: Dict, scope: str = "new", file_path: str | None = None, monitor_instance = None) -> bytes | str:
    """Build an XLSX with two sheets (test, real).

    scope:
      - "new": only today's new requests (incoming.real_new / incoming.test_new)
      - "all": all requests from the snapshot (classified via test_users)
    
    monitor_instance: optional pre-authenticated PKMMonitor for loading settled cases

    Returns bytes if file_path is None; else writes to file_path and returns the path.
    """
    if Workbook is None:
        raise ImportError("openpyxl is not installed. Please 'pip install openpyxl'.")

    # Load settled cases for cross-reference
    settled_by_case_id = _load_settled_cases(monitor_instance=monitor_instance)

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

    _write_sheet(ws_test, test_rows, title_test, settled_by_case_id)
    _write_sheet(ws_real, real_rows, title_real, settled_by_case_id)

    if file_path:
        wb.save(file_path)
        return file_path

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def _load_settled_cases(monitor_instance = None) -> Dict:
    """Load settled cases from queryId=19 using existing authenticated session.
    
    Args:
        monitor_instance: pre-authenticated PKMMonitor instance. If None, returns empty dict.
    
    Returns dict: {W001_P_FLD2: {'settled_date': 'DD-MM-YYYY', ...}, ...}
    """
    try:
        if monitor_instance is None:
            print("[DEBUG] No monitor instance provided for settled cases")
            return {}
        
        monitor = monitor_instance
        
        print("[DEBUG] Loaded settled cases from queryId=19")
        
        # Fetch settled cases (queryId=19)
        settled_params = {
            'isPoll': 'false',
            'queryId': '19',
            'queryOwner': '2',
            'isCase': 'false',
            'stateId': 'welcomeGrid-45_dashboard0',
            'page': '1',
            'start': '0',
            'limit': '500'
        }
        
        data = monitor.fetch_data(settled_params)
        if not data or not data.get('success'):
            print("[DEBUG] Failed to fetch settled cases")
            return {}
        
        settled_by_case_id = {}
        for rec in data.get('data', []):
            # W001_P_FLD2 = protocol number (like "2026/124212")
            protocol_num = str(rec.get('W001_P_FLD2', '')).strip()
            settled_date = str(rec.get('W001_P_FLD3', '')).strip()
            assigned_employee = str(rec.get('W001_P_FLD10', '')).strip()  # Employee assigned (charged) to the case
            
            if protocol_num:
                # Map by the protocol number directly (e.g., "2026/124212")
                settled_by_case_id[protocol_num] = {
                    'settled_date': settled_date,
                    'assigned_employee': assigned_employee
                }
        
        print(f"[DEBUG] Loaded {len(settled_by_case_id)} settled cases")
        return settled_by_case_id
    except Exception as e:
        # Silently fail to avoid breaking the export if settled cases unavailable
        print(f"[DEBUG] Error loading settled cases: {e}")
        return {}
