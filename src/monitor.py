"""PKMMonitor class - με υποστήριξη Email Notifications"""
import json
import hashlib
import html
import time
from datetime import datetime
from session import PKMSession
from notifications import print_status, play_alert_sound, send_notification
from email_notifier import EmailNotifier

class PKMMonitor(PKMSession):
    def __init__(self, base_url, urls, api_params=None, login_params=None, 
                 check_interval=300, username=None, password=None, session_cookies=None):
        super().__init__(base_url, urls, login_params, username, password, session_cookies)
        self.api_params = api_params or {}
        self.check_interval = check_interval
        self.previous_data = None
        self.change_log = []
        self.email_notifier = EmailNotifier()  # Νέο: Email notifier
        self.is_down = False  # Νέο: Track αν το σύστημα είναι εκτός λειτουργίας
        self.downtime_start = None  # Νέο: Track χρόνο αρχής downtime

    def fetch_page(self):
        """Ανάκτηση δεδομένων από API"""
        return self.fetch_data(self.api_params)

    def parse_table_data(self, json_data):
        """Ανάλυση δεδομένων από JSON response"""
        if not json_data or not json_data.get('success'):
            return []
        
        data = []
        for record in json_data.get('data', []):
            if isinstance(record, dict):
                data.append({
                    'docid': str(record.get('DOCID', '')),
                    'αρ_διαδικασίας': str(record.get('W003_P_FLD75', '')),
                    'κωδικός': record.get('W003_P_FLD6', ''),
                    'τίτλος': record.get('W003_P_FLD4', ''),
                    'περιγραφή': html.unescape(record.get('DESCRIPTION', '')),
                    'ενεργή': 'ΝΑΙ' if record.get('W003_P_FLD3') == 'ΝΑΙ' else 'ΟΧΙ',
                    'κατάσταση': record.get('W003_P_FLD24', ''),
                    'απευθύνεται': record.get('W003_P_FLD12', ''),
                    'αρμοδιότητα': record.get('W003_P_FLD60', ''),
                    'ροή': record.get('W003_P_FLD5', ''),
                })
        return data

    def find_differences(self, old_data, new_data):
        """Εύρεση διαφορών"""
        old_dict = {item['docid']: item for item in old_data if item.get('docid')}
        new_dict = {item['docid']: item for item in new_data if item.get('docid')}
        
        return {
            'new_entries': [item for docid, item in new_dict.items() if docid not in old_dict],
            'removed_entries': [item for docid, item in old_dict.items() if docid not in new_dict],
            'modified_entries': [{'old': old_dict[docid], 'new': new_dict[docid]} 
                                for docid in old_dict if docid in new_dict and old_dict[docid] != new_dict[docid]]
        }

    def check_for_changes(self):
        """Έλεγχος για αλλαγές"""
        print_status("🔍 Έλεγχος για αλλαγές...", 'info')
        
        json_data = self.fetch_page()
        if not json_data:
            print_status("❌ Αποτυχία ανάκτησης", 'error')
            
            # Νέο: Αν το σύστημα δεν ήταν εκτός και τώρα είναι
            if not self.is_down:
                self.is_down = True
                self.downtime_start = datetime.now()
                error_msg = "Αποτυχία ανάκτησης δεδομένων από το API"
                self.email_notifier.notify_error(
                    website_name="PKM Portal",
                    error_message=error_msg,
                    url=self.base_url,
                    timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                )
            return False
        
        current_data = self.parse_table_data(json_data)
        
        if self.previous_data is None:
            self.previous_data = current_data
            # Νέο: Αν το σύστημα ήταν εκτός και τώρα ανακάμπτει
            if self.is_down:
                self.is_down = False
                duration = self._calculate_downtime(self.downtime_start)
                self.email_notifier.notify_recovery(
                    website_name="PKM Portal",
                    url=self.base_url,
                    downtime_duration=duration,
                    timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                )
                self.downtime_start = None
            print_status(f"✅ Αρχικοποίηση - {len(current_data)} διαδικασίες", 'success')
            return False
        
        old_hash = hashlib.md5(json.dumps(self.previous_data, sort_keys=True).encode()).hexdigest()
        new_hash = hashlib.md5(json.dumps(current_data, sort_keys=True).encode()).hexdigest()
        
        if old_hash != new_hash:
            print_status("🔔 ΑΝΙΧΝΕΥΘΗΚΑΝ ΑΛΛΑΓΕΣ!", 'alert')
            changes = self.find_differences(self.previous_data, current_data)
            self._print_changes(changes)
            self.change_log.append({'timestamp': datetime.now().isoformat(), 'changes': changes})
            self.previous_data = current_data
            play_alert_sound()
            send_notification("PKM Monitor", "Ανιχνεύθηκαν αλλαγές!")
            return True
        
        print_status(f"✓ Καμία αλλαγή - {len(current_data)} διαδικασίες", 'info')
        return False

    def _print_changes(self, changes):
        """Εμφάνιση αλλαγών"""
        for label, key, icon in [("Νέες", 'new_entries', '📌'), 
                                  ("Αφαιρεθείσες", 'removed_entries', '🗑️'),
                                  ("Τροποποιημένες", 'modified_entries', '🔄')]:
            if changes.get(key):
                print(f"\n{icon} {label} Διαδικασίες ({len(changes[key])})")
                print("─" * 60)
                for item in changes[key]:
                    entry = item.get('new', item) if isinstance(item, dict) and 'new' in item else item
                    print(f"  • [{entry.get('κωδικός')}] {entry.get('τίτλος', 'N/A')}")

    def _calculate_downtime(self, start_time):
        """Νέο: Υπολογισμός διάρκειας downtime"""
        if start_time is None:
            return None
        
        duration = datetime.now() - start_time
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        seconds = int(duration.total_seconds() % 60)
        
        if hours > 0:
            return f"{hours}ω {minutes}λ {seconds}δ"
        elif minutes > 0:
            return f"{minutes}λ {seconds}δ"
        else:
            return f"{seconds}δ"

    def start_monitoring(self, duration=None):
        """Έναρξη continuous monitoring"""
        print("\n" + "="*80)
        print("🚀 PKM REAL-TIME MONITOR".center(80))
        print("="*80)
        print(f"📍 URL: {self.base_url}")
        print(f"⏱️  Συχνότητα: κάθε {self.check_interval}s ({self.check_interval/60:.1f} λεπτά)")
        print(f"📧 Email Notifications: {'✅ Enabled' if self.email_notifier.is_enabled() else '❌ Disabled'}")
        print("="*80 + "\n")
        
        start_time = time.time()
        check_count = 0
        
        try:
            while True:
                check_count += 1
                print_status(f"━━━ Έλεγχος #{check_count} ━━━", 'info')
                self.check_for_changes()
                
                if duration and (time.time() - start_time) >= duration:
                    break
                
                for remaining in range(self.check_interval, 0, -1):
                    print(f"\r⏳ Επόμενος έλεγχος σε: {remaining//60:02d}:{remaining%60:02d}   ", end='', flush=True)
                    time.sleep(1)
                print("\r" + " "*50 + "\r", end='')
                
        except KeyboardInterrupt:
            print_status(f"\n⛔ Διακοπή - Έλεγχοι: {check_count}", 'warning')