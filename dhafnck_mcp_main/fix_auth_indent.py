#!/usr/bin/env python3
"""Fix indentation in mcp_entry_point.py auth tools section"""

import re

with open('src/fastmcp/server/mcp_entry_point.py', 'r') as f:
    content = f.read()

# Find the auth tools section and fix indentation
lines = content.split('\n')
fixed_lines = []
in_auth_block = False
indent_level = 0

for i, line in enumerate(lines):
    if 'if auth_enabled:' in line and 'Add authentication tools' in lines[i-1]:
        in_auth_block = True
        indent_level = 0
        fixed_lines.append(line)
    elif in_auth_block:
        if line.strip().startswith('@server.tool()'):
            indent_level = 2  # Two levels of indentation (if block + function)
            fixed_lines.append('        ' + line.strip())
        elif line.strip().startswith('async def ') or line.strip().startswith('def '):
            fixed_lines.append('        ' + line.strip())
        elif line.strip() == '"""' or (line.strip().startswith('"""') and line.strip().endswith('"""')):
            fixed_lines.append('            ' + line.strip())
        elif in_auth_block and line.strip() and not line.strip().startswith('#'):
            # Count leading spaces to determine relative indentation
            stripped = line.lstrip()
            if stripped.startswith('try:') or stripped.startswith('except ') or stripped.startswith('finally:'):
                fixed_lines.append('            ' + stripped)
            elif stripped.startswith('return ') or stripped.startswith('if ') or stripped.startswith('elif ') or stripped.startswith('else:'):
                if lines[i-1].strip().startswith('try:') or lines[i-1].strip().startswith('except'):
                    fixed_lines.append('                ' + stripped)
                else:
                    fixed_lines.append('            ' + stripped)
            elif stripped.startswith('"'):
                # Multiline string continuation
                fixed_lines.append('            ' + stripped)
            elif stripped == '}' or stripped.startswith('}'):
                # Closing brace for dict
                fixed_lines.append('                ' + stripped)
            else:
                # Default indentation for content inside functions
                fixed_lines.append('                ' + stripped)
        elif line.strip().startswith('# Add HTTP health'):
            in_auth_block = False
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Write back
with open('src/fastmcp/server/mcp_entry_point.py', 'w') as f:
    f.write('\n'.join(fixed_lines))

print("Fixed indentation in auth tools section")