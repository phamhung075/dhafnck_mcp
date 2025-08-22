#!/usr/bin/env python3
"""
Test Supabase JWT validation directly
"""

import os
import sys
sys.path.append('/home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src')

import jwt
from datetime import datetime, timedelta

# Test token from our generation script
test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU1OTcwODQ3LCJpYXQiOjE3NTU4ODQ0NDcsImlzcyI6Imh0dHBzOi8vcG1zd212eGh6ZGZ4ZXFzZmRnaWYuc3VwYWJhc2UuY28vYXV0aC92MSIsInN1YiI6IjY1ZDczM2U5LTA0ZDYtNGRkYS05NTM2LTY4OGMzYTU5NDQ4ZSIsImVtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7InVzZXJuYW1lIjoidGVzdHVzZXIiLCJlbWFpbCI6InRlc3R1c2VyQGV4YW1wbGUuY29tIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NTU4ODQ0NDd9XSwic2Vzc2lvbl9pZCI6IjEyMzQ1Njc4LTEyMzQtMTIzNC0xMjM0LTEyMzQ1Njc4OTAxMiJ9.NRTRq3d4uVM9PHrqvwkvCA9QXdyHtaXWvx_hcH-dai8"

# Supabase JWT secret from .env
supabase_jwt_secret = "xQVwQQIPe9X00jzJT64CkDnt2/IDmst4TjzNDIVfg0T8ADxlsUZDK+SOtaBs6lYuEttroRNHIOGMPYmoyHHs7A=="

# Local JWT secret from .env  
local_jwt_secret = "dGhpcyBpcyBhIGR1bW15IGp3dCBzZWNyZXQgZm9yIGRldmVsb3BtZW50"

def test_validation():
    print("🔍 Testing JWT Validation")
    print("=" * 80)
    
    print(f"Token (first 50 chars): {test_token[:50]}...")
    print(f"Supabase secret length: {len(supabase_jwt_secret)}")
    print(f"Local secret length: {len(local_jwt_secret)}")
    print()
    
    # Test 1: Local JWT validation
    print("1️⃣ Testing LOCAL JWT validation...")
    try:
        payload = jwt.decode(test_token, local_jwt_secret, algorithms=["HS256"])
        print("✅ LOCAL validation successful!")
        print(f"   User: {payload.get('sub')} ({payload.get('email')})")
    except Exception as e:
        print(f"❌ LOCAL validation failed: {e}")
    
    print()
    
    # Test 2: Supabase JWT validation (strict)
    print("2️⃣ Testing SUPABASE JWT validation (strict)...")
    try:
        payload = jwt.decode(test_token, supabase_jwt_secret, algorithms=["HS256"])
        print("✅ SUPABASE validation successful!")
        print(f"   User: {payload.get('sub')} ({payload.get('email')})")
        print(f"   Payload keys: {list(payload.keys())}")
    except Exception as e:
        print(f"❌ SUPABASE validation failed: {e}")
    
    print()
    
    # Test 3: Supabase JWT validation (permissive)
    print("3️⃣ Testing SUPABASE JWT validation (permissive)...")
    try:
        payload = jwt.decode(
            test_token,
            supabase_jwt_secret,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_aud": False,
                "verify_iss": False,
                "verify_exp": False,
                "verify_iat": False,
                "verify_nbf": False,
                "require_exp": False,
                "require_iat": False,
                "require_nbf": False
            }
        )
        print("✅ SUPABASE validation (permissive) successful!")
        print(f"   User: {payload.get('sub')} ({payload.get('email')})")
        print(f"   Payload keys: {list(payload.keys())}")
    except Exception as e:
        print(f"❌ SUPABASE validation (permissive) failed: {e}")
    
    print()
    
    # Test 4: Decode without verification to see payload
    print("4️⃣ Decoding WITHOUT verification to inspect payload...")
    try:
        payload = jwt.decode(test_token, options={"verify_signature": False})
        print("✅ Payload decoded successfully!")
        print(f"   Full payload: {payload}")
    except Exception as e:
        print(f"❌ Payload decode failed: {e}")

if __name__ == "__main__":
    test_validation()