"""
Tests for MCP Token Service

This module tests the MCPTokenService functionality including:
- Token generation with user data and expiration
- Token validation and authentication
- Token revocation by user
- Expired token cleanup
- Token statistics and user token retrieval
- Error handling and edge cases
"""

import pytest
import asyncio
from datetime import datetime, timedelta, UTC
from unittest.mock import patch, Mock
from uuid import uuid4

from fastmcp.auth.services.mcp_token_service import (
    MCPTokenService, 
    MCPToken, 
    mcp_token_service
)


class TestMCPToken:
    """Test suite for MCPToken data structure"""
    
    def test_mcp_token_creation(self):
        """Test MCPToken creation with all fields"""
        created_at = datetime.now(UTC)
        expires_at = created_at + timedelta(hours=24)
        metadata = {"source": "test", "permissions": ["read", "write"]}
        
        token = MCPToken(
            token="mcp_test_token_123",
            user_id="user-123",
            email="test@example.com",
            created_at=created_at,
            expires_at=expires_at,
            metadata=metadata,
            is_active=True
        )
        
        assert token.token == "mcp_test_token_123"
        assert token.user_id == "user-123"
        assert token.email == "test@example.com"
        assert token.created_at == created_at
        assert token.expires_at == expires_at
        assert token.metadata == metadata
        assert token.is_active is True
    
    def test_mcp_token_creation_defaults(self):
        """Test MCPToken creation with default values"""
        token = MCPToken(
            token="mcp_test_token_123",
            user_id="user-123"
        )
        
        assert token.token == "mcp_test_token_123"
        assert token.user_id == "user-123"
        assert token.email is None
        assert token.created_at is None
        assert token.expires_at is None
        assert token.metadata is None
        assert token.is_active is True


