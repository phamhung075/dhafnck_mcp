"""
Unit tests for SQLite Template Repository
Tests CRUD operations, data serialization, and SQLite-specific functionality
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import patch, Mock

from fastmcp.task_management.infrastructure.repositories.sqlite.template_repository import SQLiteTemplateRepository
from fastmcp.task_management.domain.entities.template import Template, TemplateUsage
from fastmcp.task_management.domain.value_objects.template_id import TemplateId
from fastmcp.task_management.domain.enums.template_enums import (
    TemplateType, TemplateCategory, TemplateStatus, TemplatePriority
)

pytestmark = pytest.mark.unit


class TestSQLiteTemplateRepository:
    """Test suite for SQLite Template Repository"""

    def setup_method(self):
        """Setup test fixtures for each test"""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize repository
        self.repository = SQLiteTemplateRepository(db_path=self.db_path)
        
        # Sample template data
        self.sample_template = Template(
            id=TemplateId('test-template-123'),
            name='Test Template',
            description='A test template for unit testing',
            content='# {{title}}\n\n{{description}}\n\n- [ ] {{task_item}}',
            template_type=TemplateType.CUSTOM,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.MEDIUM,
            compatible_agents=['*'],
            file_patterns=['*.md', '*.txt'],
            variables=['title', 'description', 'task_item'],
            metadata={'test': True, 'version': '1.0'},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        self.sample_usage = TemplateUsage(
            template_id=TemplateId('test-template-123'),
            task_id='task-456',
            project_id='project-789',
            agent_name='test_agent',
            variables_used={'title': 'Test', 'description': 'Test desc'},
            output_path='/tmp/test.md',
            generation_time_ms=250,
            cache_hit=False,
            used_at=datetime.now(timezone.utc)
        )

    def teardown_method(self):
        """Cleanup after each test"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_repository_initialization(self):
        """Test repository initialization and schema creation"""
        # Verify repository is initialized
        assert self.repository is not None
        assert self.repository._db_path == self.db_path
        
        # Verify tables exist
        with self.repository._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'templates' in tables
            assert 'template_usage' in tables

    def test_schema_creation(self):
        """Test database schema creation"""
        with self.repository._get_connection() as conn:
            # Check templates table structure
            cursor = conn.execute("PRAGMA table_info(templates)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'TEXT',
                'name': 'TEXT',
                'description': 'TEXT',
                'type': 'TEXT',
                'category': 'TEXT',
                'status': 'TEXT',
                'priority': 'TEXT',
                'content': 'TEXT',
                'variables': 'TEXT',
                'metadata': 'TEXT',
                'version': 'INTEGER',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP',
                'is_active': 'INTEGER',
                'compatible_agents': 'TEXT',
                'file_patterns': 'TEXT'
            }
            
            for col_name, col_type in expected_columns.items():
                assert col_name in columns
                assert col_type in columns[col_name]

    def test_save_new_template(self):
        """Test saving a new template"""
        # Act
        saved_template = self.repository.save(self.sample_template)
        
        # Assert
        assert saved_template.id == self.sample_template.id
        assert saved_template.name == self.sample_template.name
        
        # Verify in database
        with self.repository._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM templates WHERE id = ?",
                (self.sample_template.id.value,)
            )
            row = cursor.fetchone()
            
            assert row is not None
            assert row['name'] == 'Test Template'
            assert row['type'] == 'custom'
            assert row['category'] == 'general'
            assert row['status'] == 'active'
            assert row['priority'] == 'medium'

    def test_save_existing_template_update(self):
        """Test updating an existing template"""
        # Arrange - save initial template
        self.repository.save(self.sample_template)
        
        # Modify template
        self.sample_template.name = 'Updated Template'
        self.sample_template.description = 'Updated description'
        self.sample_template.version = 2
        
        # Act
        updated_template = self.repository.save(self.sample_template)
        
        # Assert
        assert updated_template.name == 'Updated Template'
        assert updated_template.description == 'Updated description'
        assert updated_template.version == 2
        
        # Verify only one record exists
        with self.repository._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM templates WHERE id = ?",
                (self.sample_template.id.value,)
            )
            count = cursor.fetchone()[0]
            assert count == 1

    def test_get_by_id_existing(self):
        """Test retrieving an existing template by ID"""
        # Arrange
        self.repository.save(self.sample_template)
        
        # Act
        retrieved_template = self.repository.get_by_id(self.sample_template.id)
        
        # Assert
        assert retrieved_template is not None
        assert retrieved_template.id == self.sample_template.id
        assert retrieved_template.name == self.sample_template.name
        assert retrieved_template.content == self.sample_template.content
        assert retrieved_template.variables == self.sample_template.variables
        assert retrieved_template.metadata == self.sample_template.metadata
        assert retrieved_template.compatible_agents == self.sample_template.compatible_agents
        assert retrieved_template.file_patterns == self.sample_template.file_patterns

    def test_get_by_id_nonexistent(self):
        """Test retrieving a non-existent template"""
        # Act
        result = self.repository.get_by_id(TemplateId('nonexistent'))
        
        # Assert
        assert result is None

    def test_json_serialization_deserialization(self):
        """Test JSON serialization of complex fields"""
        # Arrange
        complex_template = Template(
            id=TemplateId('complex-template'),
            name='Complex Template',
            description='Template with complex data',
            content='{{content}}',
            template_type=TemplateType.CUSTOM,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.HIGH,
            compatible_agents=['agent1', 'agent2', 'agent3'],
            file_patterns=['*.py', '*.js', '*.md'],
            variables=['content', 'author', 'date'],
            metadata={
                'nested': {
                    'key': 'value',
                    'number': 42,
                    'list': [1, 2, 3]
                },
                'tags': ['test', 'complex']
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        # Act
        saved = self.repository.save(complex_template)
        retrieved = self.repository.get_by_id(complex_template.id)
        
        # Assert
        assert retrieved is not None
        assert retrieved.compatible_agents == complex_template.compatible_agents
        assert retrieved.file_patterns == complex_template.file_patterns
        assert retrieved.variables == complex_template.variables
        assert retrieved.metadata == complex_template.metadata
        assert retrieved.metadata['nested']['key'] == 'value'
        assert retrieved.metadata['nested']['number'] == 42

    def test_list_templates_empty(self):
        """Test listing templates when repository is empty"""
        # Act
        templates, count = self.repository.list_templates()
        
        # Assert
        assert templates == []
        assert count == 0

    def test_list_templates_with_data(self):
        """Test listing templates with data"""
        # Arrange
        template1 = self.sample_template
        template2 = Template(
            id=TemplateId('template-2'),
            name='Second Template',
            description='Another template',
            content='{{content}}',
            template_type=TemplateType.CODE,
            category=TemplateCategory.DEVELOPMENT,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.LOW,
            compatible_agents=['*'],
            file_patterns=[],
            variables=[],
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        self.repository.save(template1)
        self.repository.save(template2)
        
        # Act
        templates, count = self.repository.list_templates()
        
        # Assert
        assert len(templates) == 2
        assert count == 2
        assert any(t.id == template1.id for t in templates)
        assert any(t.id == template2.id for t in templates)

    def test_list_templates_with_filters(self):
        """Test listing templates with various filters"""
        # Arrange - create templates with different types and categories
        templates = [
            Template(
                id=TemplateId(f'template-{i}'),
                name=f'Template {i}',
                description=f'Description {i}',
                content='{{content}}',
                template_type=TemplateType.CODE if i % 2 == 0 else TemplateType.CUSTOM,
                category=TemplateCategory.DEVELOPMENT if i % 2 == 0 else TemplateCategory.GENERAL,
                status=TemplateStatus.ACTIVE,
                priority=TemplatePriority.MEDIUM,
                compatible_agents=['*'],
                file_patterns=[],
                variables=[],
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1,
                is_active=i % 3 != 0  # Some inactive
            )
            for i in range(5)
        ]
        
        for template in templates:
            self.repository.save(template)
        
        # Test type filter
        code_templates, code_count = self.repository.list_templates(template_type='code')
        assert len(code_templates) == 3  # templates 0, 2, 4
        assert code_count == 3
        assert all(t.template_type == TemplateType.CODE for t in code_templates)
        
        # Test category filter
        dev_templates, dev_count = self.repository.list_templates(category='development')
        assert len(dev_templates) == 3  # templates 0, 2, 4
        assert dev_count == 3
        assert all(t.category == TemplateCategory.DEVELOPMENT for t in dev_templates)
        
        # Test active filter
        active_templates, active_count = self.repository.list_templates(is_active=True)
        assert len(active_templates) == 3  # templates 1, 2, 4 (0 and 3 are inactive)
        assert active_count == 3
        assert all(t.is_active for t in active_templates)

    def test_list_templates_pagination(self):
        """Test template listing with pagination"""
        # Arrange - create multiple templates
        for i in range(10):
            template = Template(
                id=TemplateId(f'template-{i:02d}'),
                name=f'Template {i:02d}',
                description=f'Description {i}',
                content='{{content}}',
                template_type=TemplateType.CUSTOM,
                category=TemplateCategory.GENERAL,
                status=TemplateStatus.ACTIVE,
                priority=TemplatePriority.MEDIUM,
                compatible_agents=['*'],
                file_patterns=[],
                variables=[],
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1,
                is_active=True
            )
            self.repository.save(template)
        
        # Test pagination
        page1, count1 = self.repository.list_templates(limit=3, offset=0)
        page2, count2 = self.repository.list_templates(limit=3, offset=3)
        
        assert len(page1) == 3
        assert len(page2) == 3
        assert count1 == 10
        assert count2 == 10
        
        # Verify no overlap
        page1_ids = {t.id.value for t in page1}
        page2_ids = {t.id.value for t in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_agent_compatibility_filter(self):
        """Test agent compatibility filtering"""
        # Arrange
        template1 = Template(
            id=TemplateId('template-1'),
            name='Universal Template',
            description='Works with all agents',
            content='{{content}}',
            template_type=TemplateType.CUSTOM,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.MEDIUM,
            compatible_agents=['*'],
            file_patterns=[],
            variables=[],
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        template2 = Template(
            id=TemplateId('template-2'),
            name='Specific Template',
            description='Works with specific agents',
            content='{{content}}',
            template_type=TemplateType.CUSTOM,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.MEDIUM,
            compatible_agents=['coding_agent', 'test_agent'],
            file_patterns=[],
            variables=[],
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        self.repository.save(template1)
        self.repository.save(template2)
        
        # Test agent compatibility
        coding_templates, coding_count = self.repository.list_templates(
            agent_compatible='coding_agent'
        )
        
        # Should return both templates (one universal, one specific)
        assert len(coding_templates) == 2
        assert coding_count == 2
        
        # Test with non-compatible agent
        other_templates, other_count = self.repository.list_templates(
            agent_compatible='other_agent'
        )
        
        # Should return only universal template
        # Note: count reflects total before filtering, but actual list is filtered
        assert len(other_templates) == 1
        assert other_count == 2  # Total count before agent filtering
        assert other_templates[0].id == template1.id

    def test_delete_template_success(self):
        """Test successful template deletion"""
        # Arrange
        self.repository.save(self.sample_template)
        
        # Verify template exists
        retrieved = self.repository.get_by_id(self.sample_template.id)
        assert retrieved is not None
        
        # Act
        result = self.repository.delete(self.sample_template.id)
        
        # Assert
        assert result is True
        
        # Verify template is deleted
        deleted = self.repository.get_by_id(self.sample_template.id)
        assert deleted is None

    def test_delete_nonexistent_template(self):
        """Test deleting a non-existent template"""
        # Act
        result = self.repository.delete(TemplateId('nonexistent'))
        
        # Assert
        assert result is False

    def test_save_usage(self):
        """Test saving template usage record"""
        # Act
        result = self.repository.save_usage(self.sample_usage)
        
        # Assert
        assert result is True
        
        # Verify in database
        with self.repository._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM template_usage WHERE template_id = ?",
                (self.sample_usage.template_id.value,)
            )
            row = cursor.fetchone()
            
            assert row is not None
            assert row['template_id'] == self.sample_usage.template_id.value
            assert row['task_id'] == self.sample_usage.task_id
            assert row['project_id'] == self.sample_usage.project_id
            assert row['agent_name'] == self.sample_usage.agent_name
            assert row['generation_time_ms'] == self.sample_usage.generation_time_ms
            assert row['cache_hit'] == (1 if self.sample_usage.cache_hit else 0)
            
            # Check JSON serialization
            variables_used = json.loads(row['variables_used'])
            assert variables_used == self.sample_usage.variables_used

    def test_get_usage_stats(self):
        """Test getting usage statistics for a template"""
        # Arrange - save multiple usage records
        usages = [
            TemplateUsage(
                template_id=TemplateId('test-template-123'),
                task_id=f'task-{i}',
                project_id='project-789',
                agent_name='test_agent',
                variables_used={'var': f'value-{i}'},
                output_path=f'/tmp/test-{i}.md',
                generation_time_ms=100 + i * 50,
                cache_hit=i % 2 == 0,
                used_at=datetime.now(timezone.utc)
            )
            for i in range(5)
        ]
        
        for usage in usages:
            self.repository.save_usage(usage)
        
        # Act
        stats = self.repository.get_usage_stats(TemplateId('test-template-123'))
        
        # Assert
        assert stats['usage_count'] == 5
        assert stats['success_rate'] == 100.0
        assert stats['avg_generation_time'] == 200.0  # (100+150+200+250+300)/5
        assert stats['cache_hit_rate'] == 60.0  # 3 out of 5 cache hits

    def test_get_usage_stats_no_usage(self):
        """Test getting usage statistics for template with no usage"""
        # Act
        stats = self.repository.get_usage_stats(TemplateId('unused-template'))
        
        # Assert
        assert stats['usage_count'] == 0
        assert stats['success_rate'] == 100.0
        assert stats['avg_generation_time'] == 0.0
        assert stats['cache_hit_rate'] == 0.0

    def test_get_analytics_specific_template(self):
        """Test getting analytics for a specific template"""
        # Arrange
        usage = TemplateUsage(
            template_id=TemplateId('analytics-template'),
            task_id='task-123',
            project_id='project-456',
            agent_name='test_agent',
            variables_used={'test': 'value'},
            output_path='/tmp/test.md',
            generation_time_ms=150,
            cache_hit=True,
            used_at=datetime.now(timezone.utc)
        )
        self.repository.save_usage(usage)
        
        # Act
        analytics = self.repository.get_analytics(template_id='analytics-template')
        
        # Assert
        assert analytics['usage_count'] == 1
        assert analytics['avg_generation_time'] == 150.0
        assert analytics['cache_hit_rate'] == 100.0

    def test_get_analytics_overall(self):
        """Test getting overall analytics"""
        # Arrange - create templates and usage
        template1 = self.sample_template
        template2 = Template(
            id=TemplateId('template-2'),
            name='Second Template',
            description='Another template',
            content='{{content}}',
            template_type=TemplateType.CODE,
            category=TemplateCategory.DEVELOPMENT,
            status=TemplateStatus.INACTIVE,
            priority=TemplatePriority.LOW,
            compatible_agents=['*'],
            file_patterns=[],
            variables=[],
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=False
        )
        
        self.repository.save(template1)
        self.repository.save(template2)
        
        # Add usage records
        for i in range(3):
            usage = TemplateUsage(
                template_id=template1.id,
                task_id=f'task-{i}',
                project_id='project-789',
                agent_name='test_agent',
                variables_used={'var': f'value-{i}'},
                output_path=f'/tmp/test-{i}.md',
                generation_time_ms=100,
                cache_hit=False,
                used_at=datetime.now(timezone.utc)
            )
            self.repository.save_usage(usage)
        
        # Act
        analytics = self.repository.get_analytics()
        
        # Assert
        assert analytics['total_templates'] == 2
        assert analytics['active_templates'] == 1
        assert analytics['total_usage'] == 3
        assert len(analytics['most_used_templates']) == 1
        assert analytics['most_used_templates'][0]['template_id'] == template1.id.value
        assert analytics['most_used_templates'][0]['usage_count'] == 3

    def test_delete_template_with_usage(self):
        """Test deleting template that has usage records"""
        # Arrange
        self.repository.save(self.sample_template)
        self.repository.save_usage(self.sample_usage)
        
        # Verify usage exists
        with self.repository._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM template_usage WHERE template_id = ?",
                (self.sample_template.id.value,)
            )
            usage_count = cursor.fetchone()[0]
            assert usage_count == 1
        
        # Act
        result = self.repository.delete(self.sample_template.id)
        
        # Assert
        assert result is True
        
        # Verify template is deleted
        deleted_template = self.repository.get_by_id(self.sample_template.id)
        assert deleted_template is None
        
        # Verify usage records are also deleted
        with self.repository._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM template_usage WHERE template_id = ?",
                (self.sample_template.id.value,)
            )
            usage_count = cursor.fetchone()[0]
            assert usage_count == 0

    def test_database_error_handling(self):
        """Test error handling for database operations"""
        # Close and remove database file to cause errors
        os.unlink(self.db_path)
        
        with pytest.raises(Exception):
            self.repository.save(self.sample_template)

    def test_concurrent_access(self):
        """Test concurrent access to the repository"""
        # This test simulates concurrent access
        template1 = self.sample_template
        template2 = Template(
            id=TemplateId('template-2'),
            name='Concurrent Template',
            description='Test concurrent access',
            content='{{content}}',
            template_type=TemplateType.CUSTOM,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.MEDIUM,
            compatible_agents=['*'],
            file_patterns=[],
            variables=[],
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        # Save templates concurrently (simulated)
        saved1 = self.repository.save(template1)
        saved2 = self.repository.save(template2)
        
        # Verify both are saved
        assert saved1.id == template1.id
        assert saved2.id == template2.id
        
        # Verify both can be retrieved
        retrieved1 = self.repository.get_by_id(template1.id)
        retrieved2 = self.repository.get_by_id(template2.id)
        
        assert retrieved1 is not None
        assert retrieved2 is not None
        assert retrieved1.id != retrieved2.id

    @pytest.mark.parametrize("template_type", [
        TemplateType.CUSTOM,
        TemplateType.CODE,
        TemplateType.DOCUMENTATION,
        TemplateType.CONFIGURATION
    ])
    def test_different_template_types(self, template_type):
        """Test operations with different template types"""
        template = Template(
            id=TemplateId(f'template-{template_type.value}'),
            name=f'{template_type.value.title()} Template',
            description=f'A {template_type.value} template',
            content='{{content}}',
            template_type=template_type,
            category=TemplateCategory.GENERAL,
            status=TemplateStatus.ACTIVE,
            priority=TemplatePriority.MEDIUM,
            compatible_agents=['*'],
            file_patterns=[],
            variables=[],
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            version=1,
            is_active=True
        )
        
        # Save and retrieve
        saved = self.repository.save(template)
        retrieved = self.repository.get_by_id(template.id)
        
        assert saved.template_type == template_type
        assert retrieved.template_type == template_type

    def test_template_versioning(self):
        """Test template versioning functionality"""
        # Create initial template
        template = self.sample_template
        template.version = 1
        
        # Save initial version
        self.repository.save(template)
        
        # Update template with new version
        template.content = 'Updated content {{title}}'
        template.version = 2
        template.updated_at = datetime.now(timezone.utc)
        
        # Save updated version
        updated = self.repository.save(template)
        
        # Verify version is preserved
        assert updated.version == 2
        
        # Verify in database
        retrieved = self.repository.get_by_id(template.id)
        assert retrieved.version == 2
        assert 'Updated content' in retrieved.content