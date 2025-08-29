"""Test suite for user repository infrastructure adapter"""

import pytest
from unittest.mock import Mock, patch
from fastmcp.auth.infrastructure.repositories.user_repository import UserRepository
from fastmcp.auth.domain.entities.user import User
from fastmcp.auth.domain.value_objects.email import Email
from fastmcp.auth.domain.value_objects.user_id import UserId
import uuid
from datetime import datetime


@pytest.mark.unit
class TestUserRepository:
    """Test user repository infrastructure adapter"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.repository = UserRepository(self.mock_db_session)
    
    def test_repository_initialization(self):
        """Test repository initializes correctly"""
        assert self.repository is not None
        assert self.repository.db_session == self.mock_db_session
    
    def test_save_new_user(self):
        """Test saving a new user"""
        user = User(
            id=UserId(str(uuid.uuid4())),
            email=Email("test@example.com"),
            hashed_password="hashed_password_123",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Mock database model
        mock_db_user = Mock()
        mock_db_user.id = user.id.value
        mock_db_user.email = user.email.value
        
        with patch('fastmcp.auth.infrastructure.database.models.User') as mock_user_model:
            mock_user_model.return_value = mock_db_user
            self.mock_db_session.add.return_value = None
            self.mock_db_session.commit.return_value = None
            self.mock_db_session.refresh.return_value = None
            
            result = self.repository.save(user)
            
        assert result is not None
        assert result.id == user.id
        assert result.email == user.email
        self.mock_db_session.add.assert_called_once()
        self.mock_db_session.commit.assert_called_once()
    
    def test_get_user_by_id_exists(self):
        """Test getting user by ID when user exists"""
        user_id = UserId(str(uuid.uuid4()))
        
        # Mock database user
        mock_db_user = Mock()
        mock_db_user.id = user_id.value
        mock_db_user.email = "test@example.com"
        mock_db_user.hashed_password = "hashed_password"
        mock_db_user.is_active = True
        mock_db_user.created_at = datetime.utcnow()
        
        self.mock_db_session.query.return_value.filter.return_value.first.return_value = mock_db_user
        
        result = self.repository.get_by_id(user_id)
        
        assert result is not None
        assert result.id == user_id
        assert result.email.value == "test@example.com"
        assert result.is_active is True
    
    def test_get_user_by_id_not_exists(self):
        """Test getting user by ID when user doesn't exist"""
        user_id = UserId(str(uuid.uuid4()))
        
        self.mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.repository.get_by_id(user_id)
        
        assert result is None
    
    def test_get_user_by_email_exists(self):
        """Test getting user by email when user exists"""
        email = Email("test@example.com")
        
        # Mock database user
        mock_db_user = Mock()
        mock_db_user.id = str(uuid.uuid4())
        mock_db_user.email = email.value
        mock_db_user.hashed_password = "hashed_password"
        mock_db_user.is_active = True
        mock_db_user.created_at = datetime.utcnow()
        
        self.mock_db_session.query.return_value.filter.return_value.first.return_value = mock_db_user
        
        result = self.repository.get_by_email(email)
        
        assert result is not None
        assert result.email == email
        assert result.is_active is True
    
    def test_get_user_by_email_not_exists(self):
        """Test getting user by email when user doesn't exist"""
        email = Email("nonexistent@example.com")
        
        self.mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.repository.get_by_email(email)
        
        assert result is None
    
    def test_update_existing_user(self):
        """Test updating an existing user"""
        user_id = UserId(str(uuid.uuid4()))
        
        # Mock existing database user
        mock_db_user = Mock()
        mock_db_user.id = user_id.value
        mock_db_user.email = "old@example.com"
        mock_db_user.is_active = True
        
        self.mock_db_session.query.return_value.filter.return_value.first.return_value = mock_db_user
        
        # Update user data
        updated_user = User(
            id=user_id,
            email=Email("new@example.com"),
            hashed_password="new_hashed_password",
            is_active=False,
            created_at=datetime.utcnow()
        )
        
        result = self.repository.save(updated_user)
        
        assert result is not None
        assert mock_db_user.email == "new@example.com"
        assert mock_db_user.is_active is False
        self.mock_db_session.commit.assert_called_once()
    
    def test_delete_user(self):
        """Test deleting a user"""
        user_id = UserId(str(uuid.uuid4()))
        
        # Mock existing database user
        mock_db_user = Mock()
        mock_db_user.id = user_id.value
        
        self.mock_db_session.query.return_value.filter.return_value.first.return_value = mock_db_user
        
        result = self.repository.delete(user_id)
        
        assert result is True
        self.mock_db_session.delete.assert_called_once_with(mock_db_user)
        self.mock_db_session.commit.assert_called_once()
    
    def test_delete_nonexistent_user(self):
        """Test deleting a non-existent user"""
        user_id = UserId(str(uuid.uuid4()))
        
        self.mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.repository.delete(user_id)
        
        assert result is False
        self.mock_db_session.delete.assert_not_called()
        self.mock_db_session.commit.assert_not_called()
    
    def test_list_users_with_pagination(self):
        """Test listing users with pagination"""
        # Mock database users
        mock_users = []
        for i in range(3):
            mock_user = Mock()
            mock_user.id = str(uuid.uuid4())
            mock_user.email = f"user{i}@example.com"
            mock_user.is_active = True
            mock_user.created_at = datetime.utcnow()
            mock_users.append(mock_user)
        
        self.mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_users
        
        result = self.repository.list_users(offset=0, limit=10)
        
        assert len(result) == 3
        assert all(isinstance(user, User) for user in result)
        self.mock_db_session.query.return_value.offset.assert_called_once_with(0)
        self.mock_db_session.query.return_value.offset.return_value.limit.assert_called_once_with(10)
    
    def test_count_total_users(self):
        """Test counting total users"""
        self.mock_db_session.query.return_value.count.return_value = 42
        
        result = self.repository.count_users()
        
        assert result == 42
        self.mock_db_session.query.return_value.count.assert_called_once()
    
    def test_repository_handles_database_errors(self):
        """Test repository handles database errors gracefully"""
        user = User(
            id=UserId(str(uuid.uuid4())),
            email=Email("test@example.com"),
            hashed_password="hashed_password",
            is_active=True
        )
        
        # Mock database error
        self.mock_db_session.add.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            self.repository.save(user)
    
    def test_repository_converts_to_domain_entity(self):
        """Test repository properly converts database model to domain entity"""
        user_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Mock database user
        mock_db_user = Mock()
        mock_db_user.id = user_id
        mock_db_user.email = "test@example.com"
        mock_db_user.hashed_password = "hashed_password"
        mock_db_user.is_active = True
        mock_db_user.created_at = created_at
        mock_db_user.updated_at = created_at
        
        self.mock_db_session.query.return_value.filter.return_value.first.return_value = mock_db_user
        
        result = self.repository.get_by_id(UserId(user_id))
        
        assert isinstance(result, User)
        assert isinstance(result.id, UserId)
        assert isinstance(result.email, Email)
        assert result.id.value == user_id
        assert result.email.value == "test@example.com"
        assert result.hashed_password == "hashed_password"
        assert result.is_active is True
        assert result.created_at == created_at


