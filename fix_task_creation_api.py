#!/usr/bin/env python3
"""
Fix for Task Creation API Inconsistency

Problem: Task creation returns error response but still creates task in database
Root Cause: Task creation and context creation are not wrapped in a single transaction

Solution: Implement proper transaction boundaries to ensure atomicity
"""

import os
import sys

# Path to the file that needs fixing
FACADE_FILE = "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/application/facades/task_application_facade.py"

def create_backup(file_path):
    """Create a backup of the original file"""
    backup_path = file_path + ".backup"
    if not os.path.exists(backup_path):
        with open(file_path, 'r') as original:
            content = original.read()
        with open(backup_path, 'w') as backup:
            backup.write(content)
        print(f"✓ Created backup: {backup_path}")
    else:
        print(f"⚠️  Backup already exists: {backup_path}")

def apply_fix():
    """Apply the fix to ensure transaction atomicity"""
    
    # Read the current file
    with open(FACADE_FILE, 'r') as f:
        lines = f.readlines()
    
    # Find the create_task method and modify it
    in_create_task = False
    modified_lines = []
    indent_level = ""
    
    for i, line in enumerate(lines):
        # Detect the start of create_task method
        if "def create_task(self, request: CreateTaskRequest)" in line:
            in_create_task = True
            # Get the indentation level
            indent_level = line[:line.index("def")]
        
        # If we're at the try block in create_task
        if in_create_task and line.strip().startswith("try:"):
            # Insert comment about transaction handling
            modified_lines.append(line)
            modified_lines.append(f"{indent_level}        # Note: Task creation and context creation need to be atomic\n")
            modified_lines.append(f"{indent_level}        # We'll track if task was created to handle rollback if needed\n")
            modified_lines.append(f"{indent_level}        task_created = False\n")
            modified_lines.append(f"{indent_level}        created_task_id = None\n")
            continue
            
        # If we find where task is created successfully
        if in_create_task and "task_response = self._create_task_use_case.execute(request)" in line:
            modified_lines.append(line)
            # Add tracking after task creation
            next_line_index = i + 1
            if next_line_index < len(lines):
                modified_lines.append(lines[next_line_index])  # Add the empty line or next line
                modified_lines.append(f"{indent_level}            # Track that task was created\n")
                modified_lines.append(f"{indent_level}            if task_response and getattr(task_response, 'success', False):\n")
                modified_lines.append(f"{indent_level}                task_created = True\n")
                modified_lines.append(f"{indent_level}                created_task_id = task_response.task.id\n")
                continue
            
        # If we're in the context creation exception handler
        if in_create_task and "except Exception as e:" in line and "Failed to create context" in lines[i+1]:
            modified_lines.append(line)
            # Get the proper indentation for this except block
            except_indent = line[:line.index("except")]
            # Add rollback logic
            modified_lines.append(f"{except_indent}    logger.error(\"Failed to create context for task %s: %s\", task_response.task.id, e)\n")
            modified_lines.append(f"{except_indent}    # Rollback: Delete the task since context creation failed\n")
            modified_lines.append(f"{except_indent}    if task_created and created_task_id:\n")
            modified_lines.append(f"{except_indent}        try:\n")
            modified_lines.append(f"{except_indent}            from ...domain.value_objects.task_id import TaskId\n")
            modified_lines.append(f"{except_indent}            self._task_repository.delete(TaskId(created_task_id))\n")
            modified_lines.append(f"{except_indent}            logger.info(\"Rolled back task %s after context creation failure\", created_task_id)\n")
            modified_lines.append(f"{except_indent}        except Exception as rollback_error:\n")
            modified_lines.append(f"{except_indent}            logger.error(\"Failed to rollback task %s: %s\", created_task_id, rollback_error)\n")
            modified_lines.append(f"{except_indent}    \n")
            modified_lines.append(f"{except_indent}    # Return error response\n")
            modified_lines.append(f"{except_indent}    return {{\n")
            modified_lines.append(f"{except_indent}        \"success\": False,\n")
            modified_lines.append(f"{except_indent}        \"action\": \"create\",\n")
            modified_lines.append(f"{except_indent}        \"error\": f\"Task creation failed: {{str(e)}}\",\n")
            modified_lines.append(f"{except_indent}        \"error_code\": \"TRANSACTION_FAILED\",\n")
            modified_lines.append(f"{except_indent}        \"hint\": \"Both task and context creation must succeed\"\n")
            modified_lines.append(f"{except_indent}    }}\n")
            # Skip the original error handling lines
            while i < len(lines) - 1 and "return {" not in lines[i+1]:
                i += 1
            continue
            
        # Check if we've exited the create_task method
        if in_create_task and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
            in_create_task = False
            
        modified_lines.append(line)
    
    # Write the modified content
    with open(FACADE_FILE, 'w') as f:
        f.writelines(modified_lines)
    
    print("✓ Applied transaction fix to task creation")

def verify_fix():
    """Verify the fix was applied correctly"""
    with open(FACADE_FILE, 'r') as f:
        content = f.read()
    
    checks = [
        ("task_created = False", "Task creation tracking added"),
        ("self._task_repository.delete(TaskId(created_task_id))", "Rollback logic added"),
        ("TRANSACTION_FAILED", "Proper error code added")
    ]
    
    all_good = True
    for check_str, description in checks:
        if check_str in content:
            print(f"✓ {description}")
        else:
            print(f"✗ {description} - NOT FOUND")
            all_good = False
    
    return all_good

def main():
    print("Task Creation API Inconsistency Fix")
    print("=" * 50)
    
    # Create backup
    create_backup(FACADE_FILE)
    
    # Apply the fix
    print("\nApplying fix...")
    apply_fix()
    
    # Verify the fix
    print("\nVerifying fix...")
    if verify_fix():
        print("\n✅ Fix applied successfully!")
        print("\nNext steps:")
        print("1. Restart the Docker container:")
        print("   cd /home/daihungpham/agentic-project/dhafnck_mcp_main/docker")
        print("   docker-compose restart dhafnck-mcp")
        print("2. Test task creation to verify the fix works")
    else:
        print("\n❌ Fix verification failed!")
        print("Please check the modifications manually.")

if __name__ == "__main__":
    main()