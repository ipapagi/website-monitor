"""Notifications και ήχοι"""
import sys
import os
from datetime import datetime

# Optional imports
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

def play_alert_sound():
    """Αναπαραγωγή ήχου ειδοποίησης"""
    if not SOUND_AVAILABLE:
        return
    try:
        if sys.platform == 'win32':
            winsound.Beep(1000, 500)
        elif sys.platform == 'darwin':
            os.system('afplay /System/Library/Sounds/Glass.aiff')
        else:
            os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || beep -f 1000 -l 500 2>/dev/null')
    except:
        pass

def send_notification(title, message):
    """Αποστολή desktop notification"""
    if not NOTIFICATIONS_AVAILABLE:
        return
    try:
        notification.notify(title=title, message=message, app_name='PKM Monitor', timeout=10)
    except Exception as e:
        print(f"⚠️ Notification error: {e}")

def print_status(message, level='info'):
    """Εμφάνιση μηνύματος με χρωματισμό και timestamp"""
    import re
    timestamp = datetime.now().strftime('%H:%M:%S')
    colors = {
        'info': '\033[94m', 'success': '\033[92m', 'warning': '\033[93m',
        'error': '\033[91m', 'alert': '\033[95m', 'reset': '\033[0m'
    }
    color = colors.get(level, colors['info'])
    try:
        print(f"{color}[{timestamp}] {message}{colors['reset']}", flush=True)
    except UnicodeEncodeError:
        # Fallback για Windows cp1253 encoding - strip emoji
        clean_msg = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]', '', message)
        print(f"[{timestamp}] {clean_msg}", flush=True)
