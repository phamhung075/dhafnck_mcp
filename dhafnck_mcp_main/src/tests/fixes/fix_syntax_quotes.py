#!/usr/bin/env python3
"""Fix escaped quotes syntax errors"""
import re
from pathlib import Path

def fix_escaped_quotes(content):
    """Fix escaped quotes in docstrings"""
    # Fix escaped triple quotes in docstrings
    content = re.sub(r'\\"\\"\\"', '"""', content)
    # Fix escaped single quotes in docstrings  
    content = re.sub(r"\\'", "'", content)
    return content

# Fix all test files
test_dir = Path("src/tests")
for test_file in test_dir.rglob("test_*.py"):
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        
        fixed = fix_escaped_quotes(content)
        
        if fixed != content:
            with open(test_file, 'w') as f:
                f.write(fixed)
            print(f"Fixed: {test_file}")
    except Exception as e:
        print(f"Error with {test_file}: {e}")