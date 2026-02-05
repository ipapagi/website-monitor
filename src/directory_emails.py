"""Δημιουργία emails ανά Διεύθυνση με attachments για νέες αιτήσεις"""
import os
import sys
import json
import zipfile
import shutil
import html
import base64
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders, policy
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from incoming import load_incoming_snapshot, load_previous_incoming_snapshot, compare_incoming_records
from test_users import classify_records
from email_notifier import EmailNotifier
from utils import load_config
from config import get_project_root
from monitor import PKMMonitor
from directories_manager import get_directories_manager, find_email_for_request, find_email_for_directory


def _format_protocol_number(case_id: str, protocol_number: str, submitted_at: str) -> str:
    """Μορφοποιεί τον αριθμό πρωτοκόλλου ως 'Μεγάλος Αριθμός(Μικρός Αριθμός)/ΗΜ.ΠΡΩΤΟΚΟΛΛΟΥ'"""
    try:
        # Αναμένεται format: case_id(protocol_number)/YYYY-MM-DD ή similar
        if '/' in protocol_number:
            return protocol_number
        # Δημιουργία format
        dt = datetime.fromisoformat(submitted_at.replace(' ', 'T')) if '-' in submitted_at else None
        date_str = dt.strftime("%d-%m-%Y") if dt else ""
        return f"{case_id}({protocol_number})/{date_str}"
    except Exception:
        return f"{case_id}/{protocol_number}" if protocol_number else str(case_id)


def _decode_rfc2231_filename(filename_header: str) -> str:
    """Αποκωδικοποιεί RFC 2231 encoded filename (Base64 UTF-8)
    
    Παράδειγμα: =?UTF-8?B?zpXOmc6jIDIwMjYtODY0NDUgLSD...?=
    """
    if not filename_header or '?=' not in filename_header:
        return filename_header
    
    try:
        # Pattern: =?charset?encoding?encoded_text?=
        match = re.match(r'=\?([^?]+)\?([^?]+)\?([^?]+)\?=', filename_header)
        if not match:
            return filename_header
        
        charset, encoding, encoded_text = match.groups()
        
        if encoding.upper() == 'B':  # Base64
            decoded_bytes = base64.b64decode(encoded_text)
            return decoded_bytes.decode(charset, errors='replace')
    except Exception:
        pass
    
    return filename_header


def _extract_filename_from_header(content_disposition: str) -> str:
    """Εξαγάγει το όνομα αρχείου από Content-Disposition header"""
    if not content_disposition:
        return None
    
    # Ψάξε για filename* (RFC 2231) ή filename
    match = re.search(r"filename\*=([^;]+)", content_disposition)
    if match:
        filename = match.group(1).strip().strip('"').strip("'")
        return _decode_rfc2231_filename(filename)
    
    match = re.search(r'filename=([^;]+)', content_disposition)
    if match:
        filename = match.group(1).strip().strip('"').strip("'")
        return _decode_rfc2231_filename(filename)
    
    return None


def _sanitize_filename(name: str) -> str:
    """Κάνει safe το όνομα αρχείου αφαιρώντας ειδικούς χαρακτήρες"""
    # Αφαίρεση newlines, carriage returns και άλλων whitespace χαρακτήρων
    name = re.sub(r'[\n\r\t]', '', name)
    # Αφαίρεση των χαρακτήρων που δεν επιτρέπονται στο Windows/Unix
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()


def _get_attachment_list(monitor: PKMMonitor, doc_id: str) -> List[Dict]:
    """Ανακτά τη λίστα attachments για μια αίτηση
    
    Returns:
        List of dicts with 'id', 'filename', 'description', 'extension'
    """
    session = getattr(monitor, 'session', None)
    base_url = getattr(monitor, 'base_url', '')
    jwt_token = getattr(monitor, 'jwt_token', None)
    main_page_url = getattr(monitor, 'main_page_url', '')
    
    if not session or not base_url or not doc_id:
        return []
    
    url = base_url.rstrip('/') + f"/services/AttachmentServices/getAllDocumentAttachmentsSimple?docId={doc_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Accept': '*/*',
        'Accept-Language': 'el',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': main_page_url or base_url,
    }
    if jwt_token:
        headers['Authorization'] = f'Bearer {jwt_token}'
    
    try:
        response = session.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        payload = response.json()
        
        if payload.get('success') and payload.get('data'):
            return payload['data']
    except Exception as exc:
        print(f"⚠️  Αποτυχία ανάκτησης attachments για DOCID {doc_id}: {exc}")
    
    return []


