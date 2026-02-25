# Running Test Scripts

All test, check, debug, and analyze scripts have moved to `src/tests/`.

## Option 1: Run from src/tests/ directory

```bash
cd src/tests
python get_case_details.py 105139
python search_protocol.py 793923
python test_something.py
```

## Option 2: Run with Python module notation (from project root)

```bash
python -m src.tests.get_case_details 105139
python -m src.tests.search_protocol 793923
python -m src.tests.test_something
```

## Option 3: Run via wrapper scripts (from project root)

Wrapper scripts exist in root for convenience:
```bash
python get_case_details.py 105139      # Redirects to src/tests/
python search_protocol.py 793923        # Redirects to src/tests/
```

---

## Script Organization

### Test Scripts (src/tests/)
- `test_*.py` - Functional tests
- `check_*.py` - Data validation checks  
- `debug_*.py` - Debugging utilities
- `analyze_*.py` - Analysis scripts
- `search_*.py` - Search utilities
- `deep_*.py` - Deep investigation scripts

### Wrapper Scripts (root) - OPTIONAL
- For convenience, thin wrappers can exist in root that import from src/tests/
- Example: root `get_case_details.py` imports and runs `src.tests.get_case_details`

---

## Python Path Setup

All scripts in `src/tests/` automatically have the parent `src/` directory in `sys.path` via `__init__.py`:

```python
# In src/tests/__init__.py
sys.path.insert(0, os.path.join(project_root, 'src'))
```

This means imports work transparently:
```python
from monitor import PKMMonitor        # ✅ Works
from charges import fetch_charges     # ✅ Works
```

No need for relative imports or manual path manipulation.
