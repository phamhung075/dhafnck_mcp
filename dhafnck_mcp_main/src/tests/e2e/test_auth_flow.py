"""
End-to-end tests for authentication flow

This module tests the complete authentication flow from a user perspective,
simulating real user interactions across the entire system.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from unittest.mock import patch
import requests
from datetime import datetime

from fastmcp.auth.application.services.auth_service import AuthService
from fastmcp.auth.domain.entities.user import UserStatus


@pytest.fixture(scope="session")
def driver():
    """Create Selenium WebDriver for testing"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode for CI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


@pytest.fixture
def frontend_url():
    """Frontend application URL"""
    return "http://localhost:3800"


@pytest.fixture
def api_url():
    """Backend API URL"""
    return "http://localhost:8000/api/auth"


class TestAuthenticationFlow:
    """End-to-end authentication flow tests"""
    
    def test_complete_user_registration_flow(self, driver, frontend_url, api_url):
        """Test complete user registration from frontend to backend"""
        # Navigate to signup page
        driver.get(f"{frontend_url}/signup")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Fill registration form
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("e2etest@example.com")
        
        username_input = driver.find_element(By.NAME, "username")
        username_input.send_keys("e2etestuser")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("SecurePassword123!")
        
        # Submit form
        submit_button = driver.find_element(By.TYPE, "submit")
        submit_button.click()
        
        # Wait for success message or redirect
        wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.CLASS_NAME, "success-message")),
                EC.url_contains("/login")
            )
        )
        
        # Verify user was created in backend
        response = requests.get(f"{api_url}/users/by-email/e2etest@example.com")
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == "e2etest@example.com"
        assert user_data["status"] == "pending_verification"
    
    def test_complete_login_flow(self, driver, frontend_url, auth_service):
        """Test complete login flow with verified user"""
        # Create and verify test user
        user = auth_service.register_user(
            email="logintest@example.com",
            username="logintest",
            password="SecurePassword123!"
        )
        user.status = UserStatus.ACTIVE
        auth_service._user_repository.save(user)
        
        # Navigate to login page
        driver.get(f"{frontend_url}/login")
        
        wait = WebDriverWait(driver, 10)
        
        # Fill login form
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("logintest@example.com")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("SecurePassword123!")
        
        # Submit form
        submit_button = driver.find_element(By.TYPE, "submit")
        submit_button.click()
        
        # Wait for redirect to dashboard
        wait.until(EC.url_contains("/dashboard"))
        
        # Verify we're on dashboard
        assert "/dashboard" in driver.current_url
        
        # Verify user info is displayed
        user_info = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "user-info")))
        assert "logintest@example.com" in user_info.text
    
    def test_protected_route_access(self, driver, frontend_url, auth_service):
        """Test access to protected routes requires authentication"""
        # Try to access protected route without login
        driver.get(f"{frontend_url}/dashboard")
        
        wait = WebDriverWait(driver, 10)
        
        # Should be redirected to login page
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url
        
        # Login with valid credentials
        user = auth_service.register_user(
            email="protected@example.com",
            username="protectedtest",
            password="SecurePassword123!"
        )
        user.status = UserStatus.ACTIVE
        auth_service._user_repository.save(user)
        
        # Fill login form
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("protected@example.com")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("SecurePassword123!")
        
        submit_button = driver.find_element(By.TYPE, "submit")
        submit_button.click()
        
        # Should now access dashboard
        wait.until(EC.url_contains("/dashboard"))
        assert "/dashboard" in driver.current_url
    
    def test_token_refresh_flow(self, driver, frontend_url, auth_service):
        """Test automatic token refresh works in frontend"""
        # Create test user
        user = auth_service.register_user(
            email="refresh@example.com",
            username="refreshtest",
            password="SecurePassword123!"
        )
        user.status = UserStatus.ACTIVE
        auth_service._user_repository.save(user)
        
        # Login
        driver.get(f"{frontend_url}/login")
        wait = WebDriverWait(driver, 10)
        
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("refresh@example.com")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("SecurePassword123!")
        
        submit_button = driver.find_element(By.TYPE, "submit")
        submit_button.click()
        
        # Wait for dashboard
        wait.until(EC.url_contains("/dashboard"))
        
        # Make API call that would trigger token refresh
        # This simulates the token expiring and being refreshed
        driver.execute_script("""
            // Simulate API call that triggers token refresh
            fetch('/api/auth/me', {
                headers: {
                    'Authorization': 'Bearer expired_token'
                }
            }).then(response => {
                if (response.status === 401) {
                    // This should trigger automatic token refresh
                    console.log('Token refresh triggered');
                }
            });
        """)
        
        # Verify user is still logged in after refresh
        time.sleep(2)  # Wait for refresh to complete
        user_info = driver.find_element(By.CLASS_NAME, "user-info")
        assert "refresh@example.com" in user_info.text
    
    def test_logout_flow(self, driver, frontend_url, auth_service):
        """Test complete logout flow"""
        # Create and login user
        user = auth_service.register_user(
            email="logout@example.com",
            username="logouttest",
            password="SecurePassword123!"
        )
        user.status = UserStatus.ACTIVE
        auth_service._user_repository.save(user)
        
        # Login
        driver.get(f"{frontend_url}/login")
        wait = WebDriverWait(driver, 10)
        
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("logout@example.com")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("SecurePassword123!")
        
        submit_button = driver.find_element(By.TYPE, "submit")
        submit_button.click()
        
        # Wait for dashboard
        wait.until(EC.url_contains("/dashboard"))
        
        # Click logout button
        logout_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "logout-button")))
        logout_button.click()
        
        # Should be redirected to login page
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url
        
        # Try to access protected route - should redirect to login
        driver.get(f"{frontend_url}/dashboard")
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url
    
    def test_password_reset_flow(self, driver, frontend_url, api_url, auth_service):
        """Test complete password reset flow"""
        # Create test user
        user = auth_service.register_user(
            email="resettest@example.com",
            username="resettest",
            password="OldPassword123!"
        )
        user.status = UserStatus.ACTIVE
        auth_service._user_repository.save(user)
        
        # Navigate to login page
        driver.get(f"{frontend_url}/login")
        wait = WebDriverWait(driver, 10)
        
        # Click "Forgot Password" link
        forgot_password_link = wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Forgot Password?"))
        )
        forgot_password_link.click()
        
        # Fill email for password reset
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("resettest@example.com")
        
        # Submit reset request
        submit_button = driver.find_element(By.TYPE, "submit")
        
        with patch('fastmcp.auth.application.services.email_service.send_reset_email') as mock_send:
            submit_button.click()
            
            # Wait for success message
            success_message = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
            )
            assert "reset email sent" in success_message.text.lower()
            
            # Verify email was sent
            mock_send.assert_called_once()
            reset_token = mock_send.call_args[0][1]  # Get the token from the call
        
        # Simulate clicking reset link (navigate to reset page with token)
        driver.get(f"{frontend_url}/reset-password?token={reset_token}")
        
        # Fill new password
        new_password_input = wait.until(EC.presence_of_element_located((By.NAME, "new_password")))
        new_password_input.send_keys("NewSecurePassword123!")
        
        confirm_password_input = driver.find_element(By.NAME, "confirm_password")
        confirm_password_input.send_keys("NewSecurePassword123!")
        
        # Submit new password
        submit_button = driver.find_element(By.TYPE, "submit")
        submit_button.click()
        
        # Wait for success message
        success_message = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )
        assert "password reset successful" in success_message.text.lower()
        
        # Test login with new password
        driver.get(f"{frontend_url}/login")
        
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("resettest@example.com")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("NewSecurePassword123!")
        
        submit_button = driver.find_element(By.TYPE, "submit")
        submit_button.click()
        
        # Should successfully login
        wait.until(EC.url_contains("/dashboard"))
        assert "/dashboard" in driver.current_url
    
    def test_email_verification_flow(self, driver, frontend_url, auth_service):
        """Test email verification flow"""
        # Register new unverified user
        driver.get(f"{frontend_url}/signup")
        wait = WebDriverWait(driver, 10)
        
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("verify@example.com")
        
        username_input = driver.find_element(By.NAME, "username")
        username_input.send_keys("verifytest")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("SecurePassword123!")
        
        submit_button = driver.find_element(By.TYPE, "submit")
        
        with patch('fastmcp.auth.application.services.email_service.send_verification_email') as mock_send:
            submit_button.click()
            
            # Wait for success message
            wait.until(EC.url_contains("/login"))
            
            # Get verification token from mock
            mock_send.assert_called_once()
            verification_token = mock_send.call_args[0][1]
        
        # Try to login with unverified account
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("verify@example.com")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("SecurePassword123!")
        
        submit_button = driver.find_element(By.TYPE, "submit")
        submit_button.click()
        
        # Should show verification required message
        error_message = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
        )
        assert "not verified" in error_message.text.lower()
        
        # Simulate clicking verification link
        driver.get(f"{frontend_url}/verify-email?token={verification_token}")
        
        # Should show verification success
        success_message = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )
        assert "email verified" in success_message.text.lower()
        
        # Now login should work
        driver.get(f"{frontend_url}/login")
        
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("verify@example.com")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("SecurePassword123!")
        
        submit_button = driver.find_element(By.TYPE, "submit")
        submit_button.click()
        
        # Should successfully login
        wait.until(EC.url_contains("/dashboard"))
        assert "/dashboard" in driver.current_url