class TestMCPTokenService:
    """Test suite for MCPTokenService"""
    
    @pytest.fixture
    def token_service(self):
        """Create a fresh token service instance"""
        return MCPTokenService()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, token_service):
        """Test service initialization"""
        assert isinstance(token_service._tokens, dict)
        assert len(token_service._tokens) == 0
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_basic(self, token_service):
        """Test basic MCP token generation"""
        user_id = "user-123"
        email = "test@example.com"
        
        token = await token_service.generate_mcp_token_from_user_id(
            user_id=user_id,
            email=email
        )
        
        assert isinstance(token, MCPToken)
        assert token.token.startswith("mcp_")
        assert len(token.token) == 68  # "mcp_" + 64 hex chars
        assert token.user_id == user_id
        assert token.email == email
        assert token.is_active is True
        assert token.created_at is not None
        assert token.expires_at is not None
        assert token.metadata == {}
        
        # Check expiration is about 24 hours from now
        time_diff = token.expires_at - token.created_at
        assert abs(time_diff.total_seconds() - 24 * 3600) < 60  # Within 1 minute
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_with_custom_expiration(self, token_service):
        """Test MCP token generation with custom expiration"""
        user_id = "user-123"
        expires_in_hours = 48
        
        token = await token_service.generate_mcp_token_from_user_id(
            user_id=user_id,
            expires_in_hours=expires_in_hours
        )
        
        # Check expiration is about 48 hours from now
        time_diff = token.expires_at - token.created_at
        assert abs(time_diff.total_seconds() - 48 * 3600) < 60  # Within 1 minute
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_with_metadata(self, token_service):
        """Test MCP token generation with metadata"""
        user_id = "user-123"
        metadata = {
            "source": "api",
            "permissions": ["read", "write"],
            "client_info": {"app": "test_app", "version": "1.0"}
        }
        
        token = await token_service.generate_mcp_token_from_user_id(
            user_id=user_id,
            metadata=metadata
        )
        
        assert token.metadata == metadata
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_unique_tokens(self, token_service):
        """Test that generated tokens are unique"""
        user_id = "user-123"
        
        token1 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        token2 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        assert token1.token != token2.token
        assert len(token_service._tokens) == 2
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_success(self, token_service):
        """Test successful token validation"""
        user_id = "user-123"
        email = "test@example.com"
        
        # Generate token
        generated_token = await token_service.generate_mcp_token_from_user_id(
            user_id=user_id,
            email=email
        )
        
        # Validate token
        validated_token = await token_service.validate_mcp_token(generated_token.token)
        
        assert validated_token is not None
        assert validated_token.token == generated_token.token
        assert validated_token.user_id == user_id
        assert validated_token.email == email
        assert validated_token.is_active is True
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_invalid_format(self, token_service):
        """Test token validation with invalid format"""
        # Test empty token
        result = await token_service.validate_mcp_token("")
        assert result is None
        
        # Test None token
        result = await token_service.validate_mcp_token(None)
        assert result is None
        
        # Test token without mcp_ prefix
        result = await token_service.validate_mcp_token("invalid_token_123")
        assert result is None
        
        # Test random string with mcp_ prefix
        result = await token_service.validate_mcp_token("mcp_invalid_token")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_not_found(self, token_service):
        """Test token validation with non-existent token"""
        fake_token = "mcp_" + "a" * 64  # Valid format but doesn't exist
        
        result = await token_service.validate_mcp_token(fake_token)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_inactive(self, token_service):
        """Test token validation with inactive token"""
        user_id = "user-123"
        
        # Generate token
        token = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        # Mark token as inactive
        token_obj = token_service._tokens[token.token]
        token_obj.is_active = False
        
        # Validate token
        result = await token_service.validate_mcp_token(token.token)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_expired(self, token_service):
        """Test token validation with expired token"""
        user_id = "user-123"
        
        # Generate token with very short expiration
        token = await token_service.generate_mcp_token_from_user_id(
            user_id=user_id,
            expires_in_hours=0  # Expires immediately
        )
        
        # Set expiration to past
        token_obj = token_service._tokens[token.token]
        token_obj.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        
        # Validate token
        result = await token_service.validate_mcp_token(token.token)
        assert result is None
        
        # Token should be removed from storage
        assert token.token not in token_service._tokens
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_success(self, token_service):
        """Test successful token revocation for user"""
        user_id = "user-123"
        
        # Generate multiple tokens for user
        token1 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        token2 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        # Generate token for different user
        other_token = await token_service.generate_mcp_token_from_user_id(user_id="user-456")
        
        assert len(token_service._tokens) == 3
        
        # Revoke tokens for user-123
        result = await token_service.revoke_user_tokens(user_id)
        
        assert result is True
        assert len(token_service._tokens) == 1  # Only other user's token remains
        assert other_token.token in token_service._tokens
        assert token1.token not in token_service._tokens
        assert token2.token not in token_service._tokens
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_no_tokens(self, token_service):
        """Test token revocation when user has no tokens"""
        user_id = "user-123"
        
        # Generate token for different user
        await token_service.generate_mcp_token_from_user_id(user_id="user-456")
        
        # Try to revoke tokens for user with no tokens
        result = await token_service.revoke_user_tokens(user_id)
        
        assert result is False
        assert len(token_service._tokens) == 1  # Other user's token remains
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_already_inactive(self, token_service):
        """Test token revocation with already inactive tokens"""
        user_id = "user-123"
        
        # Generate token
        token = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        # Mark token as inactive
        token_obj = token_service._tokens[token.token]
        token_obj.is_active = False
        
        # Try to revoke tokens
        result = await token_service.revoke_user_tokens(user_id)
        
        assert result is False  # No active tokens to revoke
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_success(self, token_service):
        """Test successful cleanup of expired tokens"""
        user_id = "user-123"
        
        # Generate tokens with different expiration times
        token1 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        token2 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        token3 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        # Expire two tokens
        token_obj1 = token_service._tokens[token1.token]
        token_obj2 = token_service._tokens[token2.token]
        past_time = datetime.now(UTC) - timedelta(minutes=1)
        token_obj1.expires_at = past_time
        token_obj2.expires_at = past_time
        
        assert len(token_service._tokens) == 3
        
        # Cleanup expired tokens
        cleaned_count = await token_service.cleanup_expired_tokens()
        
        assert cleaned_count == 2
        assert len(token_service._tokens) == 1
        assert token3.token in token_service._tokens
        assert token1.token not in token_service._tokens
        assert token2.token not in token_service._tokens
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_no_expired(self, token_service):
        """Test cleanup when no tokens are expired"""
        user_id = "user-123"
        
        # Generate tokens that are not expired
        await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        assert len(token_service._tokens) == 2
        
        # Cleanup expired tokens
        cleaned_count = await token_service.cleanup_expired_tokens()
        
        assert cleaned_count == 0
        assert len(token_service._tokens) == 2  # No tokens removed
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_no_expiration_time(self, token_service):
        """Test cleanup with tokens that have no expiration time"""
        user_id = "user-123"
        
        # Generate token
        token = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        # Remove expiration time
        token_obj = token_service._tokens[token.token]
        token_obj.expires_at = None
        
        # Cleanup expired tokens
        cleaned_count = await token_service.cleanup_expired_tokens()
        
        assert cleaned_count == 0
        assert len(token_service._tokens) == 1  # Token not removed
    
    def test_get_token_stats_success(self, token_service):
        """Test token statistics retrieval"""
        stats = token_service.get_token_stats()
        
        assert isinstance(stats, dict)
        assert stats["total_tokens"] == 0
        assert stats["active_tokens"] == 0
        assert stats["expired_tokens"] == 0
        assert stats["service_status"] == "running"
        assert stats["storage_type"] == "in-memory"
    
    @pytest.mark.asyncio
    async def test_get_token_stats_with_tokens(self, token_service):
        """Test token statistics with various token states"""
        user_id = "user-123"
        
        # Generate active tokens
        token1 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        token2 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        # Generate expired token
        token3 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        token_obj3 = token_service._tokens[token3.token]
        token_obj3.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        
        # Generate inactive token
        token4 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        token_obj4 = token_service._tokens[token4.token]
        token_obj4.is_active = False
        
        stats = token_service.get_token_stats()
        
        assert stats["total_tokens"] == 4
        assert stats["active_tokens"] == 2
        assert stats["expired_tokens"] == 2
        assert stats["service_status"] == "running"
        assert stats["storage_type"] == "in-memory"
    
    @pytest.mark.asyncio
    async def test_get_user_tokens_success(self, token_service):
        """Test retrieving tokens for a specific user"""
        user_id = "user-123"
        other_user_id = "user-456"
        
        # Generate tokens for target user
        token1 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        token2 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        # Generate token for other user
        await token_service.generate_mcp_token_from_user_id(user_id=other_user_id)
        
        # Get tokens for target user
        user_tokens = await token_service.get_user_tokens(user_id)
        
        assert len(user_tokens) == 2
        user_token_ids = [t.token for t in user_tokens]
        assert token1.token in user_token_ids
        assert token2.token in user_token_ids
        assert all(t.user_id == user_id for t in user_tokens)
    
    @pytest.mark.asyncio
    async def test_get_user_tokens_no_tokens(self, token_service):
        """Test retrieving tokens for user with no tokens"""
        user_id = "user-123"
        
        # Generate token for different user
        await token_service.generate_mcp_token_from_user_id(user_id="user-456")
        
        # Get tokens for user with no tokens
        user_tokens = await token_service.get_user_tokens(user_id)
        
        assert len(user_tokens) == 0
    
    @pytest.mark.asyncio
    async def test_get_user_tokens_with_expired(self, token_service):
        """Test retrieving user tokens including expired ones"""
        user_id = "user-123"
        
        # Generate active token
        token1 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        # Generate expired token
        token2 = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        token_obj2 = token_service._tokens[token2.token]
        token_obj2.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        
        # Get tokens for user
        user_tokens = await token_service.get_user_tokens(user_id)
        
        assert len(user_tokens) == 2
        
        # Check that expired token is marked as inactive
        expired_token = next(t for t in user_tokens if t.token == token2.token)
        active_token = next(t for t in user_tokens if t.token == token1.token)
        
        assert expired_token.is_active is False
        assert active_token.is_active is True


