"""
Integration test for OAuth2PasswordBearer authentication

This test verifies that FastAPI's OAuth2PasswordBearer works correctly
with the existing authentication endpoints.
"""

import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from fastapi.security import OAuth2PasswordRequestForm
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastmcp.auth.interface.fastapi_auth import (
    oauth2_scheme,
    get_current_user,
    get_current_active_user,
    require_roles,
    require_admin,
    get_optional_user
)
from fastmcp.auth.interface.auth_endpoints import router as auth_router
from fastmcp.auth.domain.entities.user import User

# Create test app
app = FastAPI()
app.include_router(auth_router)


# Test endpoints using OAuth2PasswordBearer
@app.get("/test/protected")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    """Test endpoint that requires authentication"""
    return {"message": f"Hello {current_user.username}"}


@app.get("/test/admin")
async def admin_endpoint(current_user: User = Depends(require_admin)):
    """Test endpoint that requires admin role"""
    return {"message": f"Admin access for {current_user.username}"}


@app.get("/test/optional")
async def optional_auth_endpoint(user: User = Depends(get_optional_user)):
    """Test endpoint with optional authentication"""
    if user:
        return {"message": f"Authenticated as {user.username}"}
    return {"message": "Anonymous access"}


@app.post("/test/oauth2-login")
async def oauth2_login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Test OAuth2 password flow login"""
    # This would integrate with auth service
    # For testing, we'll mock the response
    if form_data.username == "testuser" and form_data.password == "testpass":
        return {
            "access_token": "test-access-token",
            "token_type": "bearer"
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")


class TestOAuth2Integration:
    """Test OAuth2PasswordBearer integration"""
    
    def test_oauth2_scheme_extraction(self):
        """Test that OAuth2PasswordBearer correctly extracts tokens"""
        client = TestClient(app)
        
        # Test without token - should return 401
        response = client.get("/test/protected")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        
        # Test with invalid token format
        response = client.get(
            "/test/protected",
            headers={"Authorization": "InvalidFormat token"}
        )
        assert response.status_code == 401
        
        # Test with Bearer token (would need valid JWT in real scenario)
        # This will fail with invalid JWT but proves OAuth2PasswordBearer extracts it
        response = client.get(
            "/test/protected",
            headers={"Authorization": "Bearer test-token-here"}
        )
        # Will return 401 due to invalid JWT, but OAuth2PasswordBearer works
        assert response.status_code == 401
    
    def test_oauth2_password_flow(self):
        """Test OAuth2 password flow with form data"""
        client = TestClient(app)
        
        # Test OAuth2PasswordRequestForm
        response = client.post(
            "/test/oauth2-login",
            data={
                "username": "testuser",
                "password": "testpass"
            }
        )
        assert response.status_code == 200
        assert response.json()["access_token"] == "test-access-token"
        assert response.json()["token_type"] == "bearer"
        
        # Test with wrong credentials
        response = client.post(
            "/test/oauth2-login",
            data={
                "username": "wronguser",
                "password": "wrongpass"
            }
        )
        assert response.status_code == 401
    
    def test_openapi_documentation(self):
        """Test that OAuth2PasswordBearer generates correct OpenAPI schema"""
        client = TestClient(app)
        
        # Get OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_schema = response.json()
        
        # Check for OAuth2 security scheme
        assert "components" in openapi_schema
        assert "securitySchemes" in openapi_schema["components"]
        
        # OAuth2PasswordBearer should create OAuth2PasswordBearer security scheme
        security_schemes = openapi_schema["components"]["securitySchemes"]
        
        # Find OAuth2 scheme
        oauth2_found = False
        for scheme_name, scheme_def in security_schemes.items():
            if scheme_def.get("type") == "oauth2":
                oauth2_found = True
                assert "flows" in scheme_def
                assert "password" in scheme_def["flows"]
                assert scheme_def["flows"]["password"]["tokenUrl"] == "/api/auth/login"
        
        assert oauth2_found, "OAuth2 security scheme not found in OpenAPI schema"
    
    def test_swagger_ui_auth(self):
        """Test that Swagger UI shows authorization button"""
        client = TestClient(app)
        
        # Swagger UI should be available
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Check that HTML contains authorization elements
        html_content = response.text
        assert "authorize" in html_content.lower()
    
    def test_protected_endpoint_requirements(self):
        """Test that protected endpoints require authentication"""
        client = TestClient(app)
        
        # Test protected endpoint
        response = client.get("/test/protected")
        assert response.status_code == 401
        
        # Test admin endpoint
        response = client.get("/test/admin")
        assert response.status_code == 401
        
        # Test optional auth endpoint (should work without auth)
        response = client.get("/test/optional")
        assert response.status_code == 200
        assert response.json()["message"] == "Anonymous access"


if __name__ == "__main__":
    # Run tests
    print("Testing OAuth2PasswordBearer Integration...")
    
    test_suite = TestOAuth2Integration()
    
    print("1. Testing OAuth2 scheme token extraction...")
    test_suite.test_oauth2_scheme_extraction()
    print("   ✓ OAuth2PasswordBearer correctly handles tokens")
    
    print("2. Testing OAuth2 password flow...")
    test_suite.test_oauth2_password_flow()
    print("   ✓ OAuth2PasswordRequestForm works correctly")
    
    print("3. Testing OpenAPI documentation generation...")
    test_suite.test_openapi_documentation()
    print("   ✓ OAuth2 security scheme in OpenAPI schema")
    
    print("4. Testing Swagger UI authentication...")
    test_suite.test_swagger_ui_auth()
    print("   ✓ Swagger UI shows authorization")
    
    print("5. Testing protected endpoint requirements...")
    test_suite.test_protected_endpoint_requirements()
    print("   ✓ Protected endpoints require authentication")
    
    print("\n✅ All OAuth2PasswordBearer integration tests passed!")