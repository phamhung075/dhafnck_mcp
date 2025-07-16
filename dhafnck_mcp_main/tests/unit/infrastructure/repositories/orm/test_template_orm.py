"""
Unit tests for ORM Template Repository
Tests CRUD operations, data mapping, and ORM-specific functionality
"""

import pytest
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import patch, Mock, MagicMock

from fastmcp.task_management.infrastructure.repositories.orm.template_repository import ORMTemplateRepository
from fastmcp.task_management.infrastructure.database.models import Template as ORMTemplate
from fastmcp.task_management.domain.entities.template import Template, TemplateUsage
from fastmcp.task_management.domain.value_objects.template_id import TemplateId
from fastmcp.task_management.domain.enums.template_enums import (
    TemplateType, TemplateCategory, TemplateStatus, TemplatePriority
)

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session"""
    session = Mock()
    return session


@pytest.fixture
def sample_template():
    """Sample template for testing"""
    return Template(
        id=TemplateId('test-template-123'),
        name='Test ORM Template',
        description='A test template for ORM unit testing',
        content='# {{title}}\n\n{{description}}\n\n- [ ] {{task_item}}',
        template_type=TemplateType.TASK,
        category=TemplateCategory.DEVELOPMENT,
        status=TemplateStatus.ACTIVE,
        priority=TemplatePriority.HIGH,
        compatible_agents=['coding_agent', 'test_agent'],
        file_patterns=['*.py', '*.js'],
        variables=['title', 'description', 'task_item'],
        metadata={'test': True, 'version': '2.0', 'author': 'test'},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        version=1,
        is_active=True
    )


@pytest.fixture
def sample_orm_template():
    """Sample ORM template for testing"""
    content_data = {
        'description': 'A test ORM template',
        'content': '# {{title}}\n\nORM Test Content',
        'status': 'active',
        'priority': 'medium',
        'compatible_agents': ['test_agent'],
        'file_patterns': ['*.py'],
        'variables': ['title'],
        'metadata': {'orm': True},
        'version': 1,
        'is_active': True
    }
    
    orm_template = ORMTemplate(
        id='orm-test-456',
        name='ORM Test Template',
        type='task',
        content=content_data,
        category='testing',
        tags=['task', 'testing', 'active', 'medium', 'test_agent', 'orm'],
        usage_count=5,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        created_by='system'
    )
    return orm_template


class TestORMTemplateRepository:
    """Test suite for ORM Template Repository"""

    def setup_method(self):
        """Setup test fixtures for each test"""
        self.repository = ORMTemplateRepository()

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_save_new_template_success(self, mock_get_session, mock_session, sample_template):
        """Test saving a new template successfully"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None  # No existing template
        mock_session.commit = Mock()
        
        # Execute
        result = self.repository.save(sample_template)
        
        # Assert
        assert result is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_save_update_existing_template(self, mock_get_session, mock_session, sample_template, sample_orm_template):
        """Test updating an existing template"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = sample_orm_template
        mock_session.commit = Mock()
        
        # Execute
        result = self.repository.save(sample_template)
        
        # Assert
        assert result is True
        assert sample_orm_template.name == sample_template.name
        assert sample_orm_template.type == sample_template.template_type.value
        mock_session.commit.assert_called_once()

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_save_template_error_handling(self, mock_get_session, mock_session, sample_template):
        """Test error handling during template save"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.side_effect = Exception("Database error")
        
        # Execute
        result = self.repository.save(sample_template)
        
        # Assert
        assert result is False

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_get_by_id_success(self, mock_get_session, mock_session, sample_orm_template):
        """Test getting template by ID successfully"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = sample_orm_template
        
        template_id = TemplateId('orm-test-456')
        
        # Execute
        result = self.repository.get_by_id(template_id)
        
        # Assert
        assert result is not None
        assert result.id == template_id
        assert result.name == 'ORM Test Template'
        assert result.template_type == TemplateType.TASK
        assert result.category == TemplateCategory.TESTING

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_get_by_id_not_found(self, mock_get_session, mock_session):
        """Test getting template by ID when not found"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        template_id = TemplateId('nonexistent')
        
        # Execute
        result = self.repository.get_by_id(template_id)
        
        # Assert
        assert result is None

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_list_templates_with_filters(self, mock_get_session, mock_session, sample_orm_template):
        """Test listing templates with filters"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_orm_template]
        
        # Execute
        result = self.repository.list_templates(
            template_type=TemplateType.TASK,
            category=TemplateCategory.TESTING,
            limit=10,
            offset=0
        )
        
        # Assert
        assert len(result) == 1
        assert result[0].name == 'ORM Test Template'
        mock_query.filter.assert_called()
        mock_query.order_by.assert_called()

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_delete_template_success(self, mock_get_session, mock_session, sample_orm_template):
        """Test deleting template successfully"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = sample_orm_template
        mock_session.commit = Mock()
        
        template_id = TemplateId('orm-test-456')
        
        # Execute
        result = self.repository.delete(template_id)
        
        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(sample_orm_template)
        mock_session.commit.assert_called_once()

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_delete_template_not_found(self, mock_get_session, mock_session):
        """Test deleting template when not found"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        template_id = TemplateId('nonexistent')
        
        # Execute
        result = self.repository.delete(template_id)
        
        # Assert
        assert result is False
        mock_session.delete.assert_not_called()

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_get_templates_by_type(self, mock_get_session, mock_session, sample_orm_template):
        """Test getting templates by type"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_orm_template]
        
        # Execute
        result = self.repository.get_templates_by_type(TemplateType.TASK)
        
        # Assert
        assert len(result) == 1
        assert result[0].template_type == TemplateType.TASK

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_get_templates_by_category(self, mock_get_session, mock_session, sample_orm_template):
        """Test getting templates by category"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_orm_template]
        
        # Execute
        result = self.repository.get_templates_by_category(TemplateCategory.TESTING)
        
        # Assert
        assert len(result) == 1
        assert result[0].category == TemplateCategory.TESTING

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_search_templates_by_tags(self, mock_get_session, mock_session, sample_orm_template):
        """Test searching templates by tags"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_orm_template]
        
        # Execute
        result = self.repository.search_templates_by_tags(['testing', 'task'])
        
        # Assert
        assert len(result) == 1
        assert result[0].name == 'ORM Test Template'

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_increment_usage_count_success(self, mock_get_session, mock_session, sample_orm_template):
        """Test incrementing usage count successfully"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = sample_orm_template
        mock_session.commit = Mock()
        initial_count = sample_orm_template.usage_count
        
        template_id = TemplateId('orm-test-456')
        
        # Execute
        result = self.repository.increment_usage_count(template_id)
        
        # Assert
        assert result is True
        assert sample_orm_template.usage_count == initial_count + 1
        mock_session.commit.assert_called_once()

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_increment_usage_count_not_found(self, mock_get_session, mock_session):
        """Test incrementing usage count when template not found"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        template_id = TemplateId('nonexistent')
        
        # Execute
        result = self.repository.increment_usage_count(template_id)
        
        # Assert
        assert result is False

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_get_usage_stats_success(self, mock_get_session, mock_session, sample_orm_template):
        """Test getting usage statistics successfully"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = sample_orm_template
        
        template_id = TemplateId('orm-test-456')
        
        # Execute
        result = self.repository.get_usage_stats(template_id)
        
        # Assert
        assert result['template_id'] == str(template_id)
        assert result['total_usage'] == sample_orm_template.usage_count
        assert 'last_used' in result
        assert 'created_at' in result

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_get_usage_stats_not_found(self, mock_get_session, mock_session):
        """Test getting usage statistics when template not found"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        template_id = TemplateId('nonexistent')
        
        # Execute
        result = self.repository.get_usage_stats(template_id)
        
        # Assert
        assert result == {}

    @patch('fastmcp.task_management.infrastructure.repositories.orm.template_repository.get_session')
    def test_get_analytics_success(self, mock_get_session, mock_session):
        """Test getting template analytics successfully"""
        # Setup
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.scalar.return_value = 10  # total templates
        mock_session.query.return_value.group_by.return_value.all.return_value = [
            ('task', 5), ('checklist', 3), ('workflow', 2)
        ]
        mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Execute
        result = self.repository.get_analytics()
        
        # Assert
        assert 'total_templates' in result
        assert 'templates_by_type' in result
        assert 'templates_by_category' in result
        assert 'most_used_templates' in result
        assert 'generated_at' in result

    def test_serialize_template_content(self, sample_template):
        """Test template content serialization"""
        # Execute
        content = self.repository._serialize_template_content(sample_template)
        
        # Assert
        assert content['description'] == sample_template.description
        assert content['content'] == sample_template.content
        assert content['status'] == sample_template.status.value
        assert content['priority'] == sample_template.priority.value
        assert content['compatible_agents'] == sample_template.compatible_agents
        assert content['file_patterns'] == sample_template.file_patterns
        assert content['variables'] == sample_template.variables
        assert content['metadata'] == sample_template.metadata
        assert content['version'] == sample_template.version
        assert content['is_active'] == sample_template.is_active

    def test_extract_tags_from_template(self, sample_template):
        """Test tag extraction from template"""
        # Execute
        tags = self.repository._extract_tags_from_template(sample_template)
        
        # Assert
        assert 'task' in tags  # template type
        assert 'development' in tags  # category
        assert 'active' in tags  # status
        assert 'high' in tags  # priority
        assert 'coding_agent' in tags  # compatible agent
        assert 'test_agent' in tags  # compatible agent
        assert 'test' in tags  # metadata key
        assert 'version' in tags  # metadata key
        assert 'author' in tags  # metadata key

    def test_orm_to_domain_conversion(self, sample_orm_template):
        """Test conversion from ORM model to domain entity"""
        # Execute
        domain_template = self.repository._orm_to_domain(sample_orm_template)
        
        # Assert
        assert domain_template.id.value == sample_orm_template.id
        assert domain_template.name == sample_orm_template.name
        assert domain_template.template_type == TemplateType.TASK
        assert domain_template.category == TemplateCategory.TESTING
        assert domain_template.description == 'A test ORM template'
        assert domain_template.content == '# {{title}}\n\nORM Test Content'
        assert domain_template.status == TemplateStatus.ACTIVE
        assert domain_template.priority == TemplatePriority.MEDIUM
        assert domain_template.compatible_agents == ['test_agent']
        assert domain_template.file_patterns == ['*.py']
        assert domain_template.variables == ['title']
        assert domain_template.metadata == {'orm': True}
        assert domain_template.version == 1
        assert domain_template.is_active is True

    def test_orm_to_domain_conversion_empty_content(self):
        """Test conversion from ORM model with empty content"""
        # Setup
        orm_template = ORMTemplate(
            id='empty-test',
            name='Empty Template',
            type='task',
            content={},  # Empty content
            category='general',
            tags=[],
            usage_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by='system'
        )
        
        # Execute
        domain_template = self.repository._orm_to_domain(orm_template)
        
        # Assert
        assert domain_template.description == ''
        assert domain_template.content == ''
        assert domain_template.status == TemplateStatus.ACTIVE  # default
        assert domain_template.priority == TemplatePriority.MEDIUM  # default
        assert domain_template.compatible_agents == []
        assert domain_template.file_patterns == []
        assert domain_template.variables == []
        assert domain_template.metadata == {}
        assert domain_template.version == 1
        assert domain_template.is_active is True