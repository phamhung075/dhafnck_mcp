#!/usr/bin/env python3
"""
Generate a test Supabase JWT token for frontend authentication testing
"""

import os
import sys
sys.path.append('/home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src')

import jwt
from datetime import datetime, timedelta
import base64

# Supabase JWT secret from environment
SUPABASE_JWT_SECRET = "xQVwQQIPe9X00jzJT64CkDnt2/IDmst4TjzNDIVfg0T8ADxlsUZDK+SOtaBs6lYuEttroRNHIOGMPYmoyHHs7A=="

# Test user information
TEST_USER_ID = "65d733e9-04d6-4dda-9536-688c3a59448e"
TEST_USER_EMAIL = "testuser@example.com"

def generate_supabase_token():
    """Generate a valid Supabase JWT token for testing"""
    
    # Token payload compatible with Supabase format
    payload = {
        "aud": "authenticated",
        "exp": int((datetime.utcnow() + timedelta(days=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": "https://pmswmvxhzdfxeqsfdgif.supabase.co/auth/v1",
        "sub": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "phone": "",
        "app_metadata": {
            "provider": "email",
            "providers": ["email"]
        },
        "user_metadata": {
            "username": "testuser",
            "email": TEST_USER_EMAIL
        },
        "role": "authenticated",
        "aal": "aal1",
        "amr": [{"method": "password", "timestamp": int(datetime.utcnow().timestamp())}],
        "session_id": "12345678-1234-1234-1234-123456789012"
    }
    
    try:
        # Generate token using Supabase JWT secret
        token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")
        
        print("✅ Supabase JWT Token Generated Successfully!")
        print("=" * 80)
        print(f"Token: {token}")
        print("=" * 80)
        print(f"User ID: {payload['sub']}")
        print(f"Email: {payload['email']}")
        print(f"Expires: {datetime.fromtimestamp(payload['exp'])}")
        print("=" * 80)
        
        # Verify the token can be decoded
        decoded = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        print("✅ Token verification successful!")
        print(f"Decoded user: {decoded.get('sub')} ({decoded.get('email')})")
        
        # Output curl command for testing
        print("\n🧪 Test with curl:")
        print(f'curl -X GET "http://localhost:8000/api/v2/tasks/" -H "Authorization: Bearer {token}"')
        
        return token
        
    except Exception as e:
        print(f"❌ Error generating token: {e}")
        return None

if __name__ == "__main__":
    print("🔐 Generating Supabase JWT Token for Frontend Testing")
    print("=" * 80)
    
    token = generate_supabase_token()
    
    if token:
        print(f"\n💾 Save this token in browser cookies as 'access_token' to test the frontend:")
        print(f"document.cookie = 'access_token={token}; path=/; max-age=86400'")