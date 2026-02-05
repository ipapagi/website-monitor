"""Διαχείριση Διευθύνσεων, Περιφερειακών Ενοτήτων και Email διευθυνσιοδότησης"""
import os
import json
from typing import Dict, List, Optional, Tuple
from config import get_project_root


class DirectoriesManager:
    """Διαχειρίζει τις Διευθύνσεις, Περιφερειακές Ενότητες και email routing"""
    
    def __init__(self, config_file: str = None):
        """Αρχικοποίηση με φόρτωση του config αρχείου"""
        if config_file is None:
            config_file = os.path.join(get_project_root(), 'data', 'directories_config.json')
        
        self.config_file = config_file
        self.config = self._load_config()
        self._build_lookup_tables()
    
    def _load_config(self) -> Dict:
        """Φορτώνει το αρχείο διαμόρφωσης"""
        if not os.path.exists(self.config_file):
            return {'directories': [], 'regional_units_map': {}}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Αποτυχία φόρτωσης διαμόρφωσης: {e}")
            return {'directories': [], 'regional_units_map': {}}
    
    def _build_lookup_tables(self):
        """Δημιουργεί lookup tables για γρήγορη αναζήτηση"""
        # Χάρτης όνομα Διεύθυνσης -> Διεύθυνση
        self.directory_by_name = {}
        # Χάρτης σύντομο όνομα Διεύθυνσης -> Διεύθυνση
        self.directory_by_short_name = {}
        # Χάρτης (Διεύθυνση, Π.Ε.) -> email
        self.email_by_dir_and_ru = {}
        
        for directory in self.config.get('directories', []):
            dir_name = directory.get('name', '').strip()
            dir_short = directory.get('short_name', '').strip()
            
            self.directory_by_name[dir_name] = directory
            if dir_short:
                self.directory_by_short_name[dir_short] = directory
            
            # Δημιουργία χάρτη (Διεύθυνση, Π.Ε.) -> email
            for ru in directory.get('regional_units', []):
                ru_name = ru.get('name', '').strip()
                email = ru.get('email', '').strip()
                key = (dir_name, ru_name)
                self.email_by_dir_and_ru[key] = email
    
    def get_directory_by_name(self, name: str) -> Optional[Dict]:
        """Αναζητεί Διεύθυνση με ακριβές όνομα"""
        if name in self.directory_by_name:
            return self.directory_by_name[name]
        
        # Αναζήτηση με partial match
        for dir_name, directory in self.directory_by_name.items():
            if name.lower() in dir_name.lower():
                return directory
        
        return None
    
    def get_directory_by_short_name(self, short_name: str) -> Optional[Dict]:
        """Αναζητεί Διεύθυνση με σύντομο όνομα"""
        return self.directory_by_short_name.get(short_name)
    
    def get_email_for_directory_and_regional_unit(
        self, directory: str, regional_unit: str
    ) -> Optional[str]:
        """Επιστρέφει το email για συγκεκριμένη Διεύθυνση και Π.Ε."""
        # Ακριβής αναζήτηση
        key = (directory.strip(), regional_unit.strip())
        if key in self.email_by_dir_and_ru:
            return self.email_by_dir_and_ru[key]
        
        # Αναζήτηση με partial match
        for (stored_dir, stored_ru), email in self.email_by_dir_and_ru.items():
            if (directory.lower() in stored_dir.lower() and 
                regional_unit.lower() in stored_ru.lower()):
                return email
        
        return None
    
    def get_regional_unit_email(self, regional_unit_name: str) -> Optional[str]:
        """Αναζητεί email περιφερειακής ενότητας"""
        ru_map = self.config.get('regional_units_map', {})
        
        # Ακριβής αναζήτηση
        if regional_unit_name in ru_map:
            return ru_map[regional_unit_name].get('email')
        
        # Partial match
        for ru_key, ru_data in ru_map.items():
            if regional_unit_name.lower() in ru_key.lower():
                return ru_data.get('email')
        
        return None
    
    def get_all_directories(self) -> List[Dict]:
        """Επιστρέφει όλες τις Διευθύνσεις"""
        return self.config.get('directories', [])
    
    def get_all_regional_units(self) -> Dict[str, Dict]:
        """Επιστρέφει όλες τις Π.Ε."""
        return self.config.get('regional_units_map', {})
    
    def get_regional_units_for_directory(self, directory_name: str) -> List[Dict]:
        """Επιστρέφει τις Π.Ε. για συγκεκριμένη Διεύθυνση"""
        directory = self.get_directory_by_name(directory_name)
        if directory:
            return directory.get('regional_units', [])
        return []
    
    def extract_directory_and_regional_unit(
        self, record: Dict
    ) -> Tuple[Optional[str], Optional[str]]:
        """Εξάγει τη Διεύθυνση και τη Π.Ε. από ένα αρχείο αίτησης
        
        Προσπαθεί να αναγνωρίσει από:
        1. Πεδίο 'directory' αν περιέχει Π.Ε.
        2. Πεδίο 'subject' ή άλλα δεδομένα
        
        Returns:
            Tuple (directory_name, regional_unit_name) ή (None, None)
        """
        directory_str = record.get('directory', '').strip()
        
        if not directory_str:
            return None, None
        
        # Αναζήτηση αν υπάρχει Π.Ε. στο όνομα
        regional_unit = None
        for ru_key in self.config.get('regional_units_map', {}).keys():
            if ru_key.lower() in directory_str.lower():
                regional_unit = ru_key
                break
        
        return directory_str, regional_unit
    
    def find_best_email_for_record(self, record: Dict) -> Optional[Tuple[str, str]]:
        """Βρίσκει το καλύτερο email για μια αίτηση
        
        Επιστρέφει: (email, source) όπου source = 'directory_ru', 'regional_unit', ή 'fallback'
        """
        directory_str, regional_unit_str = self.extract_directory_and_regional_unit(record)
        
        # Πρώτη προσπάθεια: Διεύθυνση + Π.Ε.
        if directory_str and regional_unit_str:
            email = self.get_email_for_directory_and_regional_unit(directory_str, regional_unit_str)
            if email:
                return (email, 'directory_ru')
        
        # Δεύτερη προσπάθεια: Μόνο Π.Ε.
        if regional_unit_str:
            email = self.get_regional_unit_email(regional_unit_str)
            if email:
                return (email, 'regional_unit')
        
        # Τρίτη προσπάθεια: Μόνο Διεύθυνση
        if directory_str:
            directory = self.get_directory_by_name(directory_str)
            if directory and directory.get('regional_units'):
                # Επιστρέφουμε το πρώτο email (για fallback)
                ru = directory['regional_units'][0]
                email = ru.get('email')
                if email:
                    return (email, 'fallback')
        
        return None
    
    def get_directory_info_by_name(self, directory_name: str) -> Optional[Dict]:
        """Επιστρέφει όλες τις πληροφορίες μιας Διεύθυνσης"""
        return self.get_directory_by_name(directory_name)
    
    def export_for_excel(self) -> List[Dict]:
        """Εξαγωγή δεδομένων σε format κατάλληλο για Excel"""
        rows = []
        for directory in self.get_all_directories():
            dir_name = directory.get('name', '')
            dir_short = directory.get('short_name', '')
            
            for ru in directory.get('regional_units', []):
                rows.append({
                    'Διεύθυνση': dir_name,
                    'Σύντομο Όνομα': dir_short,
                    'Περιφερειακή Ενότητα': ru.get('name', ''),
                    'Email': ru.get('email', ''),
                    'Τηλέφωνο': ru.get('phone', ''),
                    'Υπεύθυνος': ru.get('responsible', '')
                })
        
        return rows


def get_directories_manager() -> DirectoriesManager:
    """Singleton manager για τις Διευθύνσεις"""
    if not hasattr(get_directories_manager, '_instance'):
        get_directories_manager._instance = DirectoriesManager()
    return get_directories_manager._instance


# Convenience functions
def find_email_for_directory(directory_name: str) -> Optional[str]:
    """Αναζητεί email για μια Διεύθυνση"""
    manager = get_directories_manager()
    directory = manager.get_directory_by_name(directory_name)
    if directory and directory.get('regional_units'):
        return directory['regional_units'][0].get('email')
    return None


def find_email_for_request(record: Dict) -> Optional[Tuple[str, str]]:
    """Αναζητεί το καλύτερο email για μια αίτηση
    
    Returns: (email, source)
    """
    manager = get_directories_manager()
    return manager.find_best_email_for_record(record)
