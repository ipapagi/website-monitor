"""Κοινές συναρτήσεις μορφοποίησης δεδομένων για εμφάνιση"""


def format_incoming_record_text(rec):
    """Μορφοποιεί ένα incoming record για text output (terminal)"""
    case_id = rec.get('case_id', '')[:15]
    protocol = rec.get('protocol_number', '')
    date = rec.get('submitted_at', '')[:10]
    procedure = rec.get('procedure', '')[:60]
    directory = rec.get('directory', '')[:50]
    party = rec.get('party', '')[:40]
    doc_category = rec.get('document_category', '')
    
    lines = []
    lines.append(f"[{case_id}({protocol})] {date} - {doc_category}")
    lines.append(f"   📋 Διαδικασία: {procedure}")
    lines.append(f"   🏢 Δ/νση: {directory}")
    lines.append(f"   👤 Συναλλασσόμενος: {party}")
    return '\n'.join(lines)


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
