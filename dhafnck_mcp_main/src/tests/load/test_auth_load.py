"""
Load testing for authentication system

This module tests the authentication system under load to ensure it can handle
concurrent users, high request volumes, and stress conditions.
"""

import asyncio
import aiohttp
import time
import statistics
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import threading
import json
import uuid
from typing import List, Dict, Any

from fastmcp.auth.application.services.auth_service import AuthService
from fastmcp.auth.domain.entities.user import UserStatus


class AuthLoadTester:
    """Load testing utility for authentication system"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/auth"):
        self.base_url = base_url
        self.results = []
        self.errors = []
    
    async def create_test_user(self, session: aiohttp.ClientSession, user_id: str) -> Dict[str, Any]:
        """Create a test user for load testing"""
        user_data = {
            "email": f"loadtest{user_id}@example.com",
            "username": f"loadtest{user_id}",
            "password": "LoadTest123!"
        }
        
        async with session.post(f"{self.base_url}/register", json=user_data) as response:
            if response.status == 201:
                return await response.json()
            else:
                raise Exception(f"Failed to create user: {response.status}")
    
    async def login_user(self, session: aiohttp.ClientSession, email: str, password: str) -> Dict[str, Any]:
        """Login a user and return tokens"""
        login_data = {"email": email, "password": password}
        
        start_time = time.time()
        try:
            async with session.post(f"{self.base_url}/login", json=login_data) as response:
                end_time = time.time()
                response_data = await response.json()
                
                result = {
                    "status": response.status,
                    "response_time": end_time - start_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "operation": "login",
                    "email": email
                }
                
                if response.status == 200:
                    result["tokens"] = response_data
                else:
                    result["error"] = response_data.get("detail", "Unknown error")
                
                self.results.append(result)
                return result
        except Exception as e:
            end_time = time.time()
            error_result = {
                "status": 0,
                "response_time": end_time - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "operation": "login",
                "email": email,
                "error": str(e)
            }
            self.errors.append(error_result)
            return error_result
    
    async def refresh_token(self, session: aiohttp.ClientSession, refresh_token: str) -> Dict[str, Any]:
        """Refresh an access token"""
        refresh_data = {"refresh_token": refresh_token}
        
        start_time = time.time()
        try:
            async with session.post(f"{self.base_url}/refresh", json=refresh_data) as response:
                end_time = time.time()
                response_data = await response.json()
                
                result = {
                    "status": response.status,
                    "response_time": end_time - start_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "operation": "refresh"
                }
                
                if response.status == 200:
                    result["tokens"] = response_data
                else:
                    result["error"] = response_data.get("detail", "Unknown error")
                
                self.results.append(result)
                return result
        except Exception as e:
            end_time = time.time()
            error_result = {
                "status": 0,
                "response_time": end_time - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "operation": "refresh",
                "error": str(e)
            }
            self.errors.append(error_result)
            return error_result
    
    async def authenticated_request(self, session: aiohttp.ClientSession, access_token: str) -> Dict[str, Any]:
        """Make an authenticated request to test token validation"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}/me", headers=headers) as response:
                end_time = time.time()
                response_data = await response.json()
                
                result = {
                    "status": response.status,
                    "response_time": end_time - start_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "operation": "authenticated_request"
                }
                
                if response.status == 200:
                    result["user_data"] = response_data
                else:
                    result["error"] = response_data.get("detail", "Unknown error")
                
                self.results.append(result)
                return result
        except Exception as e:
            end_time = time.time()
            error_result = {
                "status": 0,
                "response_time": end_time - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "operation": "authenticated_request",
                "error": str(e)
            }
            self.errors.append(error_result)
            return error_result
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze load test results"""
        if not self.results:
            return {"error": "No results to analyze"}
        
        # Separate by operation type
        operations = {}
        for result in self.results:
            op = result["operation"]
            if op not in operations:
                operations[op] = []
            operations[op].append(result)
        
        analysis = {
            "total_requests": len(self.results),
            "total_errors": len(self.errors),
            "error_rate": len(self.errors) / (len(self.results) + len(self.errors)) * 100,
            "operations": {}
        }
        
        for op, results in operations.items():
            response_times = [r["response_time"] for r in results]
            success_count = len([r for r in results if r["status"] == 200])
            
            analysis["operations"][op] = {
                "total_requests": len(results),
                "successful_requests": success_count,
                "success_rate": success_count / len(results) * 100,
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else response_times[0]
            }
        
        return analysis


class TestConcurrentAuthentication:
    """Test concurrent authentication scenarios"""
    
    @pytest.fixture
    def load_tester(self):
        """Create load tester instance"""
        return AuthLoadTester()
    
    @pytest.fixture
    async def test_users(self, auth_service):
        """Create multiple test users for load testing"""
        users = []
        for i in range(50):
            user = auth_service.register_user(
                email=f"concurrent{i}@example.com",
                username=f"concurrent{i}",
                password="ConcurrentTest123!"
            )
            user.status = UserStatus.ACTIVE
            auth_service._user_repository.save(user)
            users.append(user)
        return users
    
    @pytest.mark.asyncio
    async def test_concurrent_logins(self, load_tester, test_users):
        """Test multiple users logging in simultaneously"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create login tasks for all users
            tasks = []
            for user in test_users[:20]:  # Test with 20 concurrent users
                task = load_tester.login_user(
                    session, 
                    user.email, 
                    "ConcurrentTest123!"
                )
                tasks.append(task)
            
            # Execute all logins simultaneously
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Analyze results
            analysis = load_tester.analyze_results()
            
            # Assertions
            assert analysis["error_rate"] < 5.0, f"Error rate too high: {analysis['error_rate']}%"
            assert analysis["operations"]["login"]["success_rate"] > 95.0, "Login success rate too low"
            assert analysis["operations"]["login"]["avg_response_time"] < 2.0, "Average response time too high"
            
            print(f"Concurrent login test completed in {end_time - start_time:.2f}s")
            print(f"Success rate: {analysis['operations']['login']['success_rate']:.1f}%")
            print(f"Average response time: {analysis['operations']['login']['avg_response_time']:.3f}s")
    
    @pytest.mark.asyncio
    async def test_token_refresh_under_load(self, load_tester, test_users):
        """Test token refresh under high load"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # First, login users to get refresh tokens
            refresh_tokens = []
            for user in test_users[:15]:
                result = await load_tester.login_user(
                    session,
                    user.email,
                    "ConcurrentTest123!"
                )
                if result["status"] == 200:
                    refresh_tokens.append(result["tokens"]["refresh_token"])
            
            # Now test concurrent token refresh
            tasks = []
            for token in refresh_tokens:
                task = load_tester.refresh_token(session, token)
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Analyze results
            analysis = load_tester.analyze_results()
            
            # Note: Some failures expected due to token rotation
            assert analysis["operations"]["refresh"]["success_rate"] > 60.0, "Refresh success rate too low"
            assert analysis["operations"]["refresh"]["avg_response_time"] < 1.0, "Refresh response time too high"
            
            print(f"Token refresh test completed in {end_time - start_time:.2f}s")
            print(f"Refresh success rate: {analysis['operations']['refresh']['success_rate']:.1f}%")
    
    @pytest.mark.asyncio
    async def test_authenticated_requests_load(self, load_tester, test_users):
        """Test authenticated requests under load"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Login users and collect access tokens
            access_tokens = []
            for user in test_users[:25]:
                result = await load_tester.login_user(
                    session,
                    user.email,
                    "ConcurrentTest123!"
                )
                if result["status"] == 200:
                    access_tokens.append(result["tokens"]["access_token"])
            
            # Make multiple authenticated requests per token
            tasks = []
            for token in access_tokens:
                for _ in range(3):  # 3 requests per user
                    task = load_tester.authenticated_request(session, token)
                    tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Analyze results
            analysis = load_tester.analyze_results()
            
            assert analysis["operations"]["authenticated_request"]["success_rate"] > 98.0, "Auth request success rate too low"
            assert analysis["operations"]["authenticated_request"]["avg_response_time"] < 0.5, "Auth request response time too high"
            
            print(f"Authenticated requests test completed in {end_time - start_time:.2f}s")
            print(f"Total requests: {len(tasks)}")
            print(f"Success rate: {analysis['operations']['authenticated_request']['success_rate']:.1f}%")


