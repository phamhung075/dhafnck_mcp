#!/usr/bin/env python3
"""
Debug script to test JWT authentication step by step
"""

import os
import sys
import jwt
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test token from environment variable or logs
TEST_TOKEN = os.getenv("TEST_JWT_TOKEN", "")

def test_environment():
    """Test 1: Check environment variables"""
    print("\n" + "="*80)
    print("TEST 1: Environment Variables")
    print("="*80)
    
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    supabase_secret = os.getenv("SUPABASE_JWT_SECRET")
    
    print(f"JWT_SECRET_KEY exists: {bool(jwt_secret)}")
    print(f"JWT_SECRET_KEY length: {len(jwt_secret) if jwt_secret else 0}")
    print(f"SUPABASE_JWT_SECRET exists: {bool(supabase_secret)}")
    print(f"SUPABASE_JWT_SECRET length: {len(supabase_secret) if supabase_secret else 0}")
    
    if jwt_secret and supabase_secret:
        print(f"Secrets are same: {jwt_secret == supabase_secret}")
    
    return jwt_secret, supabase_secret


def test_decode_token(jwt_secret, supabase_secret):
    """Test 2: Decode token with different secrets"""
    print("\n" + "="*80)
    print("TEST 2: Token Decoding")
    print("="*80)
    
    # Decode without verification to see payload
    try:
        payload = jwt.decode(TEST_TOKEN, options={"verify_signature": False})
        print("\nToken payload (no verification):")
        for key, value in payload.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Failed to decode without verification: {e}")
        return None
    
    # Try with JWT_SECRET_KEY
    print("\n--- Trying with JWT_SECRET_KEY ---")
    if jwt_secret:
        try:
            decoded = jwt.decode(
                TEST_TOKEN, 
                jwt_secret, 
                algorithms=["HS256"],
                options={"verify_aud": False}  # Skip audience check for now
            )
            print("✅ SUCCESS with JWT_SECRET_KEY (no audience check)")
            print(f"  User ID: {decoded.get('sub')}")
        except jwt.InvalidAudienceError as e:
            print(f"❌ Invalid audience with JWT_SECRET_KEY: {e}")
        except Exception as e:
            print(f"❌ Failed with JWT_SECRET_KEY: {e}")
    
    # Try with SUPABASE_JWT_SECRET
    print("\n--- Trying with SUPABASE_JWT_SECRET ---")
    if supabase_secret:
        try:
            decoded = jwt.decode(
                TEST_TOKEN,
                supabase_secret,
                algorithms=["HS256"],
                options={"verify_aud": False}  # Skip audience check for now
            )
            print("✅ SUCCESS with SUPABASE_JWT_SECRET (no audience check)")
            print(f"  User ID: {decoded.get('sub')}")
        except jwt.InvalidAudienceError as e:
            print(f"❌ Invalid audience with SUPABASE_JWT_SECRET: {e}")
        except Exception as e:
            print(f"❌ Failed with SUPABASE_JWT_SECRET: {e}")
    
    return payload


def test_audience_validation(jwt_secret, supabase_secret, payload):
    """Test 3: Test audience validation"""
    print("\n" + "="*80)
    print("TEST 3: Audience Validation")
    print("="*80)
    
    if not payload:
        print("No payload to test")
        return
    
    token_audience = payload.get("aud")
    print(f"Token audience: {token_audience}")
    
    # Test different audience values
    test_audiences = [
        "authenticated",  # Supabase default
        "mcp-server",     # Local default
        None,             # No audience check
    ]
    
    for test_aud in test_audiences:
        print(f"\n--- Testing with audience='{test_aud}' ---")
        
        if supabase_secret:
            try:
                if test_aud is None:
                    decoded = jwt.decode(
                        TEST_TOKEN,
                        supabase_secret,
                        algorithms=["HS256"],
                        options={"verify_aud": False}
                    )
                else:
                    decoded = jwt.decode(
                        TEST_TOKEN,
                        supabase_secret,
                        algorithms=["HS256"],
                        audience=test_aud
                    )
                print(f"  ✅ SUCCESS with audience='{test_aud}'")
            except jwt.InvalidAudienceError as e:
                print(f"  ❌ Invalid audience: {e}")
            except Exception as e:
                print(f"  ❌ Failed: {e}")


