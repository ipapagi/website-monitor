"""Configuration και paths management"""
import os

def get_project_root():
    """Επιστρέφει το root directory του project"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_data_path(*parts):
    """Επιστρέφει path μέσα στον data φάκελο"""
    return os.path.join(get_project_root(), 'data', *parts)

def get_baseline_path():
    """Path για baseline ενεργών διαδικασιών"""
    return get_data_path('active_procedures_baseline.json')

def get_all_procedures_baseline_path():
    """Path για baseline όλων των διαδικασιών"""
    return get_data_path('all_procedures_baseline.json')

def get_procedures_cache_path():
    """Path για procedures cache"""
    return get_data_path('procedures_cache.json')

def get_incoming_snapshot_path(date_str):
    """Path για incoming snapshot συγκεκριμένης ημερομηνίας"""
    incoming_dir = get_data_path('incoming_requests')
    os.makedirs(incoming_dir, exist_ok=True)
    return os.path.join(incoming_dir, f'incoming_{date_str}.json')

INCOMING_DEFAULT_PARAMS = {
    'isPoll': False,
    'queryId': 6,
    'queryOwner': 2,
    'isCase': False,
    'stateId': 'welcomeGrid-23_dashboard0',
    'page': 1,
    'start': 0,
    'limit': 200  # Βασικό όριο, θα γίνει pagination αν χρειαστεί
}