class TestConcurrentUsers:
    """Test concurrent user authentication scenarios"""
    
    @pytest.mark.asyncio
    async def test_multiple_users_login_simultaneously(self, api_url, auth_service):
        """Test multiple users can login simultaneously"""
        import asyncio
        import aiohttp
        
        # Create test users
        users = []
        for i in range(5):
            user = auth_service.register_user(
                email=f"concurrent{i}@example.com",
                username=f"concurrent{i}",
                password="SecurePassword123!"
            )
            user.status = UserStatus.ACTIVE
            auth_service._user_repository.save(user)
            users.append(user)
        
        async def login_user(session, email, password):
            """Login a single user"""
            async with session.post(
                f"{api_url}/login",
                json={"email": email, "password": password}
            ) as response:
                return await response.json(), response.status
        
        # Login all users simultaneously
        async with aiohttp.ClientSession() as session:
            tasks = [
                login_user(session, f"concurrent{i}@example.com", "SecurePassword123!")
                for i in range(5)
            ]
            results = await asyncio.gather(*tasks)
        
        # Verify all logins succeeded
        for result, status in results:
            assert status == 200
            assert "access_token" in result
            assert "refresh_token" in result
    
    def test_token_refresh_under_load(self, api_url, auth_service):
        """Test token refresh works under concurrent load"""
        import threading
        import time
        
        # Create test user
        user = auth_service.register_user(
            email="loadtest@example.com",
            username="loadtest",
            password="SecurePassword123!"
        )
        user.status = UserStatus.ACTIVE
        auth_service._user_repository.save(user)
        
        # Login to get tokens
        response = requests.post(
            f"{api_url}/login",
            json={"email": "loadtest@example.com", "password": "SecurePassword123!"}
        )
        tokens = response.json()
        refresh_token = tokens["refresh_token"]
        
        results = []
        
        def refresh_token_worker():
            """Worker function to refresh token"""
            try:
                response = requests.post(
                    f"{api_url}/refresh",
                    json={"refresh_token": refresh_token}
                )
                results.append(response.status_code)
            except Exception as e:
                results.append(str(e))
        
        # Create multiple threads to refresh token simultaneously
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=refresh_token_worker)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # At least one refresh should succeed
        # (Others might fail due to token rotation, which is expected)
        success_count = sum(1 for result in results if result == 200)
        assert success_count >= 1
        
        # No unexpected errors should occur
        error_count = sum(1 for result in results if isinstance(result, str))
        assert error_count == 0