@pytest.mark.integration
class TestUserRepositoryIntegration:
    """Integration tests for user repository"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.repository = UserRepository(self.mock_db_session)
    
    def test_user_lifecycle_integration(self):
        """Test complete user lifecycle through repository"""
        # Create user
        user = User(
            id=UserId(str(uuid.uuid4())),
            email=Email("lifecycle@example.com"),
            hashed_password="hashed_password",
            is_active=True
        )
        
        # Mock database operations for lifecycle
        mock_db_user = Mock()
        mock_db_user.id = user.id.value
        mock_db_user.email = user.email.value
        
        with patch('fastmcp.auth.infrastructure.database.models.User') as mock_user_model:
            mock_user_model.return_value = mock_db_user
            
            # Save user
            self.mock_db_session.add.return_value = None
            self.mock_db_session.commit.return_value = None
            self.mock_db_session.refresh.return_value = None
            
            created_user = self.repository.save(user)
            assert created_user.id == user.id
            
            # Get user
            self.mock_db_session.query.return_value.filter.return_value.first.return_value = mock_db_user
            retrieved_user = self.repository.get_by_id(user.id)
            assert retrieved_user is not None
            
            # Delete user
            self.mock_db_session.query.return_value.filter.return_value.first.return_value = mock_db_user
            deleted = self.repository.delete(user.id)
            assert deleted is True
    
    def test_repository_transaction_handling(self):
        """Test repository handles transactions properly"""
        user = User(
            id=UserId(str(uuid.uuid4())),
            email=Email("transaction@example.com"),
            hashed_password="hashed_password",
            is_active=True
        )
        
        # Mock transaction rollback on error
        self.mock_db_session.add.return_value = None
        self.mock_db_session.commit.side_effect = Exception("Commit failed")
        self.mock_db_session.rollback.return_value = None
        
        with patch('fastmcp.auth.infrastructure.database.models.User'):
            with pytest.raises(Exception, match="Commit failed"):
                self.repository.save(user)
            
            # Rollback should be called on error
            self.mock_db_session.rollback.assert_called_once()