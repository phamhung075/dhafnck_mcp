#!/usr/bin/env python3
"""Fix import errors in application services"""

import os
import re

# Directory to fix
services_dir = "src/fastmcp/task_management/application/services/"

# Pattern to fix
old_pattern = re.compile(r'from \.\.\.use_cases\.')
new_prefix = 'from ..use_cases.'

# Files to fix
files_to_fix = [
    "task_context_sync_service.py",
    "subtask_application_service.py", 
    "rule_application_service.py",
    "project_application_service.py",
    "git_branch_application_service.py"
]

for filename in files_to_fix:
    filepath = os.path.join(services_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Replace the pattern
        new_content = old_pattern.sub(new_prefix, content)
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Fixed imports in {filename}")
        else:
            print(f"No changes needed in {filename}")
    else:
        print(f"File not found: {filepath}")

print("Import fixing complete!")