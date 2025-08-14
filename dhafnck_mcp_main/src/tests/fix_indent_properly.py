"""Fix indentation properly by analyzing the structure"""

# Read the file
with open("/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/subtask_mcp_controller.py", "r") as f:
    lines = f.readlines()

# Find lines that need fixing based on their content
fixed_lines = []
for i, line in enumerate(lines):
    line_num = i + 1
    
    # Lines that are part of the try block content (after the try at line 695)
    # and before the except at line 824
    if 723 <= line_num <= 823:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        # Determine correct indentation based on content
        if stripped.startswith("# Add"):
            # Comments should be at 24 spaces
            fixed_lines.append(" " * 24 + stripped)
        elif stripped.startswith("if "):
            # if statements at this level should be at 24 spaces
            fixed_lines.append(" " * 24 + stripped)
        elif stripped.startswith("for "):
            # for loops inside if should be at 28 spaces
            if "if " in lines[i-1] or "if " in lines[i-2]:
                fixed_lines.append(" " * 28 + stripped)
            else:
                fixed_lines.append(" " * 24 + stripped)
        elif stripped.startswith("deliverables_str") or stripped.startswith("quality_info"):
            # Variable assignments inside if should be at 28 spaces
            fixed_lines.append(" " * 28 + stripped)
        elif stripped.startswith("self._context_facade"):
            # Method calls - determine based on context
            if current_indent < 28:
                fixed_lines.append(" " * 28 + stripped)
            else:
                fixed_lines.append(" " * 32 + stripped)
        elif stripped.startswith("insight_data") or stripped.startswith("skill_data") or stripped.startswith("challenge_data") or stripped.startswith("rec_data"):
            # Dictionary definitions inside for loops
            fixed_lines.append(" " * 32 + stripped)
        elif stripped.startswith('"'):
            # Dictionary keys/values - preserve relative indentation
            if current_indent == 36:
                fixed_lines.append(" " * 36 + stripped)
            elif current_indent == 40:
                fixed_lines.append(" " * 40 + stripped)
            else:
                fixed_lines.append(" " * 32 + stripped)
        elif stripped.startswith("}"):
            # Closing braces
            if current_indent == 32:
                fixed_lines.append(" " * 32 + stripped)
            elif current_indent == 36:
                fixed_lines.append(" " * 36 + stripped)
            else:
                fixed_lines.append(" " * 28 + stripped)
        elif stripped.startswith("result["):
            # Result assignments
            fixed_lines.append(" " * 24 + stripped)
        elif stripped.startswith("list_result") or stripped.startswith("subtasks") or stripped.startswith("all_complete"):
            # Variables at main level
            fixed_lines.append(" " * 28 + stripped)
        elif stripped.startswith("action=") or stripped.startswith("task_id="):
            # Function parameters
            fixed_lines.append(" " * 28 + stripped)
        elif stripped.startswith(")"):
            # Closing parentheses - match opening
            fixed_lines.append(" " * 24 + stripped)
        elif not stripped:
            # Empty lines
            fixed_lines.append(line)
        else:
            # Default - maintain relative structure
            fixed_lines.append(" " * 24 + stripped)
    else:
        fixed_lines.append(line)

# Write back
with open("/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/subtask_mcp_controller.py", "w") as f:
    f.writelines(fixed_lines)

print("Fixed indentation with proper structure")