async def test_jwt_auth_backend():
    """Test 4: Test JWTAuthBackend"""
    print("\n" + "="*80)
    print("TEST 4: JWTAuthBackend")
    print("="*80)
    
    try:
        from fastmcp.auth.mcp_integration.jwt_auth_backend import JWTAuthBackend, create_jwt_auth_backend
        from fastmcp.auth.domain.services.jwt_service import JWTService
        
        # Create JWT backend
        print("Creating JWTAuthBackend...")
        jwt_backend = create_jwt_auth_backend()
        
        # Test verify_token
        print("\nTesting verify_token...")
        access_token = await jwt_backend.verify_token(TEST_TOKEN)
        
        if access_token:
            print("✅ verify_token succeeded!")
            print(f"  client_id: {access_token.client_id}")
            print(f"  scopes: {access_token.scopes}")
        else:
            print("❌ verify_token returned None")
            
    except Exception as e:
        print(f"❌ Error testing JWTAuthBackend: {e}")
        import traceback
        traceback.print_exc()


async def test_jwt_bearer_provider():
    """Test 5: Test JWTBearerAuthProvider"""
    print("\n" + "="*80)
    print("TEST 5: JWTBearerAuthProvider")
    print("="*80)
    
    try:
        from fastmcp.server.auth.providers.jwt_bearer import JWTBearerAuthProvider
        
        # Create provider
        print("Creating JWTBearerAuthProvider...")
        provider = JWTBearerAuthProvider()
        
        # Test verify_token
        print("\nTesting verify_token...")
        access_token = await provider.verify_token(TEST_TOKEN)
        
        if access_token:
            print("✅ verify_token succeeded!")
            print(f"  client_id: {access_token.client_id}")
            print(f"  scopes: {access_token.scopes}")
        else:
            print("❌ verify_token returned None")
            
        # Test load_access_token
        print("\nTesting load_access_token...")
        access_token = await provider.load_access_token(TEST_TOKEN)
        
        if access_token:
            print("✅ load_access_token succeeded!")
            print(f"  client_id: {access_token.client_id}")
            print(f"  scopes: {access_token.scopes}")
        else:
            print("❌ load_access_token returned None")
            
    except Exception as e:
        print(f"❌ Error testing JWTBearerAuthProvider: {e}")
        import traceback
        traceback.print_exc()


async def test_jwt_auth_middleware():
    """Test 6: Test JWTAuthMiddleware"""
    print("\n" + "="*80)
    print("TEST 6: JWTAuthMiddleware")
    print("="*80)
    
    try:
        from fastmcp.auth.middleware.jwt_auth_middleware import JWTAuthMiddleware
        
        # Get the secret key from environment
        jwt_secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SUPABASE_JWT_SECRET")
        
        if not jwt_secret:
            print("❌ No JWT secret found in environment")
            return
        
        # Create middleware
        print("Creating JWTAuthMiddleware...")
        middleware = JWTAuthMiddleware(jwt_secret)
        
        # Test extract_user_from_token
        print("\nTesting extract_user_from_token...")
        user_id = middleware.extract_user_from_token(TEST_TOKEN)
        
        if user_id:
            print("✅ extract_user_from_token succeeded!")
            print(f"  user_id: {user_id}")
        else:
            print("❌ extract_user_from_token returned None")
            
    except Exception as e:
        print(f"❌ Error testing JWTAuthMiddleware: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("JWT AUTHENTICATION DEBUG TESTS")
    print("="*80)
    
    # Test 1: Environment
    jwt_secret, supabase_secret = test_environment()
    
    # Test 2: Token decoding
    payload = test_decode_token(jwt_secret, supabase_secret)
    
    # Test 3: Audience validation
    test_audience_validation(jwt_secret, supabase_secret, payload)
    
    # Test 4: JWTAuthBackend
    await test_jwt_auth_backend()
    
    # Test 5: JWTBearerAuthProvider
    await test_jwt_bearer_provider()
    
    # Test 6: JWTAuthMiddleware
    await test_jwt_auth_middleware()
    
    print("\n" + "="*80)
    print("TESTS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())