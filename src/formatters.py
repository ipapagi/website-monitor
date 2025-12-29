"""Κοινές συναρτήσεις μορφοποίησης δεδομένων για εμφάνιση"""

import os
from typing import Dict

_TEXT_WIDTHS_CACHE: Dict[str, int] | None = None


def _get_text_max_widths() -> Dict[str, int]:
    """Φορτώνει τα max widths από το config (με caching).

    Κλειδιά: case_id, procedure, directory, party
    Τιμές:
    - >0: εφαρμόζεται truncation στο αντίστοιχο μήκος
    - <=0 ή None: δεν εφαρμόζεται περιορισμός (no limit)
    """
    global _TEXT_WIDTHS_CACHE
    # Runtime override via environment variable
    full_text_flag = os.getenv("PKM_FULL_TEXT", "").strip().lower()
    if full_text_flag in ("1", "true", "yes", "on"):
        return {"case_id": 0, "procedure": 0, "directory": 0, "party": 0}

    if _TEXT_WIDTHS_CACHE is not None:
        return _TEXT_WIDTHS_CACHE

    defaults = {"case_id": 15, "procedure": 60, "directory": 50, "party": 40}
    widths = {}
    try:
        from config import get_project_root
        from utils import load_config

        cfg_path = os.path.join(get_project_root(), "config", "config.yaml")
        cfg = load_config(cfg_path) or {}
        raw = (cfg.get("text_max_widths")
               or cfg.get("terminal_formatting", {}).get("text_max_widths")
               or {})
        for k, dv in defaults.items():
            val = raw.get(k, dv)
            if val is None:
                widths[k] = 0
            elif isinstance(val, str):
                if val.lower() in ("none", "unlimited", "no-limit", "nolimit"):
                    widths[k] = 0
                else:
                    try:
                        widths[k] = int(val)
                    except Exception:
                        widths[k] = dv
            else:
                try:
                    widths[k] = int(val)
                except Exception:
                    widths[k] = dv
    except Exception:
        widths = defaults.copy()

    _TEXT_WIDTHS_CACHE = widths
    return _TEXT_WIDTHS_CACHE


def _truncate(value: str, maxlen: int) -> str:
    if value is None:
        return ""
    if maxlen and maxlen > 0:
        return str(value)[:maxlen]
    return str(value)


def format_incoming_record_text(rec):
    """Μορφοποιεί ένα incoming record για text output (terminal)

    Διαβάζει widths από το config (text_max_widths). Αν κάποια τιμή είναι 0/None,
    δεν εφαρμόζεται περιορισμός για το αντίστοιχο πεδίο.
    """
    widths = _get_text_max_widths()

    case_id = rec.get("case_id", "")
    protocol = rec.get("protocol_number", "")
    date = rec.get("submitted_at", "")[:10]
    procedure = rec.get("procedure", "")
    directory = rec.get("directory", "")
    party = rec.get("party", "")
    doc_category = rec.get("document_category", "")

    lines = []
    lines.append(f"[{case_id}({protocol})] {date} - {doc_category}")
    lines.append(f"   📋 Διαδικασία: {procedure}")
    lines.append(f"   🏢 Δ/νση: {directory}")
    lines.append(f"   👤 Συναλλασσόμενος: {party}")
    return "\n".join(lines)


def format_incoming_record_html(rec, icon, escape_fn):
    """Μορφοποιεί ένα incoming record για HTML output (email)
    
    Args:
        rec: το record
        icon: το emoji/icon για την κατηγορία
        escape_fn: συνάρτηση για HTML escape (π.χ. html.escape)
    """
    esc = escape_fn
    case_id = esc(rec.get('case_id', ''))
    protocol = esc(rec.get('protocol_number', ''))
    submitted = esc(rec.get('submitted_at', '')[:10])
    procedure = esc(rec.get('procedure', ''))
    directory = esc(rec.get('directory', ''))
    party = esc(rec.get('party', ''))
    doc_category = esc(rec.get('document_category', ''))
    
    return f"""<div style='background: #fafafa; border-left: 4px solid #1976d2; margin: 8px 0; padding: 8px;'>
        <div style='margin: 3px 0; font-size: 12px;'>
            <strong>{icon} Υπόθεση {case_id}({protocol}) - {doc_category} │ {submitted}</strong>
        </div>
        <div style='margin: 3px 0; font-size: 11px;'><strong>📋 Διαδικασία:</strong> {procedure}</div>
        <div style='margin: 3px 0; font-size: 11px;'><strong>🏢 Δ/νση:</strong> {directory}</div>
        <div style='margin: 3px 0; font-size: 11px;'><strong>👤 Συναλλασσόμενος:</strong> {party}</div>
    </div>"""


def format_incoming_record_pdf(rec, icon):
    """Μορφοποιεί ένα incoming record για PDF output
    
    Επιστρέφει list από strings για Paragraph objects
    """
    case_id = rec.get('case_id', '')
    protocol = rec.get('protocol_number', '')
    submitted = rec.get('submitted_at', '')[:10]
    procedure = rec.get('procedure', '')
    directory = rec.get('directory', '')
    party = rec.get('party', '')
    doc_category = rec.get('document_category', '')
    
    return [
        f"<b>{icon} Υπόθεση {case_id}({protocol}) - {doc_category} │ {submitted}</b>",
        f"<b>📋 Διαδικασία:</b> {procedure}",
        f"<b>🏢 Δ/νση:</b> {directory}",
        f"<b>👤 Συναλλασσόμενος:</b> {party}"
    ]
