#!/usr/bin/env python3
"""Test JWT authentication and context creation with Supabase"""

import os
import sys
import json
import requests
from datetime import datetime

# Add src to path
sys.path.insert(0, '/home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src')

# Load environment
from dotenv import load_dotenv
load_dotenv('/home/daihungpham/__projects__/agentic-project/.env')

# Get Supabase config
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

print("=" * 80)
print("Supabase Authentication and Context Test")
print("=" * 80)
print(f"Supabase URL: {SUPABASE_URL}")
print()

# First, sign up or sign in with Supabase to get a real token
test_email = "testcontext@gmail.com"
test_password = "TestPassword123!"

print(f"Attempting to sign in with: {test_email}")

# Try to sign in first
signin_response = requests.post(
    f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    headers={
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    },
    json={
        "email": test_email,
        "password": test_password
    }
)

if signin_response.status_code == 200:
    print("✅ Signed in successfully")
    auth_data = signin_response.json()
else:
    print(f"Sign in failed ({signin_response.status_code}), trying to sign up...")
    
    # Try to sign up
    signup_response = requests.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        },
        json={
            "email": test_email,
            "password": test_password
        }
    )
    
    if signup_response.status_code in [200, 201]:
        print("✅ Signed up successfully")
        auth_data = signup_response.json()
    else:
        print(f"❌ Sign up failed: {signup_response.status_code}")
        print(signup_response.text)
        sys.exit(1)

# Extract token and user info
access_token = auth_data.get("access_token")
user = auth_data.get("user", {})
user_id = user.get("id")

print(f"User ID: {user_id}")
print(f"Access Token (first 50 chars): {access_token[:50]}...")
print()

# Test creating a context with the real Supabase token
print("=" * 80)
print("Testing Context Creation with Supabase JWT")
print("=" * 80)

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Create a project context
project_id = f"project-{datetime.now().isoformat()}"
context_data = {
    "level": "project",
    "context_id": project_id,
    "data": {
        "project_name": "Test Project via Supabase",
        "description": "Testing JWT authentication with real Supabase token",
        "created_at": datetime.now().isoformat(),
        "created_by": user_id
    }
}

print(f"Creating project context for project_id: {project_id}")
print(f"User ID: {user_id}")

response = requests.post(
    "http://localhost:8000/api/v2/contexts/project",
    headers=headers,
    json=context_data
)

print(f"Response status: {response.status_code}")
if response.status_code == 200:
    print("✅ Context created successfully!")
    result = response.json()
    print(json.dumps(result, indent=2))
else:
    print(f"❌ Failed to create context: {response.text}")

# Try to get the context back
print("\n" + "=" * 80)
print("Retrieving Created Context")
print("=" * 80)

get_response = requests.get(
    f"http://localhost:8000/api/v2/contexts/project/{project_id}",
    headers=headers
)

print(f"Get context status: {get_response.status_code}")
if get_response.status_code == 200:
    print("✅ Context retrieved successfully!")
    result = get_response.json()
    print(json.dumps(result, indent=2))
    
    # Check user_id
    context = result.get("context", {})
    if context.get("user_id") == user_id:
        print(f"\n✅ CORRECT: Context saved with user_id: {context.get('user_id')}")
    else:
        print(f"\n❌ PROBLEM: Context saved with user_id: {context.get('user_id')} (expected: {user_id})")
else:
    print(f"❌ Failed to get context: {get_response.text}")

# Clean up - list all contexts for this user
print("\n" + "=" * 80)
print("Listing User's Contexts")
print("=" * 80)

list_response = requests.get(
    "http://localhost:8000/api/v2/contexts/project/list",
    headers=headers
)

print(f"List contexts status: {list_response.status_code}")
if list_response.status_code == 200:
    result = list_response.json()
    print(f"Found {result.get('count', 0)} project contexts for user {result.get('user', 'unknown')}")
    if result.get('contexts'):
        for ctx in result['contexts']:
            print(f"  - {ctx.get('context_id')}: {ctx.get('data', {}).get('project_name', 'Unnamed')}")
else:
    print(f"Failed to list contexts: {list_response.text}")