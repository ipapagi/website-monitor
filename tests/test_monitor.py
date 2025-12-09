import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from monitor import PKMMonitor

class TestPKMMonitor(unittest.TestCase):

    @patch('src.monitor.requests.get')
    def test_fetch_page_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '<html></html>'
        
        monitor = PKMMonitor("http://example.com")
        result = monitor.fetch_page()
        
        self.assertEqual(result, '<html></html>')
        mock_get.assert_called_once()

    @patch('src.monitor.requests.get')
    def test_fetch_page_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        
        monitor = PKMMonitor("http://example.com")
        result = monitor.fetch_page()
        
        self.assertIsNone(result)

    def test_calculate_hash(self):
        monitor = PKMMonitor("http://example.com")
        data = [{'κωδικος': '123', 'τιτλος': 'Test Title'}]
        result = monitor.calculate_hash(data)
        
        self.assertIsInstance(result, str)

    def test_find_differences(self):
        monitor = PKMMonitor("http://example.com")
        old_data = [{'κωδικος': '123', 'τιτλος': 'Old Title'}]
        new_data = [{'κωδικος': '123', 'τιτλος': 'New Title'}]
        
        changes = monitor.find_differences(old_data, new_data)
        
        self.assertEqual(len(changes['modified_entries']), 1)
        self.assertEqual(changes['modified_entries'][0]['old']['τιτλος'], 'Old Title')
        self.assertEqual(changes['modified_entries'][0]['new']['τιτλος'], 'New Title')

if __name__ == '__main__':
    unittest.main()