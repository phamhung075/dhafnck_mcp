#!/usr/bin/env python3
"""Manual test to verify context loading fix using existing data"""

import json

# Test using the manage_task tool

print("\n=== Testing Context Auto-loading with Existing Data ===\n")

# Test data from the RESUME_CONTEXT_AUTOLOAD_ISSUE.md
task_id = "fa3b7a54002e47d7a414f28a116ac3ca"
git_branch_id = "ea4b6c35-9e6a-449c-b48e-9f35fc34b297"

print("1. Testing GET action with context auto-loading...")
print(f"   Task ID: {task_id}")

# Create the request for get action
get_request = {
    "action": "get",
    "task_id": task_id
}

print(f"\nRequest: {json.dumps(get_request, indent=2)}")
print("\nExpected behavior:")
print("- context_available should be True (not False)")
print("- context_data should contain actual context data (not null)")
print("- The fix should check context_response.context field, not just context_response.data")

print("\n2. Testing NEXT action with context auto-loading...")
print(f"   Git Branch ID: {git_branch_id}")

# Create the request for next action
next_request = {
    "action": "next", 
    "git_branch_id": git_branch_id
}

print(f"\nRequest: {json.dumps(next_request, indent=2)}")
print("\nExpected behavior:")
print("- Task should include context_available: true")
print("- Task should include context_data with actual data")

print("\n=== Summary of Fix ===")
print("The issue was in get_task.py and next_task.py use cases:")
print("- They were checking context_response.data")
print("- But the context service returns data in context_response.context")
print("- Fixed by checking both fields with context_response.context as primary")

print("\nTo verify manually:")
print("1. Use manage_task tool with the GET request above")
print("2. Check that context_available is true and context_data is not null")
print("3. Use manage_task tool with the NEXT request above")
print("4. Check that the returned task has context loaded")