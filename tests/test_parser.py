import os
import sys
import pytest

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from parser import PKMParser  # Assuming PKMParser is the class responsible for parsing in parser.py

def test_parse_table_data_valid():
    html_content = """
    <table>
        <tr>
            <td>1</td>
            <td>ABC123</td>
            <td>Test Title 1</td>
            <td>Active</td>
            <td>Public</td>
            <td>Open</td>
        </tr>
        <tr>
            <td>2</td>
            <td>DEF456</td>
            <td>Test Title 2</td>
            <td>Inactive</td>
            <td>Private</td>
            <td>Closed</td>
        </tr>
    </table>
    """
    expected_output = [
        {
            'αριθμος': '1',
            'κωδικος': 'ABC123',
            'τιτλος': 'Test Title 1',
            'ενεργη': 'Active',
            'απευθυνεται': 'Public',
            'κατασταση': 'Open'
        },
        {
            'αριθμος': '2',
            'κωδικος': 'DEF456',
            'τιτλος': 'Test Title 2',
            'ενεργη': 'Inactive',
            'απευθυνεται': 'Private',
            'κατασταση': 'Closed'
        }
    ]
    
    parser = PKMParser()
    result = parser.parse_table_data(html_content)
    assert result == expected_output

def test_parse_table_data_empty():
    html_content = "<table></table>"
    expected_output = []
    
    parser = PKMParser()
    result = parser.parse_table_data(html_content)
    assert result == expected_output

def test_parse_table_data_invalid_structure():
    html_content = """
    <table>
        <tr>
            <td>1</td>
            <td>ABC123</td>
        </tr>
    </table>
    """
    expected_output = []
    
    parser = PKMParser()
    result = parser.parse_table_data(html_content)
    assert result == expected_output

def test_parse_table_data_with_missing_cells():
    html_content = """
    <table>
        <tr>
            <td>1</td>
            <td>ABC123</td>
            <td>Test Title 1</td>
            <td>Active</td>
        </tr>
    </table>
    """
    expected_output = [
        {
            'αριθμος': '1',
            'κωδικος': 'ABC123',
            'τιτλος': 'Test Title 1',
            'ενεργη': 'Active',
            'απευθυνεται': '',
            'κατασταση': ''
        }
    ]
    
    parser = PKMParser()
    result = parser.parse_table_data(html_content)
    assert result == expected_output