import requests
from bs4 import BeautifulSoup
import time
import json
import hashlib
import sys
import os
from datetime import datetime
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Optional imports for notifications and sound
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

try:
    import winsound  # For Windows sound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

class PKMMonitor:
    def __init__(self, base_url, urls, api_params=None, login_params=None, 
                 check_interval=300, username=None, password=None, session_cookies=None):
        """
        Παρακολούθηση σελίδας PKM (Πλατφόρμα Κυβερνητικού Μητρώου)
        
        Args:
            base_url (str): Το base URL του server
            urls (dict): Dictionary με τα endpoints (login_page, login_api, main_page, data_api)
            api_params (dict): Query parameters για το data API
            login_params (dict): Extra parameters για το login (application, otp)
            check_interval (int): Χρόνος σε δευτερόλεπτα μεταξύ ελέγχων
            username (str): Username για login
            password (str): Password για login
            session_cookies (dict): Session cookies από το browser
        """
        self.base_url = base_url.rstrip('/')
        self.urls = urls or {}
        self.api_params = api_params or {}
        self.login_params = login_params or {}
        self.check_interval = check_interval
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.previous_data = None
        self.change_log = []
        self.total_changes_found = 0
        self.logged_in = False
        self.main_page_loaded = False
        self.jwt_token = None  # Προσθήκη JWT token
        
        # Κατασκευή πλήρων URLs
        self.login_page_url = self.base_url + self.urls.get('login_page', '/login.jsp')
        self.login_api_url = self.base_url + self.urls.get('login_api', '/services/LoginServices/loginWeb')
        self.main_page_url = self.base_url + self.urls.get('main_page', '/ext_main.jsp?locale=el')
        self.data_api_url = self.base_url + self.urls.get('data_api', '/services/DataServices/getListData')
        
        # Αν δόθηκαν cookies, τα φορτώνουμε
        if session_cookies:
            for name, value in session_cookies.items():
                if value:
                    self.session.cookies.set(name, value)
                    self.logged_in = True

    def login(self):
        """Σύνδεση στο PKM με username/password"""
        if not self.username or not self.password:
            self.print_real_time_update("⚠️ Δεν δόθηκαν credentials", 'warning')
            return False
        
        try:
            print("\n" + "─"*80)
            self.print_real_time_update("🔐 ΕΝΑΡΞΗ ΔΙΑΔΙΚΑΣΙΑΣ ΣΥΝΔΕΣΗΣ", 'info')
            print("─"*80)
            
            # Πρώτα GET στο login page για cookies
            self.print_real_time_update(f"📡 GET {self.login_page_url}...", 'info')
            self.session.get(
                self.login_page_url,
                verify=False,
                timeout=10
            )
            self.print_real_time_update(f"✓ Session cookies: {list(self.session.cookies.keys())}", 'success')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
                'Accept': '*/*',
                'Accept-Language': 'el',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': self.base_url,
                'Referer': self.login_page_url,
            }
            
            login_data = {
                'username': self.username,
                'password': self.password,
                'application': self.login_params.get('application', '2'),
                'otp': self.login_params.get('otp', '')
            }
            
            self.print_real_time_update(f"📤 POST {self.login_api_url}", 'info')
            
            response = self.session.post(
                self.login_api_url,
                data=login_data,
                headers=headers,
                verify=False,
                timeout=10,
                allow_redirects=True
            )
            
            self.print_real_time_update(f"📥 Response Status: {response.status_code}", 'info')
            
            # Έλεγχος για JWT token στα response headers
            jwt_header = response.headers.get('jwt')
            if jwt_header:
                self.jwt_token = jwt_header
                self.print_real_time_update(f"🔑 JWT Token λήφθηκε από headers", 'success')
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # Έλεγχος για JWT token στο response body
                    if result.get('jwt'):
                        self.jwt_token = result.get('jwt')
                        self.print_real_time_update(f"🔑 JWT Token λήφθηκε από response body", 'success')
                    elif result.get('token'):
                        self.jwt_token = result.get('token')
                        self.print_real_time_update(f"🔑 JWT Token λήφθηκε από response body", 'success')
                    
                    if result.get('success') == True:
                        print("\n" + "="*80)
                        self.print_real_time_update("✅ ✅ ✅  LOGIN ΕΠΙΤΥΧΗΣ!  ✅ ✅ ✅", 'success')
                        print("="*80)
                        self.print_real_time_update(f"👤 Χρήστης: {self.username}", 'success')
                        self.print_real_time_update(f"🔑 JWT: {'✓ Ναι' if self.jwt_token else '✗ Όχι'}", 'success')
                        self.print_real_time_update(f"🍪 Cookies: {list(self.session.cookies.keys())}", 'success')
                        print("="*80 + "\n")
                        self.logged_in = True
                        return True
                    else:
                        error_msg = result.get('message', result.get('error', 'Άγνωστο σφάλμα'))
                        print("\n" + "="*80)
                        self.print_real_time_update("❌ LOGIN ΑΠΟΤΥΧΙΑ", 'error')
                        self.print_real_time_update(f"⚠️  {error_msg}", 'error')
                        print("="*80 + "\n")
                        return False
                except Exception as e:
                    self.print_real_time_update(f"⚠️ JSON parse error: {e}", 'warning')
                    if len(self.session.cookies) > 1:
                        self.logged_in = True
                        return True
                    return False
            else:
                print("\n" + "="*80)
                self.print_real_time_update("❌ LOGIN ΑΠΟΤΥΧΙΑ", 'error')
                self.print_real_time_update(f"⚠️  HTTP Status: {response.status_code}", 'error')
                print("="*80 + "\n")
                return False
                
        except requests.RequestException as e:
            print("\n" + "="*80)
            self.print_real_time_update("❌ ΣΦΑΛΜΑ ΣΥΝΔΕΣΗΣ", 'error')
            self.print_real_time_update(f"⚠️  {e}", 'error')
            print("="*80 + "\n")
            return False

    def load_main_page(self):
        """Φόρτωση της κύριας σελίδας για αρχικοποίηση του ExtJS app"""
        try:
            self.print_real_time_update(f"📄 Φόρτωση {self.main_page_url}...", 'info')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'el-GR,el;q=0.9',
            }
            
            response = self.session.get(
                self.main_page_url,
                headers=headers,
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                self.print_real_time_update("✅ Κύρια σελίδα φορτώθηκε επιτυχώς", 'success')
                self.main_page_loaded = True
                return True
            else:
                self.print_real_time_update(f"❌ Αποτυχία - Status: {response.status_code}", 'error')
                return False
                
        except requests.RequestException as e:
            self.print_real_time_update(f"❌ Σφάλμα: {e}", 'error')
            return False

    def fetch_page(self):
        """Ανάκτηση των δεδομένων από το API"""
        if not self.logged_in:
            if not self.login():
                return None
        
        if not self.main_page_loaded:
            if not self.load_main_page():
                return None
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
                'Accept': '*/*',
                'Accept-Language': 'el',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': self.main_page_url,
                'Connection': 'keep-alive',
            }
            
            # Προσθήκη JWT token αν υπάρχει
            if self.jwt_token:
                headers['Authorization'] = f'Bearer {self.jwt_token}'
            
            # Προσθήκη timestamp στα parameters
            params = {}
            for key, value in self.api_params.items():
                if isinstance(value, bool):
                    params[key] = str(value).lower()
                else:
                    params[key] = value
            params['_dc'] = str(int(time.time() * 1000))
            
            self.print_real_time_update(f"📡 GET {self.data_api_url}", 'info')
            if self.jwt_token:
                self.print_real_time_update(f"🔑 Με JWT Token", 'info')
            
            response = self.session.get(
                self.data_api_url, 
                params=params,
                headers=headers, 
                timeout=15, 
                verify=False
            )
            
            self.print_real_time_update(f"📥 Status: {response.status_code}", 'info')
            
            if response.status_code != 200:
                with open('debug_api_error.txt', 'w', encoding='utf-8') as f:
                    f.write(f"URL: {response.url}\n")
                    f.write(f"Status: {response.status_code}\n")
                    f.write(f"Headers: {dict(response.headers)}\n\n")
                    f.write(response.text[:2000])
                self.print_real_time_update("💾 Debug saved to debug_api_error.txt", 'info')
            
            if 'login' in response.url.lower():
                self.print_real_time_update("⚠️ Η συνεδρία έληξε, επανασύνδεση...", 'warning')
                self.logged_in = False
                self.main_page_loaded = False
                self.jwt_token = None
                if self.login() and self.load_main_page():
                    return self.fetch_page()
                else:
                    return None
            
            response.raise_for_status()
            
            # Αποθήκευση response για debugging
            result = response.json()
            with open('api_response.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            return result
            
        except requests.RequestException as e:
            self.print_real_time_update(f"❌ Σφάλμα: {e}", 'error')
            return None

    def parse_table_data(self, json_data):
        """Ανάλυση των δεδομένων από το JSON response"""
        try:
            if not json_data or not isinstance(json_data, dict):
                return []
            
            if not json_data.get('success'):
                self.print_real_time_update(f"⚠️ API Error: {json_data.get('processMessage')}", 'warning')
                return []
            
            records = json_data.get('data', [])
            
            # Debug: Αποθήκευση του JSON
            with open('api_response.json', 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            data = []
            active_count = 0
            
            for record in records:
                if isinstance(record, dict):
                    # Αποκωδικοποίηση HTML entities στην περιγραφή
                    import html
                    description = html.unescape(record.get('DESCRIPTION', ''))
                    title = record.get('W003_P_FLD4', '')
                    
                    # Έλεγχος αν είναι ενεργή
                    is_active = record.get('W003_P_FLD3', '') == 'ΝΑΙ'
                    if is_active:
                        active_count += 1
                    
                    entry = {
                        'docid': str(record.get('DOCID', '')),
                        'αρ_διαδικασίας': str(record.get('W003_P_FLD75', '')),
                        'κωδικός': record.get('W003_P_FLD6', ''),
                        'τίτλος': title,
                        'περιγραφή': description,
                        'ενεργή': 'ΝΑΙ' if is_active else 'ΟΧΙ',
                        'κατάσταση': record.get('W003_P_FLD24', ''),
                        'απευθύνεται': record.get('W003_P_FLD12', ''),
                        'αρμοδιότητα': record.get('W003_P_FLD60', ''),
                        'ροή': record.get('W003_P_FLD5', ''),
                    }
                    data.append(entry)
            
            self.print_real_time_update(f"📋 Σύνολο διαδικασιών: {len(data)}", 'info')
            self.print_real_time_update(f"✅ Ενεργές διαδικασίες: {active_count}", 'success')
            
            return data
            
        except Exception as e:
            self.print_real_time_update(f"❌ Σφάλμα κατά την ανάλυση: {e}", 'error')
            import traceback
            traceback.print_exc()
            return []
    
    def calculate_hash(self, data):
        """Υπολογισμός hash για γρήγορη σύγκριση"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    def find_differences(self, old_data, new_data):
        """Εύρεση διαφορών μεταξύ παλιών και νέων δεδομένων"""
        changes = {
            'new_entries': [],
            'removed_entries': [],
            'modified_entries': []
        }
        
        # Χρήση DOCID ως μοναδικό κλειδί
        old_dict = {item['docid']: item for item in old_data if item['docid']}
        new_dict = {item['docid']: item for item in new_data if item['docid']}
        
        # Εύρεση νέων εγγραφών
        for docid, item in new_dict.items():
            if docid not in old_dict:
                changes['new_entries'].append(item)
        
        # Εύρεση διαγραμμένων εγγραφών
        for docid, item in old_dict.items():
            if docid not in new_dict:
                changes['removed_entries'].append(item)
        
        # Εύρεση τροποποιημένων εγγραφών
        for docid in old_dict:
            if docid in new_dict:
                if old_dict[docid] != new_dict[docid]:
                    changes['modified_entries'].append({
                        'old': old_dict[docid],
                        'new': new_dict[docid]
                    })
        
        return changes
    
    def play_alert_sound(self):
        """Αναπαραγωγή ήχου ειδοποίησης"""
        if not SOUND_AVAILABLE:
            return
        
        try:
            if sys.platform == 'win32':
                # Windows
                import winsound
                winsound.Beep(1000, 500)  # Συχνότητα 1000Hz, διάρκεια 500ms
            elif sys.platform == 'darwin':
                # macOS
                os.system('afplay /System/Library/Sounds/Glass.aiff')
            else:
                # Linux
                os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || beep -f 1000 -l 500 2>/dev/null')
        except Exception as e:
            pass  # Αν αποτύχει ο ήχος, δεν είναι κρίσιμο
    
    def send_notification(self, title, message):
        """Αποστολή desktop notification"""
        if NOTIFICATIONS_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name='PKM Monitor',
                    timeout=10
                )
            except Exception as e:
                print(f"⚠️ Δεν ήταν δυνατή η αποστολή notification: {e}")
    
    def print_real_time_update(self, message, level='info'):
        """Εμφάνιση μηνύματος με χρωματισμό και timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        colors = {
            'info': '\033[94m',      # Μπλε
            'success': '\033[92m',   # Πράσινο
            'warning': '\033[93m',   # Κίτρινο
            'error': '\033[91m',     # Κόκκινο
            'alert': '\033[95m',     # Μωβ
            'reset': '\033[0m'
        }
        
        color = colors.get(level, colors['info'])
        reset = colors['reset']
        
        print(f"{color}[{timestamp}] {message}{reset}", flush=True)
    
    def check_for_changes(self):
        """Έλεγχος για αλλαγές στη σελίδα με real-time updates"""
        self.print_real_time_update("🔍 Έλεγχος για αλλαγές...", 'info')
        
        json_data = self.fetch_page()
        
        if json_data is None:
            self.print_real_time_update("❌ Αποτυχία ανάκτησης σελίδας", 'error')
            return False
        
        current_data = self.parse_table_data(json_data)
        
        if current_data is None:
            self.print_real_time_update("❌ Αποτυχία ανάλυσης δεδομένων", 'error')
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self.previous_data is None:
            # Πρώτος έλεγχος
            self.previous_data = current_data
            self.print_real_time_update(
                f"✅ Αρχικοποίηση - Βρέθηκαν {len(current_data)} διαδικασίες", 
                'success'
            )
            return False
        
        # Υπολογισμός hash για γρήγορη σύγκριση
        old_hash = self.calculate_hash(self.previous_data)
        new_hash = self.calculate_hash(current_data)
        
        if old_hash != new_hash:
            self.print_real_time_update("", 'info')
            print(f"\n{'='*80}")
            self.print_real_time_update("🔔 ΑΝΙΧΝΕΥΘΗΚΑΝ ΑΛΛΑΓΕΣ!", 'alert')
            print(f"{'='*80}\n")
            
            changes = self.find_differences(self.previous_data, current_data)
            self.print_changes(changes)
            
            # Αποθήκευση στο ιστορικό
            self.change_log.append({
                'timestamp': timestamp,
                'changes': changes
            })
            
            self.previous_data = current_data
            
            # Αυτόματη αποθήκευση μετά από αλλαγή
            self.save_log()
            
            return True
        else:
            self.print_real_time_update(
                f"✓ Καμία αλλαγή - Διαδικασίες: {len(current_data)}", 
                'info'
            )
            return False
    
    def start_monitoring(self, duration=None):
        """
        Έναρξη παρακολούθησης με real-time updates
        
        Args:
            duration (int): Συνολικός χρόνος παρακολούθησης σε δευτερόλεπτα (None για άπειρη)
        """
        print("\n" + "="*80)
        print("🚀 PKM REAL-TIME MONITOR".center(80))
        print("="*80)
        print(f"📍 Base URL: {self.base_url}")
        print(f"📍 Data API: {self.data_api_url}")
        print(f"⏱️  Συχνότητα: κάθε {self.check_interval} δευτερόλεπτα ({self.check_interval/60:.1f} λεπτά)")
        print(f"🔔 Ειδοποιήσεις: {'✓ Ενεργές' if NOTIFICATIONS_AVAILABLE else '✗ Απενεργοποιημένες'}")
        print(f"🔊 Ήχος: {'✓ Ενεργός' if SOUND_AVAILABLE else '✗ Απενεργοποιημένος'}")
        print("="*80 + "\n")
        
        self.print_real_time_update("⚡ Ξεκινά η παρακολούθηση...", 'success')
        
        start_time = time.time()
        check_count = 0
        
        try:
            while True:
                check_count += 1
                self.print_real_time_update(f"━━━ Έλεγχος #{check_count} ━━━", 'info')
                
                self.check_for_changes()
                
                if duration and (time.time() - start_time) >= duration:
                    self.print_real_time_update("✅ Ολοκλήρωση παρακολούθησης", 'success')
                    break
                
                # Εμφάνιση αντίστροφης μέτρησης
                next_check = self.check_interval
                while next_check > 0 and (not duration or (time.time() - start_time) < duration):
                    mins, secs = divmod(next_check, 60)
                    print(f"\r⏳ Επόμενος έλεγχος σε: {int(mins):02d}:{int(secs):02d}   ", end='', flush=True)
                    time.sleep(1)
                    next_check -= 1
                
                print("\r" + " "*50 + "\r", end='', flush=True)  # Καθαρισμός γραμμής
                
        except KeyboardInterrupt:
            print("\n")
            self.print_real_time_update("⛔ Διακοπή από χρήστη", 'warning')
            self.print_real_time_update(f"📊 Σύνολο ελέγχων: {check_count}", 'info')
            self.print_real_time_update(f"📊 Σύνολο αλλαγών: {self.total_changes_found}", 'info')
    
    def save_log(self, filename="pkm_changes_log.json"):
        """Αποθήκευση ιστορικού αλλαγών σε αρχείο"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.change_log, f, ensure_ascii=False, indent=2)
        print(f"💾 Το ιστορικό αποθηκεύτηκε στο {filename}")
    
    def print_changes(self, changes):
        """Εμφάνιση αλλαγών με όμορφο formatting"""
        if changes['new_entries']:
            print(f"\n📌 Νέες Διαδικασίες ({len(changes['new_entries'])})")
            print("─" * 80)
            for entry in changes['new_entries']:
                print(f"  • [{entry.get('κωδικός')}] {entry.get('τίτλος', 'N/A')}")
                print(f"    Αρ. Διαδικασίας: {entry.get('αρ_διαδικασίας')}")
                print(f"    Ενεργή: {entry.get('ενεργή')} | Κατάσταση: {entry.get('κατάσταση')}")
        
        if changes['removed_entries']:
            print(f"\n🗑️  Αφαιρεθείσες Διαδικασίες ({len(changes['removed_entries'])})")
            print("─" * 80)
            for entry in changes['removed_entries']:
                print(f"  • [{entry.get('κωδικός')}] {entry.get('τίτλος', 'N/A')}")
        
        if changes['modified_entries']:
            print(f"\n🔄 Τροποποιημένες Διαδικασίες ({len(changes['modified_entries'])})")
            print("─" * 80)
            for mod in changes['modified_entries']:
                print(f"  • [{mod['new'].get('κωδικός')}] {mod['new'].get('τίτλος', 'N/A')}")
                # Εμφάνιση τι άλλαξε
                for key in ['ενεργή', 'κατάσταση', 'τίτλος']:
                    if mod['old'].get(key) != mod['new'].get(key):
                        old_val = mod['old'].get(key, '(κενό)')
                        new_val = mod['new'].get(key, '(κενό)')
                        print(f"    {key}: {old_val} → {new_val}")
        
        print("\n")