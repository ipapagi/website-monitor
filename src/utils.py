import yaml
import os
from dotenv import load_dotenv

def log_message(message, level='INFO'):
    """Logs a message with a specified level."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} [{level}] {message}")

def load_config(config_path):
    """Φόρτωση configuration από YAML αρχείο και .env"""
    # Φόρτωση .env αρχείου
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, '.env')
    load_dotenv(env_path)
    
    # Φόρτωση YAML config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Προσθήκη credentials από environment variables
    config['username'] = os.getenv('PKM_USERNAME', '')
    config['password'] = os.getenv('PKM_PASSWORD', '')
    
    return config

def save_log_to_file(log_data, log_file):
    """Saves log data to a specified file."""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_data + '\n')