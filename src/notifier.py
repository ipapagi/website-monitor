from plyer import notification
import winsound
import os
import sys

class Notifier:
    @staticmethod
    def send_notification(title, message):
        """Send a desktop notification."""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='Website Monitor',
                timeout=10
            )
        except Exception as e:
            print(f"⚠️ Could not send notification: {e}")

    @staticmethod
    def play_alert_sound():
        """Play an alert sound based on the operating system."""
        try:
            if sys.platform == 'win32':
                winsound.Beep(1000, 500)  # Frequency 1000Hz, duration 500ms
            elif sys.platform == 'darwin':
                os.system('afplay /System/Library/Sounds/Glass.aiff')
            else:
                os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || beep -f 1000 -l 500 2>/dev/null')
        except Exception as e:
            pass  # If sound playback fails, it's not critical