def _download_single_document(monitor: PKMMonitor, doc_id: str, output_path: str) -> Tuple[bool, str]:
    """Κατεβάζει ένα μεμονωμένο έγγραφο
    
    Args:
        monitor: PKMMonitor instance
        doc_id: ID του εγγράφου
        output_path: Πλήρης διαδρομή για αποθήκευση
    
    Returns:
        Tuple (success: bool, filename: str) - filename από Content-Disposition header
    """
    session = getattr(monitor, 'session', None)
    base_url = getattr(monitor, 'base_url', '')
    jwt_token = getattr(monitor, 'jwt_token', None)
    main_page_url = getattr(monitor, 'main_page_url', '')
    
    if not session or not base_url:
        return False, None
    
    url = base_url.rstrip('/') + f"/services/DocumentServices/getNativeDoc?docId={doc_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Accept': '*/*',
        'Accept-Language': 'el',
        'Referer': main_page_url or base_url,
    }
    if jwt_token:
        headers['Authorization'] = f'Bearer {jwt_token}'
    
    try:
        response = session.get(url, headers=headers, timeout=30, verify=False, stream=True)
        response.raise_for_status()
        
        # Εξαγωγή filename από Content-Disposition header
        content_disposition = response.headers.get('Content-Disposition', '')
        filename_from_header = _extract_filename_from_header(content_disposition)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True, filename_from_header
    except Exception as exc:
        print(f"⚠️  Αποτυχία download εγγράφου {doc_id}: {exc}")
        return False, None