class TestAuthenticationStress:
    """Stress testing for authentication system"""
    
    def test_rapid_login_attempts(self, auth_service):
        """Test rapid successive login attempts"""
        # Create test user
        user = auth_service.register_user(
            email="stresstest@example.com",
            username="stresstest",
            password="StressTest123!"
        )
        user.status = UserStatus.ACTIVE
        auth_service._user_repository.save(user)
        
        def login_attempt():
            """Single login attempt"""
            try:
                tokens = auth_service.authenticate_user(
                    email="stresstest@example.com",
                    password="StressTest123!"
                )
                return {"success": True, "tokens": tokens}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Execute rapid login attempts
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(login_attempt) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        successful_logins = [r for r in results if r["success"]]
        failed_logins = [r for r in results if not r["success"]]
        
        # Should handle most requests successfully
        success_rate = len(successful_logins) / len(results) * 100
        assert success_rate > 90.0, f"Success rate too low under stress: {success_rate}%"
        
        print(f"Rapid login test: {len(successful_logins)}/{len(results)} succeeded ({success_rate:.1f}%)")
    
    def test_memory_usage_under_load(self, auth_service):
        """Test memory usage doesn't grow excessively under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many users
        users = []
        for i in range(100):
            user = auth_service.register_user(
                email=f"memtest{i}@example.com",
                username=f"memtest{i}",
                password="MemTest123!"
            )
            user.status = UserStatus.ACTIVE
            auth_service._user_repository.save(user)
            users.append(user)
        
        # Perform many authentication operations
        for _ in range(200):
            user = users[_ % len(users)]
            try:
                tokens = auth_service.authenticate_user(
                    email=user.email,
                    password="MemTest123!"
                )
                # Refresh token
                auth_service.refresh_access_token(tokens["refresh_token"])
            except Exception:
                pass  # Some failures expected due to token rotation
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100, f"Memory usage increased too much: {memory_increase:.1f}MB"
        
        print(f"Memory test: Initial={initial_memory:.1f}MB, Final={final_memory:.1f}MB, Increase={memory_increase:.1f}MB")
    
    def test_database_connection_pool_stress(self, auth_service):
        """Test database connection handling under stress"""
        def db_intensive_operation():
            """Perform database-intensive auth operations"""
            try:
                # Multiple operations that hit the database
                user_id = str(uuid.uuid4())
                email = f"dbtest{user_id}@example.com"
                
                # Register user
                user = auth_service.register_user(
                    email=email,
                    username=f"dbtest{user_id}",
                    password="DBTest123!"
                )
                user.status = UserStatus.ACTIVE
                auth_service._user_repository.save(user)
                
                # Login user
                tokens = auth_service.authenticate_user(email, "DBTest123!")
                
                # Get user info
                auth_service.get_user_by_id(str(user.id.value))
                
                # Refresh token
                auth_service.refresh_access_token(tokens["refresh_token"])
                
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Execute many concurrent database operations
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(db_intensive_operation) for _ in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        successful_ops = [r for r in results if r["success"]]
        failed_ops = [r for r in results if not r["success"]]
        
        success_rate = len(successful_ops) / len(results) * 100
        
        # Should handle database load well
        assert success_rate > 95.0, f"Database stress test success rate too low: {success_rate}%"
        
        print(f"Database stress test: {len(successful_ops)}/{len(results)} succeeded ({success_rate:.1f}%)")
        if failed_ops:
            print(f"Sample error: {failed_ops[0]['error']}")


class TestPerformanceBenchmarks:
    """Performance benchmarking for authentication system"""
    
    def test_login_performance_benchmark(self, auth_service):
        """Benchmark login performance"""
        # Create test user
        user = auth_service.register_user(
            email="benchmark@example.com",
            username="benchmark",
            password="Benchmark123!"
        )
        user.status = UserStatus.ACTIVE
        auth_service._user_repository.save(user)
        
        # Benchmark login performance
        login_times = []
        for _ in range(100):
            start_time = time.time()
            tokens = auth_service.authenticate_user(
                email="benchmark@example.com",
                password="Benchmark123!"
            )
            end_time = time.time()
            login_times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = statistics.mean(login_times)
        min_time = min(login_times)
        max_time = max(login_times)
        p95_time = statistics.quantiles(login_times, n=20)[18]
        
        # Performance assertions
        assert avg_time < 0.1, f"Average login time too slow: {avg_time:.3f}s"
        assert p95_time < 0.2, f"95th percentile login time too slow: {p95_time:.3f}s"
        
        print(f"Login performance benchmark:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        print(f"  95th percentile: {p95_time:.3f}s")
    
    def test_token_generation_performance(self, auth_service):
        """Benchmark token generation performance"""
        generation_times = []
        
        for _ in range(1000):
            start_time = time.time()
            access_token = auth_service._jwt_service.create_access_token(
                user_id="test-user-id",
                email="test@example.com",
                roles=["user"]
            )
            refresh_token, family = auth_service._jwt_service.create_refresh_token(
                user_id="test-user-id"
            )
            end_time = time.time()
            generation_times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = statistics.mean(generation_times)
        p95_time = statistics.quantiles(generation_times, n=20)[18]
        
        # Performance assertions
        assert avg_time < 0.001, f"Token generation too slow: {avg_time:.4f}s"
        assert p95_time < 0.002, f"95th percentile token generation too slow: {p95_time:.4f}s"
        
        print(f"Token generation performance:")
        print(f"  Average: {avg_time:.4f}s")
        print(f"  95th percentile: {p95_time:.4f}s")


if __name__ == "__main__":
    # Run load tests directly
    import sys
    import asyncio
    
    async def run_basic_load_test():
        """Run a basic load test"""
        load_tester = AuthLoadTester()
        
        print("Running basic load test...")
        
        # Test concurrent logins
        connector = aiohttp.TCPConnector(limit=50)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for i in range(20):
                # Create and login user
                user_id = str(uuid.uuid4())
                email = f"loadtest{i}@example.com"
                password = "LoadTest123!"
                
                # Register user first (in real test, users would already exist)
                await load_tester.create_test_user(session, str(i))
                
                # Login user
                task = load_tester.login_user(session, email, password)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        # Analyze and print results
        analysis = load_tester.analyze_results()
        print(f"Load test completed:")
        print(f"  Total requests: {analysis['total_requests']}")
        print(f"  Error rate: {analysis['error_rate']:.1f}%")
        if "login" in analysis["operations"]:
            login_stats = analysis["operations"]["login"]
            print(f"  Login success rate: {login_stats['success_rate']:.1f}%")
            print(f"  Average response time: {login_stats['avg_response_time']:.3f}s")
    
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        asyncio.run(run_basic_load_test())
    else:
        print("Run with 'python test_auth_load.py run' to execute basic load test")
        print("Or run with pytest for full test suite")