#!/usr/bin/env python3
"""
Debug JWT validation by testing the JWTService directly.
"""

import os
import json
import jwt

# Set up environment for the JWT service
os.environ.setdefault("JWT_SECRET_KEY", "default-secret-key-change-in-production")

# The JWT token from the user (should be passed via environment variable)
JWT_TOKEN = os.getenv("DEBUG_JWT_TOKEN", "")

def debug_jwt_service():
    """Test the JWTService directly."""
    try:
        import sys
        sys.path.insert(0, '/home/daihungpham/agentic-project/dhafnck_mcp_main/src')
        from fastmcp.auth.domain.services.jwt_service import JWTService
        
        # Create JWT service with the default secret
        jwt_secret = os.getenv("JWT_SECRET_KEY", "default-secret-key-change-in-production")
        jwt_service = JWTService(secret_key=jwt_secret)
        
        print(f"🔑 JWT Secret Key: {jwt_secret}")
        print(f"🔧 JWT Algorithm: {jwt_service.ALGORITHM}")
        
        # Test token verification with 'access' type
        print("\n1. Testing 'access' token type...")
        try:
            payload = jwt_service.verify_token(JWT_TOKEN, expected_type="access")
            if payload:
                print("✅ Token validated as 'access' type")
                print(f"Payload: {json.dumps(payload, indent=2)}")
            else:
                print("❌ Token rejected for 'access' type")
        except Exception as e:
            print(f"❌ Error validating as 'access': {e}")
        
        # Test token verification with 'api_token' type
        print("\n2. Testing 'api_token' token type...")
        try:
            payload = jwt_service.verify_token(JWT_TOKEN, expected_type="api_token")
            if payload:
                print("✅ Token validated as 'api_token' type")
                print(f"Payload: {json.dumps(payload, indent=2)}")
            else:
                print("❌ Token rejected for 'api_token' type")
        except Exception as e:
            print(f"❌ Error validating as 'api_token': {e}")
        
        # Test raw JWT decoding with the service's secret
        print("\n3. Testing raw JWT decoding with service secret...")
        try:
            payload = jwt.decode(JWT_TOKEN, jwt_secret, algorithms=[jwt_service.ALGORITHM])
            print("✅ Token decoded successfully with service secret")
            print(f"Raw payload: {json.dumps(payload, indent=2)}")
        except Exception as e:
            print(f"❌ Error decoding with service secret: {e}")
        
        # Test with different secrets to see what secret was used to sign the token
        print("\n4. Testing with common secret patterns...")
        test_secrets = [
            "default-secret-key-change-in-production",
            "this is a dummy jwt secret for development",
            "dGhpcyBpcyBhIGR1bW15IGp3dCBzZWNyZXQgZm9yIGRldmVsb3BtZW50",
            "your-secret-key",
            "secret",
            "jwt-secret",
            "dhafnck-secret",
            "dev-secret-key-123"
        ]
        
        for secret in test_secrets:
            try:
                payload = jwt.decode(JWT_TOKEN, secret, algorithms=["HS256"])
                print(f"✅ Token decoded with secret: '{secret}'")
                print(f"Payload: {json.dumps(payload, indent=2)}")
                return secret  # Return the correct secret
            except jwt.InvalidSignatureError:
                print(f"❌ Secret '{secret}' did not work")
            except Exception as e:
                print(f"❌ Error with secret '{secret}': {e}")
        
        return None
    
    except Exception as e:
        print(f"❌ Failed to create JWTService: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_jwt_auth_backend():
    """Test the JWTAuthBackend directly."""
    try:
        # Import and test the backend
        import asyncio
        import sys
        sys.path.insert(0, '/home/daihungpham/agentic-project/dhafnck_mcp_main/src')
        from fastmcp.auth.mcp_integration.jwt_auth_backend import create_jwt_auth_backend
        
        print("\n5. Testing JWTAuthBackend...")
        
        # Create the backend
        backend = create_jwt_auth_backend()
        print(f"✅ JWTAuthBackend created")
        
        # Test token validation
        async def test_token():
            access_token = await backend.load_access_token(JWT_TOKEN)
            if access_token:
                print("✅ JWTAuthBackend validated token successfully")
                print(f"Client ID: {access_token.client_id}")
                print(f"Scopes: {access_token.scopes}")
                print(f"Expires at: {access_token.expires_at}")
                return True
            else:
                print("❌ JWTAuthBackend rejected token")
                return False
        
        return asyncio.run(test_token())
    
    except Exception as e:
        print(f"❌ Failed to test JWTAuthBackend: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run JWT debugging tests."""
    print("🔍 JWT Authentication Debugging")
    print("=" * 60)
    
    # First, decode the token without verification
    print("Token payload (no verification):")
    try:
        payload = jwt.decode(JWT_TOKEN, options={"verify_signature": False})
        print(json.dumps(payload, indent=2))
    except Exception as e:
        print(f"❌ Failed to decode token: {e}")
    
    # Test JWT service
    correct_secret = debug_jwt_service()
    
    # Test JWT auth backend
    test_jwt_auth_backend()
    
    if correct_secret:
        print(f"\n🎯 SOLUTION: The correct JWT secret is: '{correct_secret}'")
        print("Make sure this secret is set in the JWT_SECRET_KEY environment variable")
    else:
        print("\n❌ Could not find the correct JWT secret")

if __name__ == "__main__":
    main()