def _download_bulk_documents(monitor: PKMMonitor, doc_ids: List[str], output_path: str) -> bool:
    """Κατεβάζει πολλαπλά έγγραφα σε ZIP
    
    Args:
        monitor: PKMMonitor instance
        doc_ids: List of document IDs
        output_path: Πλήρης διαδρομή για αποθήκευση ZIP
    
    Returns:
        True αν επιτυχία
    """
    session = getattr(monitor, 'session', None)
    base_url = getattr(monitor, 'base_url', '')
    jwt_token = getattr(monitor, 'jwt_token', None)
    main_page_url = getattr(monitor, 'main_page_url', '')
    
    if not session or not base_url or not doc_ids:
        return False
    
    doc_ids_str = ','.join(str(d) for d in doc_ids)
    url = base_url.rstrip('/') + f"/services/DocumentServices/getNativeDocsBulk?docIds={doc_ids_str}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Accept': '*/*',
        'Accept-Language': 'el',
        'Referer': main_page_url or base_url,
    }
    if jwt_token:
        headers['Authorization'] = f'Bearer {jwt_token}'
    
    try:
        response = session.get(url, headers=headers, timeout=60, verify=False, stream=True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as exc:
        print(f"⚠️  Αποτυχία bulk download: {exc}")
        return False


def _download_attachments(monitor: PKMMonitor, doc_id: str, party_name: str, output_dir: str = None) -> str:
    """Ανακτά όλα τα attachments και δημιουργεί ZIP με όνομα πολίτη
    
    Args:
        monitor: PKMMonitor instance
        doc_id: ID της αίτησης
        party_name: Όνομα πολίτη για το ZIP
        output_dir: Φάκελος εξόδου
    
    Returns:
        Διαδρομή ZIP ή κενό string αν αποτυχία
    """
    import shutil  # Import εδώ για χρήση στη συνάρτηση
    
    if output_dir is None:
        output_dir = os.path.join(get_project_root(), 'data', 'temp_attachments')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Δημιουργία φακέλου για προσωρινά downloads (με timestamp και random suffix για uniqueness)
    import random
    random_suffix = random.randint(10000, 99999)
    timestamp_unique = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    temp_download_dir = os.path.join(output_dir, f"temp_{doc_id}_{random_suffix}_{timestamp_unique}")
    os.makedirs(temp_download_dir, exist_ok=True)
    
    print(f"   📁 Προσωρινός φάκελος: {os.path.basename(temp_download_dir)}")
    
    downloaded_files = []
    
    # 1. Κατέβασμα κύριου εγγράφου (docId) χωριστά
    # Το όνομα παίρνεται από το Content-Disposition header
    main_doc_name = f"Application_Doc_{doc_id}.docx"  # Default name
    success, filename_from_header = _download_single_document(monitor, doc_id, os.path.join(temp_download_dir, main_doc_name))
    
    if success:
        if filename_from_header:
            # Χρήσιμοποίησε το όνομα από το header
            main_doc_name = _sanitize_filename(filename_from_header)
            # Μετακίνησε το αρχείο με το σωστό όνομα
            if main_doc_name != f"Application_Doc_{doc_id}.docx":
                temp_path = os.path.join(temp_download_dir, f"Application_Doc_{doc_id}.docx")
                new_path = os.path.join(temp_download_dir, main_doc_name)
                os.rename(temp_path, new_path)
        
        downloaded_files.append((os.path.join(temp_download_dir, main_doc_name), main_doc_name))
        print(f"   ✅ Κατέβηκε κύριο έγγραφο: {main_doc_name}")
    else:
        print(f"   ⚠️  Αποτυχία download κύριου εγγράφου (docId={doc_id})")
    
    # 2. Ανάκτηση και κατέβασμα attachments
    attachments = _get_attachment_list(monitor, doc_id)
    if not attachments:
        # Αν δεν υπάρχουν attachments, απλώς δημιουργούμε ZIP με το κύριο έγγραφο
        pass
    else:
        # Κατέβασμα όλων των attachments ως ZIP
        attachment_ids = [str(att['id']) for att in attachments]
        # Κατέβασμα όλων των attachments ως bulk ZIP
        bulk_zip_path = os.path.join(temp_download_dir, "attachments_bulk.zip")
        
        # Προετοιμασία ονομάτων/δεικτών για αποδεικτικό
        proof_keywords = ("Αποδεικτικό", "Πρωτοκόλλησης", "λήψης αιτήματος")
        proof_name_candidates = set()
        for att in attachments:
            decoded_desc = html.unescape(att.get('description', ''))
            decoded_filename = html.unescape(att.get('filename', ''))
            if any(k in decoded_desc for k in proof_keywords) or any(k in decoded_filename for k in proof_keywords):
                if decoded_filename:
                    proof_name_candidates.add(_sanitize_filename(decoded_filename))
    
        
        if _download_bulk_documents(monitor, attachment_ids, bulk_zip_path):
            print(f"   ✅ Κατέβηκαν {len(attachment_ids)} συνημμένα σε ZIP")
            
            # Εξαγωγή των αρχείων από το bulk ZIP
            try:
                # Άνοιγμα του ZIP με προσπάθεια για διάφορες κωδικοποιήσεις
                try:
                    # Δοκιμή με UTF-8
                    zf = zipfile.ZipFile(bulk_zip_path, 'r')
                except:
                    # Δοκιμή με CP437 (default)
                    zf = zipfile.ZipFile(bulk_zip_path, 'r', metadata_encoding='cp437')
                
                with zf:
                    print(f"      📦 Bulk ZIP περιέχει {len(zf.namelist())} αρχεία")
                    for member in zf.namelist():
                        print(f"      📄 Εξαγωγή: {member}")
                        
                        # Σανιτάρι το όνομα ακόμα πριν εξάγεται
                        raw_name = os.path.basename(member)
                        raw_name = html.unescape(raw_name)
                        raw_name = _sanitize_filename(raw_name)
                        
                        print(f"         → Καθαρό όνομα: {raw_name}")
                        
                        # Εξαγωγή ως προσωρινό όνομα, μετά μετονομασία
                        temp_filename = f"temp_{len(downloaded_files)}.bin"
                        extracted_path = zf.extract(member, temp_download_dir)
                        
                        # Καθορισμός final filename
                        safe_name = raw_name
                        base_name, ext = os.path.splitext(safe_name)
                        
                        # Μετονομασία αποδεικτικού αίτησης με αριθμό
                        is_proof = (
                            safe_name in proof_name_candidates
                            or any(k in base_name for k in proof_keywords)
                            or (
                                ext.lower() == '.docx'
                                and 'Αίτηση' in base_name
                                and 'ΕΙΣ' not in base_name
                            )
                        )
                        if is_proof:
                            safe_name = f"Αποδεικτικό Αίτησης {doc_id}{ext or '.docx'}"
                            print(f"         → Ανιχνεύτηκε αποδεικτικό, μετονομασία σε: {safe_name}")
                        
                        # Μετακίνηση του αρχείου με σωστό όνομα
                        final_path = os.path.join(temp_download_dir, safe_name)
                        try:
                            os.rename(extracted_path, final_path)
                            downloaded_files.append((final_path, safe_name))
                            print(f"         ✅ Αποθηκεύτηκε ως: {safe_name}")
                        except Exception as rename_err:
                            # Αν αποτύχει η μετακίνηση, χρησιμοποιήστε το extracted path
                            print(f"         ⚠️  Σφάλμα μετονομασίας: {rename_err}, χρήση original path")
                            downloaded_files.append((extracted_path, safe_name))
                
                # Διαγραφή του προσωρινού bulk ZIP
                os.remove(bulk_zip_path)
            except Exception as exc:
                print(f"   ⚠️  Αποτυχία εξαγωγής bulk ZIP: {exc}")
        else:
            print(f"   ⚠️  Αποτυχία bulk download συνημμένων")
    
    # Δημιουργία τελικού ZIP με όνομα πολίτη
    if not downloaded_files:
        print(f"   ⚠️  Δεν κατέβηκαν αρχεία για DOCID {doc_id}")
        return ""
    
    safe_party_name = _sanitize_filename(party_name) or f"aitisi_{doc_id}"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    final_zip_name = f"{safe_party_name}_{timestamp}.zip"
    final_zip_path = os.path.join(output_dir, final_zip_name)
    
    print(f"   🔧 Δημιουργία ZIP: {final_zip_name}")
    print(f"      Αρχεία προς συμπίεση: {len(downloaded_files)}")
    
    try:
        # Δημιουργία ZIP με direct zipfile module (όχι shutil) για καλύτερο έλεγχο
        with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx, (file_path, archive_name) in enumerate(downloaded_files, 1):
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    
                    # Κοντύνουμε το όνομα αν είναι πολύ μεγάλο (πάνω από 200 χαρακτήρες)
                    if len(archive_name) > 100:
                        base, ext = os.path.splitext(archive_name)
                        # Κρατούμε πρώτα και τελευταία 80 χαρακτήρα
                        archive_name = base[:40] + "..." + base[-40:] + ext
                    
                    print(f"      [{idx}/{len(downloaded_files)}] Προσθήκη: {archive_name} ({file_size} bytes)")
                    
                    # Διαβάζουμε το αρχείο και το γράφουμε στο ZIP με σωστό encoding
                    with open(file_path, 'rb') as f:
                        zf.writestr(archive_name, f.read(), compress_type=zipfile.ZIP_DEFLATED)
                else:
                    print(f"      ⚠️  Αρχείο δεν υπάρχει: {file_path}")
        
        # Έλεγχος ότι το ZIP δημιουργήθηκε
        if os.path.exists(final_zip_path):
            zip_size = os.path.getsize(final_zip_path)
            print(f"   ✅ ZIP δημιουργήθηκε: {final_zip_name} ({zip_size} bytes)")
            
            # Επαλήθευση
            try:
                with zipfile.ZipFile(final_zip_path, 'r') as test_zf:
                    bad_file = test_zf.testzip()
                    if bad_file:
                        print(f"   ⚠️  Κατεστραμμένο αρχείο: {bad_file}")
                    else:
                        print(f"   ✅ ZIP επαληθεύτηκε ({len(test_zf.namelist())} αρχεία)")
            except Exception as e:
                print(f"   ⚠️  Αδυναμία ελέγχου ZIP: {e}")
        else:
            raise Exception("ZIP file was not created")
            
    except Exception as exc:
        print(f"   ❌ Αποτυχία δημιουργίας ZIP: {exc}")
        import traceback
        traceback.print_exc()
        return ""
    finally:
        # Καθαρισμός προσωρινών αρχείων - aggressive cleanup
        try:
            if os.path.exists(temp_download_dir):
                shutil.rmtree(temp_download_dir, ignore_errors=True)
                print(f"   🧹 Διαγραφή προσωρινού φακέλου")
        except Exception as cleanup_err:
            print(f"   ⚠️  Σφάλμα στη διαγραφή: {cleanup_err}")
    
    return final_zip_path


def _save_eml_file(msg: MIMEMultipart, directory: str, date_from: str = None, date_to: str = None, output_dir: str | None = None) -> str:
    """Αποθηκεύει το email σε .eml αρχείο και επιστρέφει τη διαδρομή.
    
    Args:
        msg: Email message
        directory: Όνομα διεύθυνσης
        date_from: Ημερομηνία έναρξης range (YYYY-MM-DD)
        date_to: Ημερομηνία λήξης range (YYYY-MM-DD)
        output_dir: Φάκελος εξόδου
    """
    if output_dir is None:
        output_dir = os.path.join(get_project_root(), 'data', 'prepare_eml_files')

    os.makedirs(output_dir, exist_ok=True)

    safe_directory = _sanitize_filename(directory) or 'directory'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Προσθήκη date range στο filename αν υπάρχει
    if date_from and date_to:
        date_from_str = date_from.replace('-', '')
        date_to_str = date_to.replace('-', '')
        eml_filename = f"{safe_directory}_{date_from_str}_to_{date_to_str}_{timestamp}.eml"
    else:
        eml_filename = f"{safe_directory}_{timestamp}.eml"
    
    eml_path = os.path.join(output_dir, eml_filename)

    with open(eml_path, 'wb') as f:
        f.write(msg.as_bytes(policy=policy.default))

    return eml_path


def create_directory_eml(records: List[Dict], directory: str, party_names: List[str]) -> MIMEMultipart:
    """Δημιουργεί email σε MIMEMultipart format για ένα σύνολο αιτήσεων ανά Διεύθυνση
    
    Args:
        records: Λίστα νέων αιτήσεων
        directory: Ονομασία Διεύθυνσης
        party_names: Ονόματα αιτούντων (για το όνομα zip)
    
    Returns:
        MIMEMultipart email object
    """
    msg = MIMEMultipart('mixed')
    msg['Subject'] = f"Νέες αιτήσεις στο ΣΗΔΕ - {directory}"
    msg['From'] = os.getenv('EMAIL_ADDRESS', 'system@example.com')
    
    # HTML body με τις λεπτομέρειες αιτήσεων
    html_parts = [
        "<html><body style='font-family: Arial, sans-serif; direction: ltr; text-align: justify; text-justify: inter-word;'>",
        "<p>Καλημέρα σας,</p>",
        "<p>Σας ενημερώνουμε ότι στο Σύστημα Ηλεκτρονικής Διακίνησης Εγγράφων (ΣΗΔΕ) έχουν υποβληθεί νέες αιτήσεις για τη Διεύθυνσή σας.</p>",
        "<br><hr style='border: none; border-top: 1px solid #ccc;'><br>"
    ]
    
    for i, rec in enumerate(records, 1):
        procedure_name = rec.get('procedure', 'Άγνωστη Διαδικασία')
        submitted_at = rec.get('submitted_at', '')
        protocol = _format_protocol_number(
            rec.get('case_id', ''),
            rec.get('protocol_number', ''),
            submitted_at
        )
        party = rec.get('party', 'Άγνωστος/η')
        
        html_parts.append(f"<h3>Αίτηση {i}</h3>")
        html_parts.append(f"<p><strong>Ονομασία Ψηφιακής Υπηρεσίας:</strong> {procedure_name}</p>")
        html_parts.append(f"<p><strong>Ημερομηνία Υποβολής:</strong> {submitted_at}</p>")
        html_parts.append(f"<p><strong>Αριθμός Πρωτοκόλλου:</strong> {protocol}</p>")
        html_parts.append(f"<p><strong>Διεύθυνση Υπηρεσίας:</strong> {directory}</p>")
        html_parts.append(f"<p><strong>Ονοματεπώνυμο Αιτούντος:</strong> {party}</p>")
        html_parts.append("<br><hr style='border: none; border-top: 1px solid #ccc;'><br>")
    
    html_parts.extend([
        "<p>Σας επισυνάπτουμε όλες τις αιτήσεις καθώς και τα δικαιολογητικά που έχουν υποβληθεί.</p>",
        "<p>Παρακαλούμε για τις δικές σας ενέργειες.</p>",
        "<br><p>Για οποιαδήποτε διευκρίνιση, είμαστε στη διάθεσή σας.</p>",
        "<p>Με εκτίμηση,<br/>Σύστημα ΣΗΔΕ</p>",
        "</body></html>"
    ])
    
    html_body = "\n".join(html_parts)
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    
    return msg


def create_zip_with_attachments(records: List[Dict], monitor: PKMMonitor = None, output_dir: str = None) -> List[str]:
    """Δημιουργεί ξεχωριστά ZIP αρχεία για κάθε αίτηση με όνομα βάσει του αριθμού αίτησης
    
    Για κάθε αίτηση (numbered Αίτηση 1, 2, 3...):
    - Κατεβάζει το κύριο έγγραφο
    - Κατεβάζει όλα τα συνημμένα
    - Τα συνδυάζει σε ένα ZIP με όνομα: Αίτηση_<number>_<party_name>.zip
    
    Args:
        records: Λίστα αιτήσεων
        monitor: PKMMonitor instance (για downloads)
        output_dir: Φάκελος εξόδου (default: temp directory)
    
    Returns:
        Λίστα διαδρομών ZIP αρχείων (μία για κάθε αίτηση)
    """
    if output_dir is None:
        output_dir = os.path.join(get_project_root(), 'data', 'temp_attachments')
    
    os.makedirs(output_dir, exist_ok=True)
    
    zip_paths = []
    
    # Δημιουργία ξεχωριστού ZIP για κάθε αίτηση
    if monitor and records:
        for idx, rec in enumerate(records, 1):  # 1-indexed (Αίτηση 1, 2, 3...)
            doc_id = rec.get('doc_id')
            party_name = _sanitize_filename(rec.get('party', 'aitisi'))
            
            if doc_id:
                # Όνομα ZIP με τον αριθμό αίτησης
                aitisi_name = f"Αίτηση_{idx}"
                zip_filename = f"{aitisi_name}_{party_name}"
                
                print(f"   📥 Κατέβασμα attachments για {aitisi_name} ({party_name}, DOCID: {doc_id})...")
                zip_path = _download_attachments(monitor, doc_id, zip_filename, output_dir)
                if zip_path:
                    zip_paths.append(zip_path)
                    print(f"   ✅ Δημιουργήθηκε: {os.path.basename(zip_path)}")
                else:
                    print(f"   ⚠️  Αποτυχία download για {aitisi_name}")
    
    return zip_paths
    
    return zip_paths


def attach_zips_to_email(msg: MIMEMultipart, zip_paths: List[str]) -> None:
    """Επισυνάπτει πολλαπλά zip αρχεία στο email
    
    Args:
        msg: Email message
        zip_paths: Λίστα διαδρομών ZIP αρχείων
    """
    for zip_path in zip_paths:
        if not os.path.exists(zip_path):
            continue
        
        part = MIMEBase('application', 'octet-stream')
        with open(zip_path, 'rb') as attachment:
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(zip_path)}"')
        msg.attach(part)


