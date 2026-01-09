"""Session management και HTTP requests"""
import requests
import time
import json
import urllib3
from notifications import print_status

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PKMSession:
    def __init__(self, base_url, urls, login_params=None, username=None, password=None, session_cookies=None):
        self.base_url = base_url.rstrip('/')
        self.urls = urls or {}
        self.login_params = login_params or {}
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logged_in = False
        self.main_page_loaded = False
        self.jwt_token = None
        
        # URLs
        self.login_page_url = self.base_url + self.urls.get('login_page', '/login.jsp')
        self.login_api_url = self.base_url + self.urls.get('login_api', '/services/LoginServices/loginWeb')
        self.main_page_url = self.base_url + self.urls.get('main_page', '/ext_main.jsp?locale=el')
        self.data_api_url = self.base_url + self.urls.get('data_api', '/services/DataServices/getListData')
        
        if session_cookies:
            for name, value in session_cookies.items():
                if value:
                    self.session.cookies.set(name, value)
                    self.logged_in = True

    def login(self):
        """Σύνδεση στο PKM"""
        if not self.username or not self.password:
            print_status("⚠️ Δεν δόθηκαν credentials", 'warning')
            return False
        
        try:
            from datetime import datetime
            print("\n" + "-"*80)
            current_date = datetime.now().strftime('%d/%m/%Y')
            print_status(f"🔐 ΕΝΑΡΞΗ ΔΙΑΔΙΚΑΣΙΑΣ ΣΥΝΔΕΣΗΣ - {current_date}", 'info')
            
            # GET login page για cookies
            self.session.get(self.login_page_url, verify=False, timeout=10)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
                'Accept': '*/*', 'Accept-Language': 'el',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': self.base_url, 'Referer': self.login_page_url,
            }
            
            login_data = {
                'username': self.username, 'password': self.password,
                'application': self.login_params.get('application', '2'),
                'otp': self.login_params.get('otp', '')
            }
            
            response = self.session.post(self.login_api_url, data=login_data, 
                                        headers=headers, verify=False, timeout=10)
            
            # JWT from headers
            if response.headers.get('jwt'):
                self.jwt_token = response.headers.get('jwt')
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('jwt'):
                        self.jwt_token = result.get('jwt')
                    elif result.get('token'):
                        self.jwt_token = result.get('token')
                    
                    if result.get('success'):
                        print_status(f"✅ LOGIN ΕΠΙΤΥΧΗΣ - {self.username}", 'success')
                        self.logged_in = True
                        return True
                    else:
                        print_status(f"❌ LOGIN ΑΠΟΤΥΧΙΑ: {result.get('message', 'Άγνωστο')}", 'error')
                        return False
                except:
                    if len(self.session.cookies) > 1:
                        self.logged_in = True
                        return True
            return False
        except requests.RequestException as e:
            print_status(f"❌ ΣΦΑΛΜΑ ΣΥΝΔΕΣΗΣ: {e}", 'error')
            return False

    def load_main_page(self):
        """Φόρτωση κύριας σελίδας"""
        try:
            response = self.session.get(self.main_page_url, verify=False, timeout=15,
                headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'})
            if response.status_code == 200:
                self.main_page_loaded = True
                return True
            return False
        except:
            return False

    def fetch_data(self, api_params):
        """Ανάκτηση δεδομένων από API"""
        if not self.logged_in and not self.login():
            return None
        if not self.main_page_loaded and not self.load_main_page():
            return None
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
                'Accept': '*/*', 'Accept-Language': 'el',
                'X-Requested-With': 'XMLHttpRequest', 'Referer': self.main_page_url,
            }
            if self.jwt_token:
                headers['Authorization'] = f'Bearer {self.jwt_token}'
            
            params = {k: str(v).lower() if isinstance(v, bool) else v for k, v in api_params.items()}
            params['_dc'] = str(int(time.time() * 1000))
            
            response = self.session.get(self.data_api_url, params=params, 
                                       headers=headers, timeout=15, verify=False)
            
            if 'login' in response.url.lower():
                self.logged_in = False
                self.main_page_loaded = False
                self.jwt_token = None
                if self.login() and self.load_main_page():
                    return self.fetch_data(api_params)
                return None
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print_status(f"❌ Σφάλμα fetch: {e}", 'error')
            return None
