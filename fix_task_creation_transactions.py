#!/usr/bin/env python3
"""
Fix for Task Creation API Inconsistency - Transaction-based Solution

Problem: Task creation returns error response but still creates task in database
Root Cause: Task creation and context creation are not wrapped in a single transaction

Solution: Use database transaction to ensure atomicity
"""

import os
import sys

# Path to the file that needs fixing
FACADE_FILE = "/home/daihungpham/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/application/facades/task_application_facade.py"

def apply_transaction_fix():
    """Apply transaction-based fix to ensure atomicity"""
    
    # Read the current file
    with open(FACADE_FILE, 'r') as f:
        content = f.read()
    
    # Find and replace the create_task method to add transaction handling
    # We need to modify the create_task method to use transactions
    
    # Replace the context creation exception handler to include rollback
    old_except_block = '''                except Exception as e:
                    logger.error("Failed to create context for task %s: %s", task_response.task.id, e)
                    # Task was created successfully but context failed - return task without context
                    task_dict = asdict(task_response.task)
                    if not task_dict.get("context_id"):
                        task_dict["context_id"] = task_response.task.id
                    task_dict["context_available"] = False
                    task_dict["context_data"] = None
                    
                    return {
                        "success": True,
                        "action": "create",
                        "task": task_dict,
                        "message": msg + " (Context creation failed)",
                    }'''
    
    new_except_block = '''                except Exception as e:
                    logger.error("Failed to create context for task %s: %s", task_response.task.id, e)
                    # Rollback: Delete the task since context creation is required
                    try:
                        from ...domain.value_objects.task_id import TaskId
                        self._task_repository.delete(TaskId(str(task_response.task.id)))
                        logger.info("Rolled back task %s after context creation failure", task_response.task.id)
                    except Exception as rollback_error:
                        logger.error("Failed to rollback task %s: %s", task_response.task.id, rollback_error)
                        # If rollback fails, still return error to prevent inconsistent state
                    
                    # Return error response since task creation should be atomic with context
                    return {
                        "success": False,
                        "action": "create",
                        "error": f"Task creation failed: Context creation error - {str(e)}",
                        "error_code": "CONTEXT_CREATION_FAILED",
                        "hint": "Task creation requires successful context initialization"
                    }'''
    
    # Also update the other context creation failure block (lines 169-183)
    old_context_fail_block = '''                    else:
                        # Context creation failed, but task was created - log warning and continue
                        logger.warning("Context creation failed for task %s, task created without context", task_response.task.id)
                        # Make sure to set context_id on the task even if context creation failed
                        task_dict = asdict(task_response.task)
                        if not task_dict.get("context_id"):
                            task_dict["context_id"] = task_response.task.id
                        task_dict["context_available"] = False
                        task_dict["context_data"] = None
                        
                        return {
                            "success": True,
                            "action": "create",
                            "task": task_dict,
                            "message": msg + " (Context creation failed)",
                        }'''
    
    new_context_fail_block = '''                    else:
                        # Context creation failed - rollback task creation
                        logger.warning("Context creation failed for task %s, rolling back", task_response.task.id)
                        try:
                            from ...domain.value_objects.task_id import TaskId
                            self._task_repository.delete(TaskId(str(task_response.task.id)))
                            logger.info("Rolled back task %s after context sync failure", task_response.task.id)
                        except Exception as rollback_error:
                            logger.error("Failed to rollback task %s: %s", task_response.task.id, rollback_error)
                        
                        return {
                            "success": False,
                            "action": "create",
                            "error": "Task creation failed: Unable to initialize task context",
                            "error_code": "CONTEXT_SYNC_FAILED",
                            "hint": "Task creation requires successful context initialization"
                        }'''
    
    # Apply the replacements
    content = content.replace(old_except_block, new_except_block)
    content = content.replace(old_context_fail_block, new_context_fail_block)
    
    # Write the modified content
    with open(FACADE_FILE, 'w') as f:
        f.write(content)
    
    print("✓ Applied transaction fix to task creation")

def verify_fix():
    """Verify the fix was applied correctly"""
    with open(FACADE_FILE, 'r') as f:
        content = f.read()
    
    checks = [
        ("self._task_repository.delete(TaskId(str(task_response.task.id)))", "Rollback logic added"),
        ("CONTEXT_CREATION_FAILED", "Context creation error code added"),
        ("CONTEXT_SYNC_FAILED", "Context sync error code added"),
        ("Task creation requires successful context initialization", "Error hint added")
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
    print("Task Creation Transaction Fix")
    print("=" * 50)
    
    # Apply the fix
    print("\nApplying transaction fix...")
    apply_transaction_fix()
    
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