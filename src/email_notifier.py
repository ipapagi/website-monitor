import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class EmailNotifier:
    def __init__(self, admins_file: str = None):
        """
        Initialize email notifier with SMTP configuration
        
        Args:
            admins_file: Path to JSON file containing admin emails
        """
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 465))
        self.use_tls = os.getenv("EMAIL_USE_TLS", "false").lower() == "true"
        
        # Resolve admins file path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_admins = os.path.join(base_dir, "data", "admins.json")
        configured_admins = admins_file or os.getenv("ADMINS_FILE", default_admins)
        self.admins_file = configured_admins if os.path.isabs(configured_admins) else os.path.join(base_dir, configured_admins)
        self.enabled = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "true").lower() == "true"
        
    def is_enabled(self) -> bool:
        """Check if email notifications are enabled"""
        return self.enabled and all([
            self.email_address,
            self.email_password,
            self.smtp_server,
            self.smtp_port
        ])
        
    def load_admins(self) -> List[Dict]:
        """Load admin emails from JSON file"""
        try:
            with open(self.admins_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("admins", [])
        except FileNotFoundError:
            print(f"Warning: admins file not found at {self.admins_file}")
            return []
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in admins file at {self.admins_file}")
            return []
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Send email to a single recipient
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML supported)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.is_enabled():
            print("Email notifications are disabled")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach HTML body
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Connect to SMTP server and send
            if self.use_tls:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(self.email_address, self.email_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.email_address, self.email_password)
                    server.send_message(msg)

            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def notify_error(self, website_name: str, error_message: str, url: str, timestamp: str = None):
        """
        Notify admins about website error - Comprehensive report format
        
        Args:
            website_name: Name of the website with error
            error_message: Error description
            url: Website URL
            timestamp: Time of error (optional)
        """
        if not self.is_enabled():
            return
            
        if timestamp is None:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        admins = self.load_admins()
        subject = f"Αναφορά Σφάλματος: {website_name}"
        
        # Categorize error type
        error_type = "Σφάλμα Σύνδεσης"
        if "timeout" in error_message.lower():
            error_type = "Λήξη Χρόνου Αναμονής"
        elif "status code" in error_message.lower():
            error_type = "Μη Αναμενόμενος Κωδικός Απόκρισης"
        elif "connection" in error_message.lower():
            error_type = "Αδυναμία Σύνδεσης"
        
        body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #d32f2f; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f5f5f5; }}
                    .section {{ background-color: white; margin: 15px 0; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .label {{ font-weight: bold; color: #555; display: inline-block; width: 150px; }}
                    .value {{ color: #000; }}
                    .error-box {{ background-color: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 15px 0; }}
                    .footer {{ text-align: center; color: #777; font-size: 12px; padding: 20px; }}
                    .status {{ display: inline-block; padding: 5px 15px; border-radius: 3px; background-color: #d32f2f; color: white; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>⚠️ ΑΝΑΦΟΡΑ ΣΦΑΛΜΑΤΟΣ ΣΥΣΤΗΜΑΤΟΣ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ</h2>
                </div>
                <div class="content">
                    <div class="section">
                        <h3>Περίληψη Συμβάντος</h3>
                        <p><span class="label">Κατάσταση:</span> <span class="status">ΕΚΤΟΣ ΛΕΙΤΟΥΡΓΙΑΣ</span></p>
                        <p><span class="label">Ιστότοπος:</span> <span class="value">{website_name}</span></p>
                        <p><span class="label">URL:</span> <span class="value">{url}</span></p>
                        <p><span class="label">Τύπος Σφάλματος:</span> <span class="value">{error_type}</span></p>
                        <p><span class="label">Ημερομηνία/Ώρα:</span> <span class="value">{timestamp}</span></p>
                    </div>
                    
                    <div class="section">
                        <h3>Λεπτομέρειες Σφάλματος</h3>
                        <div class="error-box">
                            {error_message}
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>Προτεινόμενες Ενέργειες</h3>
                        <ul>
                            <li>Έλεγχος διαθεσιμότητας διακομιστή</li>
                            <li>Επαλήθευση διαμόρφωσης δικτύου</li>
                            <li>Έλεγχος αρχείων καταγραφής (logs) του διακομιστή</li>
                            <li>Επικοινωνία με τεχνική υποστήριξη εάν το πρόβλημα επιμένει</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>Αυτό είναι ένα αυτοματοποιημένο μήνυμα από το Σύστημα Παρακολούθησης Ιστοτόπων</p>
                    <p>Περιφερειακή Ενότητα Μαγνησίας - Τμήμα Πληροφορικής</p>
                </div>
            </body>
        </html>
        """
        
        sent_count = 0
        for admin in admins:
            if admin.get("notify_on_error", True):
                if self.send_email(admin['email'], subject, body):
                    sent_count += 1
        
        print(f"Error notification sent to {sent_count} admin(s)")
    
    def notify_recovery(self, website_name: str, url: str, downtime_duration: Optional[str] = None, timestamp: str = None):
        """
        Notify admins about website recovery - Comprehensive report format
        
        Args:
            website_name: Name of the recovered website
            url: Website URL
            downtime_duration: Duration of downtime (optional)
            timestamp: Time of recovery (optional)
        """
        if not self.is_enabled():
            return
            
        if timestamp is None:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        admins = self.load_admins()
        subject = f"Αναφορά Αποκατάστασης: {website_name}"
        
        downtime_info = f"<p><span class='label'>Διάρκεια Διακοπής:</span> <span class='value'>{downtime_duration}</span></p>" if downtime_duration else ""
        
        body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #388e3c; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f5f5f5; }}
                    .section {{ background-color: white; margin: 15px 0; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .label {{ font-weight: bold; color: #555; display: inline-block; width: 150px; }}
                    .value {{ color: #000; }}
                    .success-box {{ background-color: #e8f5e9; border-left: 4px solid #388e3c; padding: 15px; margin: 15px 0; }}
                    .footer {{ text-align: center; color: #777; font-size: 12px; padding: 20px; }}
                    .status {{ display: inline-block; padding: 5px 15px; border-radius: 3px; background-color: #388e3c; color: white; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>✅ ΑΝΑΦΟΡΑ ΑΠΟΚΑΤΑΣΤΑΣΗΣ ΣΥΣΤΗΜΑΤΟΣ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ</h2>
                </div>
                <div class="content">
                    <div class="section">
                        <h3>Περίληψη Συμβάντος</h3>
                        <p><span class="label">Κατάσταση:</span> <span class="status">ΛΕΙΤΟΥΡΓΙΚΟ</span></p>
                        <p><span class="label">Ιστότοπος:</span> <span class="value">{website_name}</span></p>
                        <p><span class="label">URL:</span> <span class="value">{url}</span></p>
                        {downtime_info}
                        <p><span class="label">Ημερομηνία/Ώρα:</span> <span class="value">{timestamp}</span></p>
                    </div>
                    
                    <div class="section">
                        <h3>Κατάσταση Συστήματος</h3>
                        <div class="success-box">
                            Ο ιστότοπος έχει αποκατασταθεί και λειτουργεί κανονικά. Όλες οι υπηρεσίες είναι διαθέσιμες.
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>Επόμενα Βήματα</h3>
                        <ul>
                            <li>Το σύστημα παρακολούθησης συνεχίζει την κανονική λειτουργία</li>
                            <li>Συνιστάται έλεγχος των αρχείων καταγραφής για την αιτία της διακοπής</li>
                            <li>Εφαρμογή προληπτικών μέτρων εάν απαιτείται</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>Αυτό είναι ένα αυτοματοποιημένο μήνυμα από το Σύστημα Παρακολούθησης Ιστοτόπων</p>
                    <p>Περιφερειακή Ενότητα Μαγνησίας - Τμήμα Πληροφορικής</p>
                </div>
            </body>
        </html>
        """
        
        sent_count = 0
        for admin in admins:
            if admin.get("notify_on_recovery", True):
                if self.send_email(admin['email'], subject, body):
                    sent_count += 1
        
        print(f"Recovery notification sent to {sent_count} admin(s)")
    
    def send_daily_report(self, checks_performed: int, errors_count: int, websites_status: Dict):
        """
        Send daily summary report to admins
        
        Args:
            checks_performed: Total number of checks performed
            errors_count: Total number of errors detected
            websites_status: Dictionary with current status of all websites
        """
        if not self.is_enabled():
            return
            
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        admins = self.load_admins()
        subject = f"Ημερήσια Αναφορά Παρακολούθησης - {datetime.now().strftime('%d/%m/%Y')}"
        
        # Build websites status table
        status_rows = ""
        for name, is_up in websites_status.items():
            status_icon = "✅" if is_up else "❌"
            status_text = "Λειτουργικό" if is_up else "Εκτός Λειτουργίας"
            status_color = "#4caf50" if is_up else "#f44336"
            status_rows += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{status_icon} {name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; color: {status_color}; font-weight: bold;">{status_text}</td>
            </tr>
            """
        
        body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #1976d2; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f5f5f5; }}
                    .section {{ background-color: white; margin: 15px 0; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                    .stat-box {{ text-align: center; padding: 20px; background-color: #e3f2fd; border-radius: 5px; flex: 1; margin: 0 10px; }}
                    .stat-number {{ font-size: 36px; font-weight: bold; color: #1976d2; }}
                    .stat-label {{ color: #555; margin-top: 5px; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    th {{ background-color: #1976d2; color: white; padding: 12px; text-align: left; }}
                    .footer {{ text-align: center; color: #777; font-size: 12px; padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>📊 ΗΜΕΡΗΣΙΑ ΑΝΑΦΟΡΑ ΣΥΣΤΗΜΑΤΟΣ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ</h2>
                    <p>{datetime.now().strftime('%d/%m/%Y')}</p>
                </div>
                <div class="content">
                    <div class="section">
                        <h3>Στατιστικά Στοιχεία</h3>
                        <div class="stats">
                            <div class="stat-box">
                                <div class="stat-number">{checks_performed}</div>
                                <div class="stat-label">Συνολικοί Έλεγχοι</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-number">{errors_count}</div>
                                <div class="stat-label">Σφάλματα</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>Κατάσταση Ιστοτόπων</h3>
                        <table>
                            <tr>
                                <th>Ιστότοπος</th>
                                <th>Κατάσταση</th>
                            </tr>
                            {status_rows}
                        </table>
                    </div>
                </div>
                <div class="footer">
                    <p>Αυτό είναι ένα αυτοματοποιημένο μήνυμα από το Σύστημα Παρακολούθησης Ιστοτόπων</p>
                    <p>Περιφερειακή Ενότητα Μαγνησίας - Τμήμα Πληροφορικής</p>
                </div>
            </body>
        </html>
        """
        
        sent_count = 0
        for admin in admins:
            if self.send_email(admin['email'], subject, body):
                sent_count += 1
        
        print(f"Daily report sent to {sent_count} admin(s)")

    def send_daily_digest(self, digest: Dict) -> bool:
        """Στέλνει αναλυτικό ημερήσια αναφορά (διαδικασίες + εισερχόμενα)."""
        if not self.is_enabled():
            print("Email notifications are disabled")
            return False

        def esc(val):
            import html

            return html.escape(str(val)) if val is not None else ""

        def render_proc_rows(changes, label):
            rows = ""
            if not changes:
                return "<tr><td colspan='4'>—</td></tr>"
            for item in changes:
                proc = item.get('new', item) if isinstance(item, dict) and 'new' in item else item
                code = esc(proc.get('κωδικός', ''))
                title = esc(proc.get('τίτλος', ''))
                status = esc(proc.get('ενεργή', ''))
                rows += f"""
                <tr>
                    <td>{esc(label)}</td>
                    <td>{code}</td>
                    <td>{title}</td>
                    <td>{status}</td>
                </tr>
                """
            return rows or "<tr><td colspan='4'>—</td></tr>"

        def render_incoming_rows(records, icon):
            if not records:
                return "<tr><td colspan='5'>—</td></tr>"
            rows = ""
            for rec in records:
                rows += f"""
                <tr>
                    <td>{icon}</td>
                    <td>{esc(rec.get('case_id', ''))}</td>
                    <td>{esc(rec.get('submitted_at', '')[:16])}</td>
                    <td>{esc(rec.get('subject', ''))}</td>
                    <td>{esc(rec.get('party', ''))}</td>
                </tr>
                """
            return rows

        incoming = digest.get('incoming', {})
        incoming_changes = incoming.get('changes', {})
        active_changes = (digest.get('active') or {}).get('changes')
        all_changes = (digest.get('all') or {}).get('changes')

        def count_changes(changes, key):
            return len(changes.get(key, [])) if changes else 0

        stats_cards = {
            'active_total': digest.get('active', {}).get('total', 0),
            'all_total': digest.get('all', {}).get('total', 0),
            'active_new': count_changes(active_changes or {}, 'new'),
            'active_mod': count_changes(active_changes or {}, 'modified'),
            'all_new': count_changes(all_changes or {}, 'new'),
            'all_mod': count_changes(all_changes or {}, 'modified'),
            'incoming_total': incoming.get('stats', {}).get('total', 0),
            'incoming_real': incoming.get('stats', {}).get('real', 0),
            'incoming_test': incoming.get('stats', {}).get('test', 0),
            'incoming_removed': count_changes(incoming_changes or {}, 'removed'),
        }

        subject = f"Ημερήσια Αναφορά ΣΗΔΕ – {datetime.now().strftime('%d/%m/%Y')}"

        body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, sans-serif; color: #333; line-height: 1.6; }}
                    .header {{ background: linear-gradient(90deg, #0d47a1, #1976d2); color: #fff; padding: 20px; text-align: center; }}
                    .section {{ background: #fff; margin: 15px 0; padding: 15px; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
                    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
                    .card {{ background: #f5f7fb; border-radius: 6px; padding: 12px; text-align: center; }}
                    .card h4 {{ margin: 0; color: #555; font-size: 13px; }}
                    .card .num {{ font-size: 28px; font-weight: 700; color: #0d47a1; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                    th, td {{ border: 1px solid #e0e0e0; padding: 8px; text-align: left; font-size: 13px; }}
                    th {{ background: #f0f4ff; color: #0d47a1; }}
                    .pill {{ display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
                    .pill-green {{ background: #e8f5e9; color: #2e7d32; }}
                    .pill-red {{ background: #ffebee; color: #c62828; }}
                    .pill-blue {{ background: #e3f2fd; color: #1565c0; }}
                    .sub {{ color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>ΗΜΕΡΗΣΙΑ ΑΝΑΦΟΡΑ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ</h2>
                    <div>{esc(digest.get('generated_at', ''))} – {esc(digest.get('base_url', ''))}</div>
                </div>

                <div class="section">
                    <h3>Σύνοψη</h3>
                    <div class="cards">
                        <div class="card"><h4>Ενεργές διαδικασίες</h4><div class="num">{stats_cards['active_total']}</div></div>
                        <div class="card"><h4>Σύνολο διαδικασιών</h4><div class="num">{stats_cards['all_total']}</div></div>
                        <div class="card"><h4>Νέες ενεργές</h4><div class="num">{stats_cards['active_new']}</div></div>
                        <div class="card"><h4>Τροποποιήσεις ενεργών</h4><div class="num">{stats_cards['active_mod']}</div></div>
                        <div class="card"><h4>Νέες συνολικές</h4><div class="num">{stats_cards['all_new']}</div></div>
                        <div class="card"><h4>Τροποποιήσεις συνολικών</h4><div class="num">{stats_cards['all_mod']}</div></div>
                        <div class="card"><h4>Αιτήσεις (σύνολο)</h4><div class="num">{stats_cards['incoming_total']}</div></div>
                        <div class="card"><h4>Πραγματικές</h4><div class="num">{stats_cards['incoming_real']}</div></div>
                        <div class="card"><h4>Δοκιμαστικές</h4><div class="num">{stats_cards['incoming_test']}</div></div>
                        <div class="card"><h4>Αφαιρέθηκαν</h4><div class="num">{stats_cards['incoming_removed']}</div></div>
                    </div>
                </div>

                <div class="section">
                    <h3>Αλλαγές Ενεργών Διαδικασιών</h3>
                    <div class="sub">Baseline: {esc((digest.get('active') or {}).get('baseline_timestamp') or '—')}</div>
                    <table>
                        <tr><th>Τύπος</th><th>Κωδικός</th><th>Τίτλος</th><th>Ενεργή</th></tr>
                        {render_proc_rows((active_changes or {}).get('new', []), 'Νέα')}
                        {render_proc_rows((active_changes or {}).get('activated', []), 'Ενεργοποιήθηκαν')}
                        {render_proc_rows((active_changes or {}).get('deactivated', []), 'Απενεργοποιήθηκαν')}
                        {render_proc_rows((active_changes or {}).get('removed', []), 'Αφαιρέθηκαν')}
                        {render_proc_rows((active_changes or {}).get('modified', []), 'Τροποποιήθηκαν')}
                    </table>
                </div>

                <div class="section">
                    <h3>Αλλαγές Συνόλου Διαδικασιών</h3>
                    <div class="sub">Baseline: {esc((digest.get('all') or {}).get('baseline_timestamp') or '—')}</div>
                    <table>
                        <tr><th>Τύπος</th><th>Κωδικός</th><th>Τίτλος</th><th>Ενεργή</th></tr>
                        {render_proc_rows((all_changes or {}).get('new', []), 'Νέες')}
                        {render_proc_rows((all_changes or {}).get('activated', []), 'Ενεργοποιήθηκαν')}
                        {render_proc_rows((all_changes or {}).get('deactivated', []), 'Απενεργοποιήθηκαν')}
                        {render_proc_rows((all_changes or {}).get('removed', []), 'Αφαιρέθηκαν')}
                        {render_proc_rows((all_changes or {}).get('modified', []), 'Τροποποιήθηκαν')}
                    </table>
                </div>

                <div class="section">
                    <h3>Εισερχόμενες Αιτήσεις ({esc(incoming.get('date', ''))})</h3>
                    <div class="sub">Σύγκριση με: {esc(incoming.get('reference_date') or 'πρώτη καταγραφή')}</div>
                    <h4>Νέες Πραγματικές</h4>
                    <table>
                        <tr><th></th><th>Case ID</th><th>Υποβλήθηκε</th><th>Θέμα</th><th>Συναλλασσόμενος</th></tr>
                        {render_incoming_rows(incoming.get('real_new', []), '✅')}
                    </table>
                    <h4>Νέες Δοκιμαστικές</h4>
                    <table>
                        <tr><th></th><th>Case ID</th><th>Υποβλήθηκε</th><th>Θέμα</th><th>Συναλλασσόμενος</th></tr>
                        {render_incoming_rows(incoming.get('test_new', []), '🧪')}
                    </table>
                    <h4>Αφαιρέθηκαν</h4>
                    <table>
                        <tr><th></th><th>Case ID</th><th>Υποβλήθηκε</th><th>Θέμα</th><th>Συναλλασσόμενος</th></tr>
                        {render_incoming_rows(incoming_changes.get('removed', []), '🗑️')}
                    </table>
                    <h4>Τροποποιήθηκαν</h4>
                    <table>
                        <tr><th></th><th>Case ID</th><th>Υποβλήθηκε</th><th>Θέμα</th><th>Συναλλασσόμενος</th></tr>
                        {render_incoming_rows([m.get('new', {}) for m in incoming_changes.get('modified', [])], '🔄')}
                    </table>
                </div>
            </body>
        </html>
        """

        sent = 0
        for admin in self.load_admins():
            if self.send_email(admin['email'], subject, body):
                sent += 1
        print(f"Daily digest sent to {sent} admin(s)")
        return sent > 0


# Example usage
if __name__ == "__main__":
    notifier = EmailNotifier()
    
    if notifier.is_enabled():
        # Test error notification
        notifier.notify_error(
            website_name="PKM Portal",
            error_message="Connection timeout - Unable to reach server after 10 seconds",
            url="https://pkm.rcm.gov.gr"
        )
    else:
        print("Email notifications are disabled or not configured properly")