#!/usr/bin/env python3
"""
Batch update all test scripts to use src_setup.py for path configuration.

This script finds all sys.path.insert patterns and replaces them with:
    from src_setup import *
"""

import os
import re
from pathlib import Path

def update_script(filepath):
    """Update a single script to use src_setup"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Pattern 1: sys.path.insert(0, 'src')
    content = re.sub(
        r"^sys\.path\.insert\(0, ['\"]\.?/?src['\"]?\)",
        "",
        content,
        flags=re.MULTILINE
    )
    
    # Pattern 2: sys.path.insert(0, os.path.join(...))
    content = re.sub(
        r"^sys\.path\.insert\(0, os\.path\.join\([^)]+\)\)",
        "",
        content,
        flags=re.MULTILINE
    )
    
    # Remove extra blank lines that might have been created
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    # If we made changes and don't have src_setup import, add it
    if content != original and 'from src_setup import' not in content:
        # Find the first import line
        import_match = re.search(r'^(from|import)\s', content, re.MULTILINE)
        if import_match:
            # Insert before first import
            insert_pos = import_match.start()
            # But after the shebang and docstring
            lines = content[:insert_pos].split('\n')
            insert_line = len(lines) - 1
            
            new_lines = content.split('\n')
            new_lines.insert(insert_line, '')
            new_lines.insert(insert_line, '# Setup path for imports')
            new_lines.insert(insert_line + 1, 'from src_setup import *')
            content = '\n'.join(new_lines)
    
    # Write back if changed
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    tests_dir = Path(__file__).parent
    
    count = 0
    for pyfile in tests_dir.glob('*.py'):
        if pyfile.name in ['__init__.py', 'src_setup.py', 'MIGRATION_NOTES.py']:
            continue
        
        if update_script(str(pyfile)):
            count += 1
            print(f"  ✓ Updated: {pyfile.name}")
    
    print(f"\n✅ Updated {count} scripts")


if __name__ == '__main__':
    main()
