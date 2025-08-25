#!/usr/bin/env python3
"""Test JWT authentication and context creation"""

import os
import sys
import json
import jwt
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, '/home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src')

# Load environment
from dotenv import load_dotenv
load_dotenv('/home/daihungpham/__projects__/agentic-project/.env')

# Get JWT secret
JWT_SECRET = os.getenv('JWT_SECRET_KEY')
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')

print("=" * 80)
print("JWT Configuration Test")
print("=" * 80)
print(f"JWT_SECRET_KEY length: {len(JWT_SECRET) if JWT_SECRET else 0}")
print(f"SUPABASE_JWT_SECRET length: {len(SUPABASE_JWT_SECRET) if SUPABASE_JWT_SECRET else 0}")
print(f"Secrets match: {JWT_SECRET == SUPABASE_JWT_SECRET}")
print()

# Create a test token
test_user_id = "test-user-123"
test_email = "test@example.com"

# Create token payload
payload = {
    "sub": test_user_id,
    "email": test_email,
    "user_id": test_user_id,
    "iat": datetime.utcnow(),
    "exp": datetime.utcnow() + timedelta(hours=1),
    "token_type": "access",
    "roles": ["user"],
    "iss": "https://pmswmvxhzdfxeqsfdgif.supabase.co/auth/v1",
    # No audience claim - it's disabled
}

# Sign token
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
print("Generated test token:")
print(f"Token (first 50 chars): {token[:50]}...")
print()

# Test decoding
try:
    decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": True, "verify_aud": False})
    print("✅ Token decoded successfully:")
    print(json.dumps(decoded, indent=2, default=str))
except Exception as e:
    print(f"❌ Token decode failed: {e}")

print()
print("=" * 80)
print("Testing Context Creation with JWT")
print("=" * 80)

import requests

# Test health endpoint first (no auth required)
response = requests.get("http://localhost:8000/health")
print(f"Health check (no auth): {response.status_code}")

# Test authenticated endpoint
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Try to create a project context
project_id = "test-project-001"
context_data = {
    "level": "project",
    "context_id": project_id,
    "data": {
        "project_name": "Test Project",
        "description": "Testing JWT authentication and context creation",
        "created_at": datetime.utcnow().isoformat(),
        "created_by": test_user_id
    }
}

print(f"\nCreating project context for project_id: {project_id}")
print(f"User ID: {test_user_id}")

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
    if "user_id" in result:
        if result["user_id"] == test_user_id:
            print(f"\n✅ CORRECT: Context saved with user_id: {result['user_id']}")
        else:
            print(f"\n❌ PROBLEM: Context saved with user_id: {result['user_id']} (expected: {test_user_id})")
else:
    print(f"❌ Failed to get context: {get_response.text}")