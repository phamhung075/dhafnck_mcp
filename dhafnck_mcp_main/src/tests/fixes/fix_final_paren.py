#!/usr/bin/env python3
"""
Fix final parenthesis issue
"""
import re
from pathlib import Path

files = [
    "src/tests/integration/test_json_fields.py",
    "src/tests/integration/test_orm_relationships.py",
]

for filepath in files:
    path = Path(filepath)
    if path.exists():
        with open(path, 'r') as f:
            content = f.read()
        
        # Fix the specific pattern "delegation_rules={}, )"
        content = re.sub(r"delegation_rules={},\s*\)", r"delegation_rules={}", content)
        
        with open(path, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")