class TestGlobalTokenService:
    """Test suite for global token service instance"""
    
    def test_global_service_instance(self):
        """Test global service instance is accessible"""
        assert mcp_token_service is not None
        assert isinstance(mcp_token_service, MCPTokenService)
    
    @pytest.mark.asyncio
    async def test_global_service_functionality(self):
        """Test global service instance functionality"""
        user_id = "test-user-global"
        
        # Clear any existing tokens from global instance
        mcp_token_service._tokens.clear()
        
        # Generate token using global service
        token = await mcp_token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        assert token is not None
        assert token.user_id == user_id
        
        # Validate token using global service
        validated = await mcp_token_service.validate_mcp_token(token.token)
        assert validated is not None
        assert validated.token == token.token
        
        # Clean up
        await mcp_token_service.revoke_user_tokens(user_id)
    
    def test_global_service_isolation(self):
        """Test global service isolation from test instances"""
        # Create local service
        local_service = MCPTokenService()
        
        # Services should have separate token storage
        assert local_service._tokens is not mcp_token_service._tokens
        assert id(local_service._tokens) != id(mcp_token_service._tokens)


class TestMCPTokenServiceErrorHandling:
    """Test suite for error handling scenarios"""
    
    @pytest.fixture
    def token_service(self):
        """Create a fresh token service instance"""
        return MCPTokenService()
    
    @pytest.mark.asyncio
    async def test_concurrent_token_generation(self, token_service):
        """Test concurrent token generation for same user"""
        user_id = "user-123"
        
        # Generate multiple tokens concurrently
        tasks = [
            token_service.generate_mcp_token_from_user_id(user_id=user_id)
            for _ in range(5)
        ]
        
        tokens = await asyncio.gather(*tasks)
        
        assert len(tokens) == 5
        assert len(set(t.token for t in tokens)) == 5  # All unique tokens
        assert all(t.user_id == user_id for t in tokens)
        assert len(token_service._tokens) == 5
    
    @pytest.mark.asyncio
    async def test_concurrent_token_validation(self, token_service):
        """Test concurrent token validation"""
        user_id = "user-123"
        
        # Generate a token
        token = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
        
        # Validate token concurrently
        tasks = [
            token_service.validate_mcp_token(token.token)
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(r is not None for r in results)
        assert all(r.token == token.token for r in results)
    
    @pytest.mark.asyncio 
    async def test_edge_case_user_ids(self, token_service):
        """Test token generation with edge case user IDs"""
        edge_case_ids = [
            "",  # Empty string
            "   ",  # Whitespace only
            "user-with-very-long-id-" + "x" * 100,  # Very long ID
            "用户123",  # Unicode characters
            "user@domain.com",  # Email-like ID
            "user/with/slashes",  # Special characters
        ]
        
        for user_id in edge_case_ids:
            token = await token_service.generate_mcp_token_from_user_id(user_id=user_id)
            assert token.user_id == user_id
            
            # Validate token works
            validated = await token_service.validate_mcp_token(token.token)
            assert validated is not None
            assert validated.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_large_metadata_handling(self, token_service):
        """Test token generation with large metadata"""
        user_id = "user-123"
        large_metadata = {
            "large_field": "x" * 10000,  # 10KB string
            "nested_data": {
                "level1": {
                    "level2": {
                        "level3": ["item"] * 1000  # Large nested structure
                    }
                }
            },
            "array_data": list(range(1000))  # Large array
        }
        
        token = await token_service.generate_mcp_token_from_user_id(
            user_id=user_id,
            metadata=large_metadata
        )
        
        assert token.metadata == large_metadata
        
        # Validate token still works
        validated = await token_service.validate_mcp_token(token.token)
        assert validated is not None
        assert validated.metadata == large_metadata
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_on_large_operations(self, token_service):
        """Test memory behavior with large number of tokens"""
        import gc
        
        user_id = "user-123"
        
        # Generate many tokens
        tokens = []
        for i in range(100):
            token = await token_service.generate_mcp_token_from_user_id(
                user_id=f"{user_id}-{i}",
                metadata={"index": i, "data": "x" * 100}
            )
            tokens.append(token)
        
        assert len(token_service._tokens) == 100
        
        # Revoke all tokens
        for i in range(100):
            await token_service.revoke_user_tokens(f"{user_id}-{i}")
        
        assert len(token_service._tokens) == 0
        
        # Force garbage collection
        gc.collect()
        
        # Verify service still works after large operations
        new_token = await token_service.generate_mcp_token_from_user_id(user_id="new-user")
        assert new_token is not None
        assert len(token_service._tokens) == 1