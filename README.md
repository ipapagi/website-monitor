# Website Monitor

A Python application that monitors websites for changes and sends notifications via Discord webhooks.

## Overview
Website Monitor is a Python project designed to monitor a specified URL for changes. It fetches the webpage, parses the relevant data, and notifies the user of any changes detected. This project is useful for tracking updates on government platforms, news sites, or any other web pages where timely information is crucial.

## Features
- Monitors a specified URL for changes at configurable intervals.
- Parses HTML content to extract relevant data from tables.
- Sends desktop notifications and plays alert sounds when changes are detected.
- Logs changes for historical reference.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Project Structure
```
website-monitor/
├── src/                  # Source code for the project
│   ├── __init__.py      # Marks the src directory as a Python package
│   ├── monitor.py       # Contains the PKMMonitor class for monitoring
│   ├── notifier.py      # Handles notification functionalities
│   ├── parser.py        # Responsible for parsing HTML content
│   └── utils.py         # Utility functions for logging and configuration
├── tests/                # Unit tests for the project
│   ├── __init__.py      # Marks the tests directory as a Python package
│   ├── test_monitor.py   # Unit tests for monitor.py
│   └── test_parser.py    # Unit tests for parser.py
├── logs/                 # Directory for log files
│   └── .gitkeep         # Keeps the logs directory in version control
├── data/                 # Directory for data files
│   └── .gitkeep         # Keeps the data directory in version control
├── config/               # Configuration files
│   └── config.yaml      # Configuration settings for the project
├── requirements.txt      # Project dependencies
├── .gitignore            # Files and directories to ignore in Git
├── setup.py              # Setup script for the project
└── README.md             # Documentation for the project
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd website-monitor
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the project by editing `config/config.yaml` to set the URL and check intervals.

## Usage

### Βασική χρήση - Continuous Monitoring
```bash
python -m src.main
```

### Αποθήκευση Baseline
Αποθηκεύει τις τρέχουσες ενεργές διαδικασίες ως baseline για μελλοντική σύγκριση:
```bash
python -m src.main --save-baseline
```

### Σύγκριση με Baseline
Συγκρίνει τις τρέχουσες διαδικασίες με το αποθηκευμένο baseline:
```bash
python -m src.main --compare
```

### Εμφάνιση Ενεργών Διαδικασιών
```bash
python -m src.main --list-active
```

### Συνδυασμός Παραμέτρων
```bash
# Αποθήκευση baseline και εμφάνιση ενεργών
python -m src.main --save-baseline --list-active

# Σύγκριση και εμφάνιση
python -m src.main --compare --list-active
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.