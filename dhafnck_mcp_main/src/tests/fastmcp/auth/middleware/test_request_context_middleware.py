"""Test suite for request context middleware"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import uuid


class MockRequest:
    def __init__(self, headers=None, url="/test", method="GET"):
        self.headers = headers or {}
        self.url = Mock()
        self.url.path = url
        self.method = method
        self.state = Mock()

class MockResponse:
    def __init__(self, status_code=200, headers=None):
        self.status_code = status_code
        self.headers = headers or {}


@pytest.mark.unit
class TestRequestContextMiddleware:
    """Test request context middleware functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        from fastmcp.auth.middleware.request_context_middleware import RequestContextMiddleware
        self.middleware = RequestContextMiddleware(None)
    
    def test_middleware_initialization(self):
        """Test middleware initializes correctly"""
        assert self.middleware is not None
        assert hasattr(self.middleware, 'app')
    
    @pytest.mark.asyncio
    async def test_assigns_request_id_to_every_request(self):
        """Test middleware assigns unique request ID to every request"""
        request = MockRequest()
        call_next = AsyncMock(return_value=MockResponse())
        
        await self.middleware.__call__(request, call_next)
        
        # Check that request ID was assigned
        assert hasattr(request.state, 'request_id')
        assert request.state.request_id is not None
        assert isinstance(request.state.request_id, str)
        
        # Request ID should be a valid UUID
        try:
            uuid.UUID(request.state.request_id)
        except ValueError:
            pytest.fail("Request ID is not a valid UUID")
    
    @pytest.mark.asyncio
    async def test_preserves_existing_request_state(self):
        """Test middleware preserves existing request state"""
        request = MockRequest()
        request.state.existing_data = "important_data"
        request.state.user = {"user_id": "123"}
        call_next = AsyncMock(return_value=MockResponse())
        
        await self.middleware.__call__(request, call_next)
        
        # Verify existing state is preserved
        assert request.state.existing_data == "important_data"
        assert request.state.user == {"user_id": "123"}
        # And new request ID is added
        assert hasattr(request.state, 'request_id')
    
    @pytest.mark.asyncio
    async def test_middleware_call_chain_preservation(self):
        """Test middleware properly calls next middleware in chain"""
        request = MockRequest()
        call_next = AsyncMock(return_value=MockResponse(status_code=201))
        
        response = await self.middleware.__call__(request, call_next)
        
        # Ensure call_next was called with the request
        call_next.assert_called_once_with(request)
        # Ensure response is returned as-is
        assert response.status_code == 201