def group_new_requests_by_directory(records: List[Dict]) -> Dict[str, List[Dict]]:
    """Ομαδοποιεί νέες αιτήσεις ανά Διεύθυνση
    
    Args:
        records: Λίστα αιτήσεων
    
    Returns:
        Dict με κλειδί: directory name, value: λίστα αιτήσεων
    """
    grouped = {}
    for rec in records:
        directory = rec.get('directory', 'Άγνωστη Διεύθυνση')
        if directory not in grouped:
            grouped[directory] = []
        grouped[directory].append(rec)
    return grouped


def send_directory_emails(send_to_chat: bool = False, config_path: str | None = None, test_date: str | None = None) -> bool:
    """Δημιουργεί και αποστέλνει emails ανά Διεύθυνση με attachments
    
    Args:
        send_to_chat: Αν True, αποστέλνει και στο chat group υποστήριξης
        config_path: Διαδρομή config file
        test_date: Ημερομηνία δοκιμής (format: YYYY-MM-DD) για ανάκτηση αιτήσεων από παλιότερα snapshots
    
    Returns:
        True αν επιτυχής
    """
    from daily_report import build_daily_digest
    
    try:
        digest = build_daily_digest(config_path, target_date=test_date)
        incoming = digest.get('incoming', {})
        
        # Ανάκτηση date range από digest
        date_from = incoming.get('date')  # Η ημερομηνία του snapshot
        reference_date = incoming.get('reference_date')  # Το προηγούμενο snapshot
        
        # Ανάκτηση νέων αιτήσεων (μόνο πραγματικές)
        all_new = incoming.get('real_new', [])
        
        if not all_new:
            print("ℹ️  Δεν υπάρχουν νέες αιτήσεις για αποστολή")
            return True
        
        # Ομαδοποίηση ανά Διεύθυνση
        grouped = group_new_requests_by_directory(all_new)
        
        notifier = EmailNotifier()
        send_enabled = notifier.is_enabled()
        if not send_enabled:
            print("⚠️  Email notifications είναι απενεργοποιημένα — θα δημιουργηθούν μόνο .eml αρχεία")
        
        # Δημιουργία monitor για downloads (με login)
        monitor = None
        try:
            from config import get_project_root
            if config_path is None:
                config_path = os.path.join(get_project_root(), 'config', 'config.yaml')
            
            config = load_config(config_path)
            monitor = PKMMonitor(
                base_url=config.get("base_url", "https://shde.pkm.gov.gr"),
                urls=config.get("urls", {}),
                api_params=config.get("api_params", {}),
                login_params=config.get("login_params", {}),
                check_interval=config.get("check_interval", 300),
                username=config.get("username"),
                password=config.get("password"),
                session_cookies=config.get("session_cookies"),
            )
            if monitor.login():
                print("✅ Σύνδεση επιτυχής για download attachments")
            else:
                print("⚠️  Αποτυχία σύνδεσης - τα attachments δεν θα κατέβουν")
                monitor = None
        except Exception as exc:
            print(f"⚠️  Αποτυχία δημιουργίας monitor: {exc}")
            import traceback
            traceback.print_exc()
            monitor = None
        
        sent_count = 0
        
        for directory, records in grouped.items():
            print(f"\n📧 Δημιουργία email για Διεύθυνση: {directory}")
            print(f"   Αιτήσεις: {len(records)}")
            
            # Δημιουργία email
            msg = create_directory_eml(records, directory, 
                                      [r.get('party', '') for r in records])
            
            # Δημιουργία ZIPs με attachments (ένα ανά αίτηση με τον αριθμό της)
            print(f"   📦 Κλήση create_zip_with_attachments για {len(records)} αιτήσεις...")
            zip_paths = create_zip_with_attachments(records, monitor)
            print(f"   📦 Επιστράφηκαν {len(zip_paths)} ZIPs: {[os.path.basename(z) for z in zip_paths]}")
            
            if zip_paths:
                attach_zips_to_email(msg, zip_paths)
                print(f"   📎 Προστέθηκαν {len(zip_paths)} attachments στο email")
            else:
                print(f"   ⚠️  Δεν υπάρχουν ZIPs για προσθήκη στο email!")
            
            # Εύρεση email - προσπαθούμε πολλές μεθόδους
            recipient_email = None
            source = None
            
            # Μέθοδος 1: Αναζήτηση από τη διαμόρφωση (directories_config.json)
            # Χρησιμοποιούμε το πρώτο record για να βρούμε τη Π.Ε.
            if records:
                email_tuple = find_email_for_request(records[0])
                if email_tuple:
                    recipient_email, source = email_tuple
                    print(f"   ℹ️  Email βρέθηκε από {source}")
            
            # Μέθοδος 2: Fallback σε περιβάλλον μεταβλητές
            if not recipient_email:
                recipient_email = os.getenv(f"DIRECTORY_EMAIL_{directory}", None)
                if recipient_email:
                    source = "environment"
                    print(f"   ℹ️  Email βρέθηκε από περιβάλλον μεταβλητή")
            
            # Μέθοδος 3: Αναζήτηση στη διαμόρφωση με όνομα Διεύθυνσης
            if not recipient_email:
                email = find_email_for_directory(directory)
                if email:
                    recipient_email = email
                    source = "directory_config"
                    print(f"   ℹ️  Email βρέθηκε από διαμόρφωση Διεύθυνσης")
            
            if not recipient_email:
                print(f"   ⚠️  Δεν βρέθηκε email για τη Διεύθυνση '{directory}'")
                print(f"   💡 Συμπληρώστε το αρχείο data/directories_config.json ή ορίστε DIRECTORY_EMAIL_{directory}")
                continue
            
            # Αποστολή email
            msg['To'] = recipient_email
            eml_path = _save_eml_file(msg, directory, date_from=reference_date, date_to=date_from)
            print(f"   📝 Αποθηκεύτηκε .eml: {eml_path}")
            if send_enabled:
                if notifier.send_email_message(msg):
                    print(f"   ✅ Email εστάλη στο {recipient_email}")
                    sent_count += 1
                else:
                    print(f"   ❌ Αποτυχία αποστολής email στο {recipient_email}")
            else:
                print(f"   🚫 Παράλειψη αποστολής (notifications disabled) προς {recipient_email}")
            
            # Αν ζητήθηκε, αποστολή και στο chat group υποστήριξης
            if send_to_chat:
                print(f"   📱 Αποστολή σύνοψης στο chat υποστήριξης...")
                # TODO: Προσθήκη logic για αποστολή στο Teams/chat
                print(f"   ℹ️  Chat notification: {len(records)} νέες αιτήσεις για {directory}")
        
        if send_enabled:
            print(f"\n✅ Εστάλησαν {sent_count} emails")
            return sent_count > 0

        print("\n✅ Ολοκληρώθηκε η δημιουργία .eml χωρίς αποστολή")
        return True
    
    except Exception as e:
        print(f"❌ Σφάλμα κατά τη δημιουργία/αποστολή emails: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    from datetime import datetime, timedelta
    
    send_to_chat = '--chat' in sys.argv
    test_date = None
    
    # Ψάξε για παράμετρο --date=YYYY-MM-DD
    for arg in sys.argv[1:]:
        if arg.startswith('--date='):
            test_date = arg.split('=')[1]
            try:
                datetime.strptime(test_date, '%Y-%m-%d')
                print(f"🗓️  Δοκιμή με ημερομηνία: {test_date}")
            except ValueError:
                print(f"❌ Λάθος format ημερομηνίας. Χρησιμοποιήστε: --date=YYYY-MM-DD")
                sys.exit(1)
    
    send_directory_emails(send_to_chat=send_to_chat, test_date=test_date)
