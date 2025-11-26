def parse_table_data(html):
    """Parse the HTML content and extract relevant data from tables."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('tr')

    data = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 4:  # Ensure there are enough cells
            entry = {
                'αριθμος': cells[0].get_text(strip=True) if len(cells) > 0 else '',
                'κωδικος': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                'τιτλος': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                'ενεργη': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                'απευθυνεται': cells[4].get_text(strip=True) if len(cells) > 4 else '',
                'κατασταση': cells[5].get_text(strip=True) if len(cells) > 5 else ''
            }
            data.append(entry)

    return data