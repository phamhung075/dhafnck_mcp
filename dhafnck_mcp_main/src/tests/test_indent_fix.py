"""Helper script to fix indentation in subtask_mcp_controller.py"""

import re

# Read the file
with open("/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/subtask_mcp_controller.py", "r") as f:
    lines = f.readlines()

# Fix indentation from line 723 to 823 (inside the try block)
fixed_lines = []
for i, line in enumerate(lines):
    if i < 722 or i > 822:
        fixed_lines.append(line)
    else:
        # These lines should be indented by 24 spaces (6 levels of 4 spaces)
        # Currently they have 20 spaces, so add 4 more
        if line.strip() and not line.startswith("                        "):
            # Add 4 spaces to lines that don't have enough indentation
            fixed_lines.append("    " + line)
        else:
            fixed_lines.append(line)

# Write back
with open("/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/subtask_mcp_controller.py", "w") as f:
    f.writelines(fixed_lines)

print("Fixed indentation")