class TestSecurityScenarios:
    """Test security-related authentication scenarios"""
    
    def test_account_lockout_after_failed_attempts(self, api_url, auth_service):
        """Test account gets locked after multiple failed login attempts"""
        # Create test user
        user = auth_service.register_user(
            email="lockout@example.com",
            username="lockouttest",
            password="SecurePassword123!"
        )
        user.status = UserStatus.ACTIVE
        auth_service._user_repository.save(user)
        
        # Attempt login with wrong password multiple times
        for attempt in range(6):  # Should lock after 5 attempts
            response = requests.post(
                f"{api_url}/login",
                json={"email": "lockout@example.com", "password": "WrongPassword"}
            )
            
            if attempt < 5:
                assert response.status_code == 401
                assert "Invalid credentials" in response.json()["detail"]
            else:
                # 6th attempt should show account locked
                assert response.status_code == 403
                assert "locked" in response.json()["detail"].lower()
        
        # Even with correct password, login should fail
        response = requests.post(
            f"{api_url}/login",
            json={"email": "lockout@example.com", "password": "SecurePassword123!"}
        )
        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()
    
    def test_sql_injection_protection(self, api_url):
        """Test API is protected against SQL injection attempts"""
        # Try SQL injection in email field
        response = requests.post(
            f"{api_url}/login",
            json={
                "email": "admin@example.com'; DROP TABLE users; --",
                "password": "password"
            }
        )
        
        # Should return invalid credentials, not a database error
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_xss_protection_in_responses(self, api_url, auth_service):
        """Test API responses are protected against XSS"""
        # Try to register with XSS payload in username
        response = requests.post(
            f"{api_url}/register",
            json={
                "email": "xsstest@example.com",
                "username": "<script>alert('xss')</script>",
                "password": "SecurePassword123!"
            }
        )
        
        # Registration might succeed but response should be escaped
        if response.status_code == 201:
            data = response.json()
            # Username should be escaped or sanitized
            assert "<script>" not in data.get("username", "")
        else:
            # Or it might be rejected due to validation
            assert response.status_code in [400, 422]